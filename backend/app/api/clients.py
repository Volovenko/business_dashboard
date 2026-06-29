"""``/api/clients`` — list clients with aggregates, fetch one with projects."""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.api.deps import ClientRepoDep
from app.core.exceptions import EntityNotFoundError
from app.schemas.client import ClientRead, ClientWithAggregates
from app.schemas.detail import ClientWithProjects

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("", response_model=list[ClientWithAggregates])
async def list_clients(repo: ClientRepoDep) -> list[ClientWithAggregates]:
    rows = await repo.list_with_aggregates()
    return [
        ClientWithAggregates(
            **ClientRead.model_validate(row.client).model_dump(),
            project_count=row.project_count,
            payment_count=row.payment_count,
            total_amount=row.total_amount,
        )
        for row in rows
    ]


@router.get("/{client_id}", response_model=ClientWithProjects)
async def get_client(client_id: uuid.UUID, repo: ClientRepoDep) -> ClientWithProjects:
    client = await repo.get_with_projects(client_id)
    if client is None:
        raise EntityNotFoundError("Client", client_id)
    return ClientWithProjects.model_validate(client)
