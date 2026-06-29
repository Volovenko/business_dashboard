"""API-level test fixtures: a FastAPI app instance whose ``get_session`` is
overridden to reuse the per-test SAVEPOINT'd session from the root conftest.

That way each test sees the same data the routes operate on, and the outer
rollback in the root conftest cleans everything up.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.main import create_app


@pytest_asyncio.fixture()
async def app(db_session: AsyncSession) -> AsyncIterator[FastAPI]:
    application = create_app()

    async def _override_get_session() -> AsyncIterator[AsyncSession]:
        # Yield the same SAVEPOINT-bound session the test set up its data in.
        # We deliberately do NOT close it here — the root conftest owns its lifecycle.
        yield db_session

    application.dependency_overrides[get_session] = _override_get_session
    try:
        yield application
    finally:
        application.dependency_overrides.clear()


@pytest_asyncio.fixture()
async def api_client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
