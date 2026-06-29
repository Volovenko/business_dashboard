"""``/api/payments`` — list payments with rich filters; single fetch with relations."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Query

from app.api.deps import PaymentRepoDep
from app.core.exceptions import EntityNotFoundError
from app.models import ActStatus
from app.schemas.payment import PaymentFilters, PaymentWithRelations

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.get("", response_model=list[PaymentWithRelations])
async def list_payments(
    repo: PaymentRepoDep,
    project_id: uuid.UUID | None = None,
    client_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    act_status: ActStatus | None = None,
    service_type: str | None = None,
    search: str | None = Query(default=None, max_length=255),
) -> list[PaymentWithRelations]:
    filters = PaymentFilters(
        project_id=project_id,
        client_id=client_id,
        date_from=date_from,
        date_to=date_to,
        act_status=act_status,
        service_type=service_type,
        search=search,
    )
    payments = await repo.list(filters)
    return [PaymentWithRelations.model_validate(p) for p in payments]


@router.get("/{payment_id}", response_model=PaymentWithRelations)
async def get_payment(payment_id: uuid.UUID, repo: PaymentRepoDep) -> PaymentWithRelations:
    payment = await repo.get_with_relations(payment_id)
    if payment is None:
        raise EntityNotFoundError("Payment", payment_id)
    return PaymentWithRelations.model_validate(payment)
