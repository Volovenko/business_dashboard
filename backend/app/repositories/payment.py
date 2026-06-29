"""Read/write access for :class:`Payment` aggregate."""

from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import Act, Client, Payment
from app.schemas.payment import PaymentFilters


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, payment: Payment) -> None:
        self._session.add(payment)
        await self._session.flush()

    async def get(self, payment_id: uuid.UUID) -> Payment | None:
        return await self._session.get(Payment, payment_id)

    async def get_with_relations(self, payment_id: uuid.UUID) -> Payment | None:
        stmt = self._with_relations(select(Payment)).where(Payment.id == payment_id)
        return await self._session.scalar(stmt)

    async def list(self, filters: PaymentFilters) -> list[Payment]:
        stmt = self._with_relations(select(Payment))
        stmt = self._apply_filters(stmt, filters)
        stmt = stmt.order_by(Payment.payment_date.desc(), Payment.created_at.desc())
        result = await self._session.scalars(stmt)
        return list(result.unique().all())

    @staticmethod
    def _with_relations(stmt):
        return stmt.options(
            joinedload(Payment.client),
            joinedload(Payment.project),
            joinedload(Payment.act),
        )

    @staticmethod
    def _apply_filters(stmt, filters: PaymentFilters):
        if filters.client_id is not None:
            stmt = stmt.where(Payment.client_id == filters.client_id)
        if filters.project_id is not None:
            stmt = stmt.where(Payment.project_id == filters.project_id)
        if filters.date_from is not None:
            stmt = stmt.where(Payment.payment_date >= filters.date_from)
        if filters.date_to is not None:
            stmt = stmt.where(Payment.payment_date <= filters.date_to)
        if filters.service_type is not None:
            stmt = stmt.where(Payment.service_type == filters.service_type)
        if filters.act_status is not None:
            stmt = stmt.join(Act, Act.payment_id == Payment.id).where(
                Act.status == filters.act_status
            )
        if filters.search:
            pattern = f"%{filters.search}%"
            stmt = stmt.join(Client, Client.id == Payment.client_id).where(
                or_(
                    Payment.payment_purpose.ilike(pattern),
                    Client.name.ilike(pattern),
                )
            )
        return stmt
