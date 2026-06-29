"""Smoke tests for the test infrastructure: schema present, isolation works."""

from __future__ import annotations

from sqlalchemy import select

from app.models import Client
from tests.factories import create_client


async def test_can_persist_and_query(db_session) -> None:
    client = await create_client(db_session, name="ООО Изотест")

    fetched = await db_session.scalar(select(Client).where(Client.id == client.id))

    assert fetched is not None
    assert fetched.name == "ООО Изотест"


async def test_rollback_isolates_tests_part_one(db_session) -> None:
    await create_client(db_session, inn="9999999999", name="Не должен пережить")


async def test_rollback_isolates_tests_part_two(db_session) -> None:
    leftover = await db_session.scalar(select(Client).where(Client.inn == "9999999999"))
    assert leftover is None
