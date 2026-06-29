from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActStatus
from tests.factories import create_act, create_client, create_payment, create_project


async def test_list_payments_with_relations_sorted_desc(
    api_client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    client = await create_client(db_session, name="ООО Икс")
    project = await create_project(db_session, client=client, name="Проект Икс")
    older = await create_payment(
        db_session, client=client, project=project, payment_date=date(2026, 1, 1)
    )
    newer = await create_payment(
        db_session, client=client, project=project, payment_date=date(2026, 6, 1)
    )
    await create_act(db_session, payment=older, status=ActStatus.NOT_SENT)
    await create_act(db_session, payment=newer, status=ActStatus.WAITING_SIGNATURE, is_sent=True)

    response = await api_client.get("/api/payments")

    assert response.status_code == 200
    rows = response.json()
    assert [r["id"] for r in rows] == [str(newer.id), str(older.id)]
    assert rows[0]["client"]["name"] == "ООО Икс"
    assert rows[0]["project"]["name"] == "Проект Икс"
    assert rows[0]["act"]["status"] == "waiting_signature"


async def test_list_payments_filtered_by_act_status(
    api_client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    client = await create_client(db_session)
    project = await create_project(db_session, client=client)
    p1 = await create_payment(db_session, client=client, project=project)
    p2 = await create_payment(db_session, client=client, project=project)
    await create_act(db_session, payment=p1, status=ActStatus.CLOSED, is_sent=True, is_signed=True)
    await create_act(db_session, payment=p2, status=ActStatus.NOT_SENT)

    response = await api_client.get("/api/payments", params={"act_status": "closed"})

    rows = response.json()
    assert [r["id"] for r in rows] == [str(p1.id)]


async def test_list_payments_filtered_by_search_purpose(
    api_client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    client = await create_client(db_session, name="ООО Альфа")
    project = await create_project(db_session, client=client)
    match = await create_payment(
        db_session, client=client, project=project, payment_purpose="Оплата по счёту № 42"
    )
    await create_payment(
        db_session, client=client, project=project, payment_purpose="Другая оплата"
    )

    response = await api_client.get("/api/payments", params={"search": "счёту № 42"})

    rows = response.json()
    assert [r["id"] for r in rows] == [str(match.id)]


async def test_list_payments_filtered_by_search_client_name(
    api_client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    target_client = await create_client(db_session, name="ООО Уникальное", inn="7723456789")
    other_client = await create_client(db_session, name="ООО Прочее", inn="7723456780")
    p_target = await create_payment(
        db_session,
        client=target_client,
        project=await create_project(db_session, client=target_client),
    )
    await create_payment(
        db_session,
        client=other_client,
        project=await create_project(db_session, client=other_client),
    )

    response = await api_client.get("/api/payments", params={"search": "Уникальное"})

    rows = response.json()
    assert [r["id"] for r in rows] == [str(p_target.id)]


async def test_list_payments_filtered_by_date_range(
    api_client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    client = await create_client(db_session)
    project = await create_project(db_session, client=client)
    in_range = await create_payment(
        db_session, client=client, project=project, payment_date=date(2026, 3, 15)
    )
    await create_payment(
        db_session, client=client, project=project, payment_date=date(2026, 1, 1)
    )
    await create_payment(
        db_session, client=client, project=project, payment_date=date(2026, 6, 1)
    )

    response = await api_client.get(
        "/api/payments",
        params={"date_from": "2026-03-01", "date_to": "2026-04-01"},
    )

    rows = response.json()
    assert [r["id"] for r in rows] == [str(in_range.id)]


async def test_get_payment_returns_relations(
    api_client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    client = await create_client(db_session)
    project = await create_project(db_session, client=client)
    payment = await create_payment(
        db_session, client=client, project=project, amount=Decimal("999.99")
    )
    await create_act(db_session, payment=payment, status=ActStatus.NOT_SENT)

    response = await api_client.get(f"/api/payments/{payment.id}")

    body = response.json()
    assert body["id"] == str(payment.id)
    assert Decimal(body["amount"]) == Decimal("999.99")
    assert body["act"]["status"] == "not_sent"


async def test_get_payment_404_when_missing(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get(f"/api/payments/{uuid.uuid4()}")
    assert response.status_code == 404
