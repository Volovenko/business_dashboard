"""Builds the dashboard summary payload from a single SQL snapshot."""

from __future__ import annotations

from typing import Protocol

from app.repositories.summary import SummaryRow
from app.schemas.summary import SummaryRead


class _SummarySource(Protocol):
    async def snapshot(self) -> SummaryRow: ...


class SummaryService:
    """Wraps :class:`SummaryRepository` and projects its row into the API schema.

    Kept as a service (rather than letting the router call the repository directly)
    so that future cross-cutting concerns — caching, role-based filtering, currency
    conversion — have a single place to live.
    """

    def __init__(self, repository: _SummarySource) -> None:
        self._repository = repository

    async def build(self) -> SummaryRead:
        row = await self._repository.snapshot()
        return SummaryRead.model_validate(row)
