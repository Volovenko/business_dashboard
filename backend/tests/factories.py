"""Lightweight async factories for ORM models.

`build_*` returns an unpersisted instance. `create_*` persists via the session
and flushes (no commit — keeps the test SAVEPOINT alive). All fields have sane
defaults; pass kwargs to override.
"""

from __future__ import annotations

import secrets
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Act, ActStatus, Client, Payment, Project, ProjectStatus


def _rand_inn() -> str:
    return str(10**9 + secrets.randbelow(9 * 10**9))


def build_client(**overrides: Any) -> Client:
    defaults: dict[str, Any] = {
        "name": f"ООО Тест-{secrets.token_hex(3)}",
        "inn": _rand_inn(),
    }
    return Client(**(defaults | overrides))


async def create_client(session: AsyncSession, **overrides: Any) -> Client:
    instance = build_client(**overrides)
    session.add(instance)
    await session.flush()
    return instance


def build_project(*, client: Client, **overrides: Any) -> Project:
    defaults: dict[str, Any] = {
        "client_id": client.id,
        "name": f"Проект {secrets.token_hex(3)}",
        "status": ProjectStatus.ACTIVE,
    }
    return Project(**(defaults | overrides))


async def create_project(session: AsyncSession, *, client: Client, **overrides: Any) -> Project:
    instance = build_project(client=client, **overrides)
    session.add(instance)
    await session.flush()
    return instance


def build_payment(
    *,
    client: Client,
    project: Project,
    **overrides: Any,
) -> Payment:
    defaults: dict[str, Any] = {
        "client_id": client.id,
        "project_id": project.id,
        "payment_date": date.today(),
        "amount": Decimal("10000.00"),
        "payment_purpose": "Оплата по счёту",
        "service_type": "разработка",
        "invoice_number": None,
        "contract_number": None,
        "doc_number": None,
    }
    return Payment(**(defaults | overrides))


async def create_payment(
    session: AsyncSession,
    *,
    client: Client,
    project: Project,
    **overrides: Any,
) -> Payment:
    instance = build_payment(client=client, project=project, **overrides)
    session.add(instance)
    await session.flush()
    return instance


def build_act(*, payment: Payment, **overrides: Any) -> Act:
    defaults: dict[str, Any] = {
        "payment_id": payment.id,
        "is_sent": False,
        "is_signed": False,
        "status": ActStatus.NOT_SENT,
    }
    return Act(**(defaults | overrides))


async def create_act(session: AsyncSession, *, payment: Payment, **overrides: Any) -> Act:
    instance = build_act(payment=payment, **overrides)
    session.add(instance)
    await session.flush()
    return instance


def days_ago(n: int) -> date:
    return date.today() - timedelta(days=n)


def now_utc() -> datetime:
    return datetime.now(UTC)
