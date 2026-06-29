"""Test fixtures for backend.

Lifecycle:
    session start  → drop/create `dashboard_test`, run alembic upgrade head.
    session engine → one AsyncEngine pointed at the test DB (NullPool).
    each test      → fresh AsyncSession on a connection wrapped in an outer
                     transaction; SAVEPOINT join mode lets services call
                     `commit()` freely without ending isolation; teardown
                     rolls back the outer transaction → clean state.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from tests.db import migrate_test_database, recreate_test_database, test_async_url


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_test_database() -> None:
    recreate_test_database()
    migrate_test_database()


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(test_async_url(), poolclass=NullPool)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture()
async def db_session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    connection = await engine.connect()
    outer_transaction = await connection.begin()
    session = AsyncSession(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    try:
        yield session
    finally:
        await session.close()
        if outer_transaction.is_active:
            await outer_transaction.rollback()
        await connection.close()
