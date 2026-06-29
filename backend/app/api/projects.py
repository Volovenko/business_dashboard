"""``/api/projects`` — list projects with aggregates, fetch one with payments."""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.api.deps import ProjectRepoDep
from app.core.exceptions import EntityNotFoundError
from app.schemas.client import ClientSummary
from app.schemas.detail import ProjectWithPayments
from app.schemas.project import ProjectRead, ProjectWithAggregates

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectWithAggregates])
async def list_projects(
    repo: ProjectRepoDep,
    client_id: uuid.UUID | None = None,
) -> list[ProjectWithAggregates]:
    rows = await repo.list_with_aggregates(client_id=client_id)
    return [
        ProjectWithAggregates(
            **ProjectRead.model_validate(row.project).model_dump(),
            client=ClientSummary.model_validate(row.client),
            payment_count=row.payment_count,
            total_amount=row.total_amount,
            acts_closed=row.acts_closed,
            acts_open=row.acts_open,
        )
        for row in rows
    ]


@router.get("/{project_id}", response_model=ProjectWithPayments)
async def get_project(project_id: uuid.UUID, repo: ProjectRepoDep) -> ProjectWithPayments:
    project = await repo.get_with_payments(project_id)
    if project is None:
        raise EntityNotFoundError("Project", project_id)
    return ProjectWithPayments.model_validate(project)
