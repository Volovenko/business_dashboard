"""Helpers for creating, migrating and tearing down the dedicated test database.

The test suite uses a separate database (`dashboard_test`) on the same Postgres
service that the application uses. This module owns the lifecycle: drop, create,
migrate. It deliberately uses synchronous psycopg2 because both Postgres's
administrative commands (DROP/CREATE DATABASE) and Alembic itself are sync.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from app.core.config import get_settings

TEST_DB_NAME = "dashboard_test"
_BACKEND_ROOT = Path(__file__).resolve().parent.parent


def _swap_database(url: str, db_name: str) -> str:
    base, _ = url.rsplit("/", 1)
    return f"{base}/{db_name}"


def test_async_url() -> str:
    return _swap_database(get_settings().database_url, TEST_DB_NAME)


def test_sync_url() -> str:
    return _swap_database(get_settings().database_url_sync, TEST_DB_NAME)


def _admin_sync_url() -> str:
    return _swap_database(get_settings().database_url_sync, "postgres")


def recreate_test_database() -> None:
    admin_engine = create_engine(_admin_sync_url(), isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            conn.execute(
                text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = :name AND pid <> pg_backend_pid()"
                ),
                {"name": TEST_DB_NAME},
            )
            conn.execute(text(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}"'))
            conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    finally:
        admin_engine.dispose()


def migrate_test_database() -> None:
    cfg = Config(str(_BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(_BACKEND_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", test_sync_url())
    command.upgrade(cfg, "head")
