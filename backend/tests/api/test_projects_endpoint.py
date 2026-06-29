from __future__ import annotations

import uuid
from decimal import Decimal

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import create_client, create_payment, create_project


async def test_list_projects_with_aggregates(
    api_client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    client = await create_client(db_session, name="ООО Заказчик")
    project = await create_project(db_session, client=client, name="Лендинг")
    await create_payment(db_session, client=client, project=project, amount=Decimal("100"))
    await create_payment(db_session, client=client, project=project, amount=Decimal("200"))

    response = await api_client.get("/api/projects")

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    row = rows[0]
    assert row["name"] == "Лендинг"
    assert row["client"]["name"] == "ООО Заказчик"
    assert row["payment_count"] == 2
    assert Decimal(row["total_amount"]) == Decimal("300")


async def test_list_projects_filtered_by_client(
    api_client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    a = await create_client(db_session, name="A", inn="7710000001")
    b = await create_client(db_session, name="B", inn="7710000002")
    await create_project(db_session, client=a, name="A-1")
    await create_project(db_session, client=b, name="B-1")

    response = await api_client.get("/api/projects", params={"client_id": str(a.id)})

    rows = response.json()
    assert [r["name"] for r in rows] == ["A-1"]


async def test_get_project_returns_payments(
    api_client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    client = await create_client(db_session)
    project = await create_project(db_session, client=client)
    await create_payment(db_session, client=client, project=project, amount=Decimal("10"))

    response = await api_client.get(f"/api/projects/{project.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(project.id)
    assert len(body["payments"]) == 1
    assert Decimal(body["payments"][0]["amount"]) == Decimal("10")


async def test_get_project_404_when_missing(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get(f"/api/projects/{uuid.uuid4()}")
    assert response.status_code == 404
