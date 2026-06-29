"""Read/write access for :class:`Client` aggregate."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Client, Payment, Project


@dataclass(frozen=True, slots=True)
class ClientAggregateRow:
    """Domain projection: a client plus aggregate counters computed in SQL."""

    client: Client
    project_count: int
    payment_count: int
    total_amount: Decimal


class ClientRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, client: Client) -> None:
        self._session.add(client)
        await self._session.flush()

    async def get(self, client_id: uuid.UUID) -> Client | None:
        return await self._session.get(Client, client_id)

    async def get_by_inn(self, inn: str) -> Client | None:
        stmt = select(Client).where(Client.inn == inn)
        return await self._session.scalar(stmt)

    async def get_with_projects(self, client_id: uuid.UUID) -> Client | None:
        stmt = (
            select(Client)
            .options(selectinload(Client.projects))
            .where(Client.id == client_id)
        )
        return await self._session.scalar(stmt)

    async def list_with_aggregates(self) -> list[ClientAggregateRow]:
        project_counts = (
            select(
                Project.client_id.label("client_id"),
                func.count(Project.id).label("project_count"),
            )
            .group_by(Project.client_id)
            .subquery()
        )
        payment_aggregates = (
            select(
                Payment.client_id.label("client_id"),
                func.count(Payment.id).label("payment_count"),
                func.coalesce(func.sum(Payment.amount), 0).label("total_amount"),
            )
            .group_by(Payment.client_id)
            .subquery()
        )

        stmt = (
            select(
                Client,
                func.coalesce(project_counts.c.project_count, 0).label("project_count"),
                func.coalesce(payment_aggregates.c.payment_count, 0).label("payment_count"),
                func.coalesce(payment_aggregates.c.total_amount, Decimal("0")).label("total_amount"),
            )
            .outerjoin(project_counts, project_counts.c.client_id == Client.id)
            .outerjoin(payment_aggregates, payment_aggregates.c.client_id == Client.id)
            .order_by(Client.name)
        )

        result = await self._session.execute(stmt)
        return [
            ClientAggregateRow(
                client=row.Client,
                project_count=row.project_count,
                payment_count=row.payment_count,
                total_amount=Decimal(row.total_amount),
            )
            for row in result.all()
        ]
