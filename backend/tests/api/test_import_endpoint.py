from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Act, Client, Payment, Project

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "bank_statement.pdf"


@pytest.fixture()
def pdf_bytes() -> bytes:
    return FIXTURE.read_bytes()


async def test_preview_returns_parsed_payments(
    api_client: httpx.AsyncClient, pdf_bytes: bytes
) -> None:
    response = await api_client.post(
        "/api/import/preview",
        files={"file": ("statement.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["payments"]) == 24
    first = body["payments"][0]
    assert {"client_inn", "client_name", "project_name", "service_type",
            "payment_date", "amount", "payment_purpose", "doc_number"} <= first.keys()


async def test_preview_rejects_empty_file(api_client: httpx.AsyncClient) -> None:
    response = await api_client.post(
        "/api/import/preview",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )

    assert response.status_code == 400


async def test_commit_persists_clients_projects_payments_and_acts(
    api_client: httpx.AsyncClient, db_session: AsyncSession, pdf_bytes: bytes
) -> None:
    preview = await api_client.post(
        "/api/import/preview",
        files={"file": ("statement.pdf", pdf_bytes, "application/pdf")},
    )
    payments = preview.json()["payments"]

    response = await api_client.post(
        "/api/import/commit", json={"payments": payments}
    )

    assert response.status_code == 200
    summary = response.json()
    assert summary["created_payments"] == 24
    assert summary["created_acts"] == 24
    assert summary["created_clients"] >= 1
    assert summary["created_projects"] >= 1

    client_count = await db_session.scalar(select(func.count(Client.id)))
    project_count = await db_session.scalar(select(func.count(Project.id)))
    payment_count = await db_session.scalar(select(func.count(Payment.id)))
    act_count = await db_session.scalar(select(func.count(Act.id)))
    assert payment_count == 24
    assert act_count == 24
    assert client_count == summary["created_clients"]
    assert project_count == summary["created_projects"]


async def test_commit_rejects_unknown_fields(api_client: httpx.AsyncClient) -> None:
    response = await api_client.post(
        "/api/import/commit",
        json={"payments": [{"unexpected_field": "x"}]},
    )

    assert response.status_code == 422
