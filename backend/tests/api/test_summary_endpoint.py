from __future__ import annotations

from decimal import Decimal

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActStatus
from tests.factories import create_act, create_client, create_payment, create_project


async def test_summary_returns_zeros_on_empty_db(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get("/api/summary")

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "total_amount": "0",
        "total_projects": 0,
        "total_payments": 0,
        "closed_amount": "0",
        "open_amount": "0",
        "acts_not_sent": 0,
        "acts_waiting_signature": 0,
    }


async def test_summary_aggregates_by_status(
    api_client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    client = await create_client(db_session)
    project = await create_project(db_session, client=client)
    closed_payment = await create_payment(db_session, client=client, project=project, amount=Decimal("3000"))
    await create_act(db_session, payment=closed_payment, is_sent=True, is_signed=True, status=ActStatus.CLOSED)

    waiting_payment = await create_payment(db_session, client=client, project=project, amount=Decimal("1500"))
    await create_act(db_session, payment=waiting_payment, is_sent=True, status=ActStatus.WAITING_SIGNATURE)

    not_sent_payment = await create_payment(db_session, client=client, project=project, amount=Decimal("500"))
    await create_act(db_session, payment=not_sent_payment, status=ActStatus.NOT_SENT)

    response = await api_client.get("/api/summary")

    body = response.json()
    assert Decimal(body["total_amount"]) == Decimal("5000")
    assert Decimal(body["closed_amount"]) == Decimal("3000")
    assert Decimal(body["open_amount"]) == Decimal("2000")
    assert body["total_projects"] == 1
    assert body["total_payments"] == 3
    assert body["acts_not_sent"] == 1
    assert body["acts_waiting_signature"] == 1
