from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    database_url: str = Field(
        ...,
        description="Async SQLAlchemy DSN (asyncpg driver) used by the application.",
    )
    database_url_sync: str = Field(
        ...,
        description="Sync SQLAlchemy DSN (psycopg2 driver) used by Alembic migrations.",
    )
    attention_threshold_days: int = Field(
        default=30,
        ge=1,
        description="Days after payment_date when a non-closed act becomes 'attention'.",
    )
    owner_inn: str = Field(
        default="782934761208",
        description="ИНН of the statement owner (ИП Громов); used to skip self-transfers on import.",
    )
    bank_inn: str = Field(
        default="7801001407",
        description="ИНН of the servicing bank (АО ФИН-МОСТ БАНК); used to skip bank-side credits.",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
