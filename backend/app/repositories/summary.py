"""Aggregate counters for the dashboard summary endpoint."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Act, ActStatus, Payment, Project


@dataclass(frozen=True, slots=True)
class SummaryRow:
    """Plain numeric snapshot of the whole workspace, computed in one query."""

    total_amount: Decimal
    total_projects: int
    total_payments: int
    closed_amount: Decimal
    open_amount: Decimal
    acts_not_sent: int
    acts_waiting_signature: int


class SummaryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def snapshot(self) -> SummaryRow:
        total_projects = await self._session.scalar(select(func.count(Project.id))) or 0

        closed_amount = func.coalesce(
            func.sum(case((Act.status == ActStatus.CLOSED, Payment.amount), else_=0)),
            0,
        )
        acts_not_sent = func.coalesce(
            func.sum(case((Act.status == ActStatus.NOT_SENT, 1), else_=0)),
            0,
        )
        acts_waiting_signature = func.coalesce(
            func.sum(case((Act.status == ActStatus.WAITING_SIGNATURE, 1), else_=0)),
            0,
        )

        stmt = select(
            func.count(Payment.id).label("total_payments"),
            func.coalesce(func.sum(Payment.amount), 0).label("total_amount"),
            closed_amount.label("closed_amount"),
            acts_not_sent.label("acts_not_sent"),
            acts_waiting_signature.label("acts_waiting_signature"),
        ).outerjoin(Act, Act.payment_id == Payment.id)

        row = (await self._session.execute(stmt)).one()
        total_amount = Decimal(row.total_amount)
        closed = Decimal(row.closed_amount)
        return SummaryRow(
            total_amount=total_amount,
            total_projects=total_projects,
            total_payments=row.total_payments,
            closed_amount=closed,
            open_amount=total_amount - closed,
            acts_not_sent=row.acts_not_sent,
            acts_waiting_signature=row.acts_waiting_signature,
        )
