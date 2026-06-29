from __future__ import annotations

import uuid
from decimal import Decimal

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import create_client, create_payment, create_project


async def test_list_clients_empty(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get("/api/clients")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_clients_returns_aggregates_sorted_by_name(
    api_client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    alpha = await create_client(db_session, name="Альфа", inn="7700000001")
    beta = await create_client(db_session, name="Бета", inn="7700000002")
    project = await create_project(db_session, client=alpha)
    await create_payment(db_session, client=alpha, project=project, amount=Decimal("1234.56"))

    response = await api_client.get("/api/clients")

    assert response.status_code == 200
    payload = response.json()
    assert [c["name"] for c in payload] == ["Альфа", "Бета"]
    alpha_row = payload[0]
    assert alpha_row["project_count"] == 1
    assert alpha_row["payment_count"] == 1
    assert Decimal(alpha_row["total_amount"]) == Decimal("1234.56")
    beta_row = payload[1]
    assert beta_row["project_count"] == 0
    assert beta_row["payment_count"] == 0
    assert Decimal(beta_row["total_amount"]) == Decimal("0")
    assert beta_row["id"] == str(beta.id)


async def test_get_client_returns_projects(
    api_client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    client = await create_client(db_session)
    project = await create_project(db_session, client=client, name="Сайт")

    response = await api_client.get(f"/api/clients/{client.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(client.id)
    assert [p["name"] for p in body["projects"]] == ["Сайт"]
    assert body["projects"][0]["id"] == str(project.id)


async def test_get_client_404_when_missing(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get(f"/api/clients/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json()["entity"] == "Client"
