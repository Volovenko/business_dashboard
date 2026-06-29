from __future__ import annotations

import uuid
from datetime import date

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActStatus, ProjectStatus
from tests.factories import create_act, create_client, create_payment, create_project


async def test_patch_act_marks_sent_and_stamps_timestamp(
    api_client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    client = await create_client(db_session)
    project = await create_project(db_session, client=client)
    payment = await create_payment(db_session, client=client, project=project, payment_date=date.today())
    act = await create_act(db_session, payment=payment)

    response = await api_client.patch(f"/api/acts/{act.id}", json={"is_sent": True})

    assert response.status_code == 200
    body = response.json()
    assert body["is_sent"] is True
    assert body["sent_at"] is not None
    assert body["status"] == "waiting_signature"


async def test_patch_act_signs_and_promotes_project_to_completed(
    api_client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    client = await create_client(db_session)
    project = await create_project(db_session, client=client)
    payment = await create_payment(db_session, client=client, project=project, payment_date=date.today())
    act = await create_act(
        db_session, payment=payment, is_sent=True, status=ActStatus.WAITING_SIGNATURE
    )

    response = await api_client.patch(
        f"/api/acts/{act.id}", json={"is_sent": True, "is_signed": True}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "closed"

    await db_session.refresh(project)
    assert project.status is ProjectStatus.COMPLETED


async def test_patch_act_rejects_signed_without_sent(
    api_client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    client = await create_client(db_session)
    project = await create_project(db_session, client=client)
    payment = await create_payment(db_session, client=client, project=project)
    act = await create_act(db_session, payment=payment)

    response = await api_client.patch(
        f"/api/acts/{act.id}", json={"is_sent": False, "is_signed": True}
    )

    assert response.status_code == 422


async def test_patch_act_404_when_missing(api_client: httpx.AsyncClient) -> None:
    response = await api_client.patch(
        f"/api/acts/{uuid.uuid4()}", json={"is_sent": True}
    )
    assert response.status_code == 404


async def test_patch_act_writes_manager_comment(
    api_client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    client = await create_client(db_session)
    project = await create_project(db_session, client=client)
    payment = await create_payment(db_session, client=client, project=project)
    act = await create_act(db_session, payment=payment)

    response = await api_client.patch(
        f"/api/acts/{act.id}", json={"manager_comment": "напомнить клиенту"}
    )

    assert response.status_code == 200
    assert response.json()["manager_comment"] == "напомнить клиенту"
