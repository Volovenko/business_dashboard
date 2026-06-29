from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from pydantic import Field

from app.models import ActStatus
from app.schemas.act import ActRead
from app.schemas.client import ClientSummary
from app.schemas.common import APIModel, WriteModel
from app.schemas.project import ProjectSummary


class PaymentCreate(WriteModel):
    project_id: uuid.UUID
    client_id: uuid.UUID
    payment_date: date
    amount: Decimal = Field(gt=Decimal("0"))
    payment_purpose: str = Field(min_length=1, max_length=1000)
    service_type: str = Field(min_length=1, max_length=64)
    invoice_number: str | None = Field(default=None, max_length=128)
    contract_number: str | None = Field(default=None, max_length=128)
    doc_number: str | None = Field(default=None, max_length=64)


class PaymentRead(APIModel):
    id: uuid.UUID
    project_id: uuid.UUID
    client_id: uuid.UUID
    payment_date: date
    amount: Decimal
    payment_purpose: str
    service_type: str
    invoice_number: str | None
    contract_number: str | None
    doc_number: str | None
    created_at: datetime


class PaymentWithRelations(PaymentRead):
    client: ClientSummary
    project: ProjectSummary
    act: ActRead | None


@dataclass(frozen=True, slots=True)
class PaymentFilters:
    """Query-side filter bag used by repositories and routers (not a request body)."""

    project_id: uuid.UUID | None = None
    client_id: uuid.UUID | None = None
    date_from: date | None = None
    date_to: date | None = None
    act_status: ActStatus | None = None
    service_type: str | None = None
    search: str | None = None
