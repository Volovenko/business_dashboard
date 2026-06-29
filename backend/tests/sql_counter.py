"""Utility for asserting query counts in repository tests.

Use it to lock in that aggregate/list endpoints never regress into N+1.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine

_SKIP_PREFIXES = ("SAVEPOINT", "RELEASE", "ROLLBACK", "BEGIN", "COMMIT")


@contextmanager
def count_queries(engine: AsyncEngine) -> Iterator[list[str]]:
    """Yields a list that accumulates every non-transactional SQL statement issued
    against *engine* while the context is open."""

    statements: list[str] = []
    sync_engine = engine.sync_engine

    def _on_execute(conn, cursor, statement, parameters, context, executemany):  # noqa: ARG001
        normalized = statement.strip().upper()
        if not normalized.startswith(_SKIP_PREFIXES):
            statements.append(statement)

    event.listen(sync_engine, "before_cursor_execute", _on_execute)
    try:
        yield statements
    finally:
        event.remove(sync_engine, "before_cursor_execute", _on_execute)
