"""Read/write access for :class:`Act`."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import Act, ActStatus, Payment


class ActRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, act: Act) -> None:
        self._session.add(act)
        await self._session.flush()

    async def get(self, act_id: uuid.UUID) -> Act | None:
        return await self._session.get(Act, act_id)

    async def get_with_payment(self, act_id: uuid.UUID) -> Act | None:
        stmt = (
            select(Act).options(joinedload(Act.payment)).where(Act.id == act_id)
        )
        return await self._session.scalar(stmt)

    async def list_statuses_for_project(self, project_id: uuid.UUID) -> list[ActStatus]:
        stmt = (
            select(Act.status)
            .join(Payment, Payment.id == Act.payment_id)
            .where(Payment.project_id == project_id)
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def update(self, act: Act, **fields: Any) -> None:
        for name, value in fields.items():
            if not hasattr(act, name):
                raise AttributeError(f"Act has no attribute {name!r}")
            setattr(act, name, value)
        await self._session.flush()
