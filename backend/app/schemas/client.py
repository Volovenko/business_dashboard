from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.common import APIModel, WriteModel


class ClientCreate(WriteModel):
    name: str = Field(min_length=1, max_length=255)
    inn: str = Field(min_length=10, max_length=12)
    ogrn: str | None = Field(default=None, max_length=20)
    bank_account: str | None = Field(default=None, max_length=30)
    contact_person: str | None = Field(default=None, max_length=255)


class ClientRead(APIModel):
    id: uuid.UUID
    name: str
    inn: str
    ogrn: str | None
    bank_account: str | None
    contact_person: str | None
    created_at: datetime


class ClientSummary(APIModel):
    """Lightweight client reference embedded into payment/project responses."""

    id: uuid.UUID
    name: str
    inn: str


class ClientWithAggregates(ClientRead):
    project_count: int
    payment_count: int
    total_amount: Decimal
