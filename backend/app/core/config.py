from __future__ import annotations

from functools import lru_cache

from pydantic import Field, model_validator
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
        description="Async SQLAlchemy DSN (asyncpg driver). "
                    "Render provides postgresql://... — it will be auto-converted.",
    )
    database_url_sync: str | None = Field(
        default=None,
        description="Sync DSN for Alembic. Derived from database_url if not set.",
    )
    attention_threshold_days: int = Field(
        default=30,
        ge=1,
        description="Days after payment_date when a non-closed act becomes 'attention'.",
    )
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        description="Allowed CORS origins. Set CORS_ORIGINS=https://your-app.onrender.com in prod.",
    )
    owner_inn: str = Field(
        default="782934761208",
        description="ИНН of the statement owner; used to skip self-transfers on import.",
    )
    bank_inn: str = Field(
        default="7801001407",
        description="ИНН of the servicing bank; used to skip bank-side credits.",
    )

    @model_validator(mode="after")
    def _derive_sync_url(self) -> Settings:
        if self.database_url_sync is None:
            url = self.database_url
            # Render gives postgresql://... — convert for asyncpg and psycopg2
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            self.database_url = url
            self.database_url_sync = url.replace("+asyncpg", "+psycopg2")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
