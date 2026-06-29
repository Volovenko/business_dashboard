from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any

import pytest

from app.core.exceptions import EntityNotFoundError
from app.models import Act, ActStatus, Payment, Project, ProjectStatus
from app.schemas.act import ActUpdate
from app.services.update_act_service import UpdateActService

FIXED_NOW = datetime(2026, 6, 25, 12, 0, tzinfo=UTC)
THRESHOLD_DAYS = 30


def _make_payment(project_id: uuid.UUID, payment_date: date) -> Payment:
    payment = Payment(
        id=uuid.uuid4(),
        project_id=project_id,
        client_id=uuid.uuid4(),
        payment_date=payment_date,
        amount=0,  # type: ignore[arg-type]
        payment_purpose="",
        service_type="",
    )
    return payment


def _make_act(payment: Payment, **overrides: Any) -> Act:
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "payment_id": payment.id,
        "is_sent": False,
        "is_signed": False,
        "status": ActStatus.NOT_SENT,
    }
    act = Act(**(defaults | overrides))
    # Mimic SQLAlchemy's eager-loaded relationship without touching the session.
    act.payment = payment
    return act


@dataclass
class _FakeActRepo:
    act: Act | None
    sibling_statuses: list[ActStatus] = field(default_factory=list)
    updates: list[dict[str, Any]] = field(default_factory=list)

    async def get_with_payment(self, act_id: uuid.UUID) -> Act | None:
        if self.act is None or self.act.id != act_id:
            return None
        return self.act

    async def list_statuses_for_project(self, project_id: uuid.UUID) -> list[ActStatus]:
        return list(self.sibling_statuses)

    async def update(self, act: Act, **fields: Any) -> None:
        for name, value in fields.items():
            setattr(act, name, value)
        self.updates.append(fields)


@dataclass
class _FakeProjectRepo:
    project: Project | None
    status_updates: list[ProjectStatus] = field(default_factory=list)

    async def get(self, project_id: uuid.UUID) -> Project | None:
        if self.project is None or self.project.id != project_id:
            return None
        return self.project

    async def update_status(self, project: Project, status: ProjectStatus) -> None:
        project.status = status
        self.status_updates.append(status)


def _service(
    act_repo: _FakeActRepo,
    project_repo: _FakeProjectRepo,
    *,
    now: datetime = FIXED_NOW,
) -> UpdateActService:
    return UpdateActService(
        act_repo=act_repo,
        project_repo=project_repo,
        clock=lambda: now,
        threshold_days=THRESHOLD_DAYS,
    )


class TestUpdate:
    async def test_raises_when_act_missing(self) -> None:
        act_repo = _FakeActRepo(act=None)
        project_repo = _FakeProjectRepo(project=None)

        with pytest.raises(EntityNotFoundError):
            await _service(act_repo, project_repo).update(uuid.uuid4(), ActUpdate(is_sent=True))

    async def test_marks_act_as_sent_and_stamps_sent_at(self) -> None:
        project = Project(id=uuid.uuid4(), client_id=uuid.uuid4(), name="P", status=ProjectStatus.ACTIVE)
        payment = _make_payment(project.id, payment_date=FIXED_NOW.date())
        act = _make_act(payment)
        act_repo = _FakeActRepo(act=act, sibling_statuses=[ActStatus.WAITING_SIGNATURE])
        project_repo = _FakeProjectRepo(project=project)

        result = await _service(act_repo, project_repo).update(act.id, ActUpdate(is_sent=True))

        assert result.is_sent is True
        assert result.sent_at == FIXED_NOW
        assert result.status is ActStatus.WAITING_SIGNATURE
        assert act_repo.updates  # at least one update call

    async def test_marks_act_as_signed_and_stamps_signed_at(self) -> None:
        project = Project(id=uuid.uuid4(), client_id=uuid.uuid4(), name="P", status=ProjectStatus.ACTIVE)
        payment = _make_payment(project.id, payment_date=FIXED_NOW.date())
        act = _make_act(payment, is_sent=True, sent_at=FIXED_NOW, status=ActStatus.WAITING_SIGNATURE)
        act_repo = _FakeActRepo(act=act, sibling_statuses=[ActStatus.CLOSED])
        project_repo = _FakeProjectRepo(project=project)

        result = await _service(act_repo, project_repo).update(
            act.id, ActUpdate(is_sent=True, is_signed=True)
        )

        assert result.is_signed is True
        assert result.signed_at == FIXED_NOW
        assert result.status is ActStatus.CLOSED

    async def test_clears_sent_at_when_is_sent_set_back_to_false(self) -> None:
        project = Project(id=uuid.uuid4(), client_id=uuid.uuid4(), name="P", status=ProjectStatus.ACTIVE)
        payment = _make_payment(project.id, payment_date=FIXED_NOW.date())
        act = _make_act(payment, is_sent=True, sent_at=FIXED_NOW, status=ActStatus.WAITING_SIGNATURE)
        act_repo = _FakeActRepo(act=act)
        project_repo = _FakeProjectRepo(project=project)

        result = await _service(act_repo, project_repo).update(act.id, ActUpdate(is_sent=False))

        assert result.is_sent is False
        assert result.sent_at is None
        assert result.status is ActStatus.NOT_SENT

    async def test_does_not_overwrite_existing_sent_at_when_flag_unchanged(self) -> None:
        earlier = datetime(2026, 6, 1, 9, 0, tzinfo=UTC)
        project = Project(id=uuid.uuid4(), client_id=uuid.uuid4(), name="P", status=ProjectStatus.ACTIVE)
        payment = _make_payment(project.id, payment_date=FIXED_NOW.date())
        act = _make_act(payment, is_sent=True, sent_at=earlier, status=ActStatus.WAITING_SIGNATURE)
        act_repo = _FakeActRepo(act=act)
        project_repo = _FakeProjectRepo(project=project)

        result = await _service(act_repo, project_repo).update(
            act.id, ActUpdate(manager_comment="напомнил клиенту")
        )

        assert result.sent_at == earlier
        assert result.manager_comment == "напомнил клиенту"

    async def test_recomputes_status_to_attention_for_stale_payment(self) -> None:
        project = Project(id=uuid.uuid4(), client_id=uuid.uuid4(), name="P", status=ProjectStatus.ACTIVE)
        old_date = FIXED_NOW.date().replace(day=1)  # June 1 — well past 30 days back? actually no
        # Pick a date 31 days ago for certainty:
        from datetime import timedelta

        old_date = FIXED_NOW.date() - timedelta(days=31)
        payment = _make_payment(project.id, payment_date=old_date)
        act = _make_act(payment)
        act_repo = _FakeActRepo(act=act, sibling_statuses=[ActStatus.ATTENTION])
        project_repo = _FakeProjectRepo(project=project)

        result = await _service(act_repo, project_repo).update(act.id, ActUpdate())

        assert result.status is ActStatus.ATTENTION
        assert project_repo.status_updates == [ProjectStatus.ATTENTION]

    async def test_promotes_project_to_completed_when_all_acts_closed(self) -> None:
        project = Project(id=uuid.uuid4(), client_id=uuid.uuid4(), name="P", status=ProjectStatus.ACTIVE)
        payment = _make_payment(project.id, payment_date=FIXED_NOW.date())
        act = _make_act(payment, is_sent=True, sent_at=FIXED_NOW, status=ActStatus.WAITING_SIGNATURE)
        # Sibling already closed; once this act is signed, all will be CLOSED.
        act_repo = _FakeActRepo(act=act, sibling_statuses=[ActStatus.CLOSED, ActStatus.CLOSED])
        project_repo = _FakeProjectRepo(project=project)

        await _service(act_repo, project_repo).update(act.id, ActUpdate(is_signed=True))

        assert project_repo.status_updates == [ProjectStatus.COMPLETED]

    async def test_on_hold_project_status_is_not_overridden(self) -> None:
        project = Project(id=uuid.uuid4(), client_id=uuid.uuid4(), name="P", status=ProjectStatus.ON_HOLD)
        payment = _make_payment(project.id, payment_date=FIXED_NOW.date())
        act = _make_act(payment, is_sent=True, sent_at=FIXED_NOW, status=ActStatus.WAITING_SIGNATURE)
        act_repo = _FakeActRepo(act=act, sibling_statuses=[ActStatus.CLOSED])
        project_repo = _FakeProjectRepo(project=project)

        await _service(act_repo, project_repo).update(act.id, ActUpdate(is_signed=True))

        # Status didn't change → no update call (still ON_HOLD).
        assert project_repo.status_updates == [] or project_repo.status_updates == [ProjectStatus.ON_HOLD]
        assert project.status is ProjectStatus.ON_HOLD

    async def test_does_not_update_project_when_status_unchanged(self) -> None:
        project = Project(id=uuid.uuid4(), client_id=uuid.uuid4(), name="P", status=ProjectStatus.ACTIVE)
        payment = _make_payment(project.id, payment_date=FIXED_NOW.date())
        act = _make_act(payment)
        # Project stays ACTIVE: mix of not_sent siblings, no attention, not all closed.
        act_repo = _FakeActRepo(act=act, sibling_statuses=[ActStatus.NOT_SENT, ActStatus.WAITING_SIGNATURE])
        project_repo = _FakeProjectRepo(project=project)

        await _service(act_repo, project_repo).update(act.id, ActUpdate(manager_comment="заметка"))

        assert project_repo.status_updates == []
