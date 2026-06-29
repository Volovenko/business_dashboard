"""Apply a partial update to an :class:`Act` and propagate status recomputation."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any, Protocol

from app.core.exceptions import EntityNotFoundError
from app.models import Act, ActStatus, Project, ProjectStatus
from app.schemas.act import ActUpdate
from app.services.act_status_service import ActStatusService
from app.services.project_status_service import ProjectStatusService


class _ActRepo(Protocol):
    async def get_with_payment(self, act_id: uuid.UUID) -> Act | None: ...
    async def list_statuses_for_project(self, project_id: uuid.UUID) -> list[ActStatus]: ...
    async def update(self, act: Act, **fields: Any) -> None: ...


class _ProjectRepo(Protocol):
    async def get(self, project_id: uuid.UUID) -> Project | None: ...
    async def update_status(self, project: Project, status: ProjectStatus) -> None: ...


class UpdateActService:
    """Orchestrates the four steps of an act update:

    1. Merge the incoming partial payload into the loaded act.
    2. Stamp ``sent_at`` / ``signed_at`` on rising edges; clear on falling edges.
    3. Recompute the act's status via :class:`ActStatusService` (pure function).
    4. Re-aggregate the parent project's status via :class:`ProjectStatusService`.

    Both repositories are passed in so the service stays unit-testable with fakes.
    """

    def __init__(
        self,
        *,
        act_repo: _ActRepo,
        project_repo: _ProjectRepo,
        clock: Callable[[], datetime],
        threshold_days: int,
    ) -> None:
        self._act_repo = act_repo
        self._project_repo = project_repo
        self._clock = clock
        self._threshold_days = threshold_days

    async def update(self, act_id: uuid.UUID, payload: ActUpdate) -> Act:
        act = await self._act_repo.get_with_payment(act_id)
        if act is None:
            raise EntityNotFoundError("Act", act_id)

        changes = self._build_changes(act, payload)
        await self._act_repo.update(act, **changes)
        await self._reaggregate_project(act)
        return act

    def _build_changes(self, act: Act, payload: ActUpdate) -> dict[str, Any]:
        now = self._clock()
        is_sent = act.is_sent if payload.is_sent is None else payload.is_sent
        is_signed = act.is_signed if payload.is_signed is None else payload.is_signed

        changes: dict[str, Any] = {"is_sent": is_sent, "is_signed": is_signed}

        if payload.is_sent is not None and payload.is_sent != act.is_sent:
            changes["sent_at"] = now if payload.is_sent else None
        if payload.is_signed is not None and payload.is_signed != act.is_signed:
            changes["signed_at"] = now if payload.is_signed else None
        if payload.manager_comment is not None:
            changes["manager_comment"] = payload.manager_comment

        changes["status"] = ActStatusService.compute(
            is_sent=is_sent,
            is_signed=is_signed,
            payment_date=act.payment.payment_date,
            today=now.date(),
            threshold_days=self._threshold_days,
        )
        return changes

    async def _reaggregate_project(self, act: Act) -> None:
        project = await self._project_repo.get(act.payment.project_id)
        if project is None:
            return

        sibling_statuses = await self._act_repo.list_statuses_for_project(project.id)
        new_status = ProjectStatusService.aggregate(
            current_status=project.status,
            act_statuses=sibling_statuses,
        )
        if new_status is not project.status:
            await self._project_repo.update_status(project, new_status)
