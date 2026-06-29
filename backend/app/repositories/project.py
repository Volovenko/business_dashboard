"""Read/write access for :class:`Project` aggregate."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Act, ActStatus, Client, Payment, Project, ProjectStatus


@dataclass(frozen=True, slots=True)
class ProjectAggregateRow:
    """A project together with its owning client and SQL-side payment/act counters."""

    project: Project
    client: Client
    payment_count: int
    total_amount: Decimal
    acts_closed: int
    acts_open: int


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, project: Project) -> None:
        self._session.add(project)
        await self._session.flush()

    async def get(self, project_id: uuid.UUID) -> Project | None:
        return await self._session.get(Project, project_id)

    async def get_by_client_and_name(self, client_id: uuid.UUID, name: str) -> Project | None:
        stmt = select(Project).where(Project.client_id == client_id, Project.name == name)
        return await self._session.scalar(stmt)

    async def get_with_payments(self, project_id: uuid.UUID) -> Project | None:
        stmt = (
            select(Project)
            .options(selectinload(Project.payments))
            .where(Project.id == project_id)
        )
        return await self._session.scalar(stmt)

    async def list_with_aggregates(
        self,
        *,
        client_id: uuid.UUID | None = None,
    ) -> list[ProjectAggregateRow]:
        payment_aggregates = (
            select(
                Payment.project_id.label("project_id"),
                func.count(Payment.id).label("payment_count"),
                func.coalesce(func.sum(Payment.amount), 0).label("total_amount"),
            )
            .group_by(Payment.project_id)
            .subquery()
        )

        act_aggregates = (
            select(
                Payment.project_id.label("project_id"),
                func.sum(
                    case((Act.status == ActStatus.CLOSED, 1), else_=0)
                ).label("acts_closed"),
                func.sum(
                    case((Act.status != ActStatus.CLOSED, 1), else_=0)
                ).label("acts_open"),
            )
            .join(Act, Act.payment_id == Payment.id)
            .group_by(Payment.project_id)
            .subquery()
        )

        stmt = (
            select(
                Project,
                Client,
                func.coalesce(payment_aggregates.c.payment_count, 0).label("payment_count"),
                func.coalesce(payment_aggregates.c.total_amount, Decimal("0")).label("total_amount"),
                func.coalesce(act_aggregates.c.acts_closed, 0).label("acts_closed"),
                func.coalesce(act_aggregates.c.acts_open, 0).label("acts_open"),
            )
            .join(Client, Client.id == Project.client_id)
            .outerjoin(payment_aggregates, payment_aggregates.c.project_id == Project.id)
            .outerjoin(act_aggregates, act_aggregates.c.project_id == Project.id)
            .order_by(Project.name)
        )
        if client_id is not None:
            stmt = stmt.where(Project.client_id == client_id)

        result = await self._session.execute(stmt)
        return [
            ProjectAggregateRow(
                project=row.Project,
                client=row.Client,
                payment_count=row.payment_count,
                total_amount=Decimal(row.total_amount),
                acts_closed=row.acts_closed,
                acts_open=row.acts_open,
            )
            for row in result.all()
        ]

    async def update_status(self, project: Project, status: ProjectStatus) -> None:
        project.status = status
        await self._session.flush()
