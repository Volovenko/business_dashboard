from __future__ import annotations

import uuid

from app.models import ActStatus
from app.repositories.act import ActRepository
from tests.factories import create_act, create_client, create_payment, create_project, now_utc


class TestGet:
    async def test_returns_act_by_id(self, db_session) -> None:
        client = await create_client(db_session)
        project = await create_project(db_session, client=client)
        payment = await create_payment(db_session, client=client, project=project)
        act = await create_act(db_session, payment=payment)

        fetched = await ActRepository(db_session).get(act.id)

        assert fetched is not None
        assert fetched.id == act.id

    async def test_returns_none_when_missing(self, db_session) -> None:
        assert await ActRepository(db_session).get(uuid.uuid4()) is None


class TestGetWithPayment:
    async def test_eager_loads_payment(self, db_session) -> None:
        client = await create_client(db_session)
        project = await create_project(db_session, client=client)
        payment = await create_payment(db_session, client=client, project=project)
        act = await create_act(db_session, payment=payment)

        fetched = await ActRepository(db_session).get_with_payment(act.id)

        assert fetched is not None
        assert fetched.payment.id == payment.id

    async def test_returns_none_when_missing(self, db_session) -> None:
        assert await ActRepository(db_session).get_with_payment(uuid.uuid4()) is None


class TestAdd:
    async def test_persists_act(self, db_session) -> None:
        from app.models import Act

        client = await create_client(db_session)
        project = await create_project(db_session, client=client)
        payment = await create_payment(db_session, client=client, project=project)
        repo = ActRepository(db_session)
        act = Act(payment_id=payment.id, status=ActStatus.NOT_SENT)

        await repo.add(act)

        fetched = await repo.get(act.id)
        assert fetched is not None


class TestListStatusesForProject:
    async def test_returns_statuses_for_project_acts_only(self, db_session) -> None:
        client = await create_client(db_session)
        project_a = await create_project(db_session, client=client)
        project_b = await create_project(db_session, client=client)
        payment_a1 = await create_payment(db_session, client=client, project=project_a)
        payment_a2 = await create_payment(db_session, client=client, project=project_a)
        payment_b1 = await create_payment(db_session, client=client, project=project_b)
        await create_act(db_session, payment=payment_a1, status=ActStatus.CLOSED)
        await create_act(db_session, payment=payment_a2, status=ActStatus.WAITING_SIGNATURE)
        await create_act(db_session, payment=payment_b1, status=ActStatus.NOT_SENT)

        statuses = await ActRepository(db_session).list_statuses_for_project(project_a.id)

        assert sorted(s.value for s in statuses) == sorted(
            [ActStatus.CLOSED.value, ActStatus.WAITING_SIGNATURE.value]
        )

    async def test_returns_empty_when_project_has_no_acts(self, db_session) -> None:
        client = await create_client(db_session)
        project = await create_project(db_session, client=client)

        statuses = await ActRepository(db_session).list_statuses_for_project(project.id)

        assert statuses == []


class TestUpdate:
    async def test_updates_fields_and_flushes(self, db_session) -> None:
        client = await create_client(db_session)
        project = await create_project(db_session, client=client)
        payment = await create_payment(db_session, client=client, project=project)
        act = await create_act(db_session, payment=payment)
        sent_at = now_utc()
        repo = ActRepository(db_session)

        await repo.update(
            act,
            is_sent=True,
            sent_at=sent_at,
            status=ActStatus.WAITING_SIGNATURE,
            manager_comment="отправил клиенту",
        )

        fetched = await repo.get(act.id)
        assert fetched is not None
        assert fetched.is_sent is True
        assert fetched.sent_at == sent_at
        assert fetched.status is ActStatus.WAITING_SIGNATURE
        assert fetched.manager_comment == "отправил клиенту"

    async def test_ignores_unknown_attributes(self, db_session) -> None:
        client = await create_client(db_session)
        project = await create_project(db_session, client=client)
        payment = await create_payment(db_session, client=client, project=project)
        act = await create_act(db_session, payment=payment)
        repo = ActRepository(db_session)

        # `nonexistent` is not on the model — must raise rather than silently swallow.
        import pytest

        with pytest.raises(AttributeError):
            await repo.update(act, nonexistent=True)
