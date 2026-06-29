from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.schemas.common import APIModel, WriteModel


class ParsedPaymentSchema(APIModel):
    """One payment extracted from the bank statement, ready for review/commit."""

    client_inn: str
    client_name: str
    project_name: str
    service_type: str
    payment_date: date
    amount: Decimal
    payment_purpose: str
    invoice_number: str | None
    doc_number: str


class ParsedPaymentInput(WriteModel):
    """Mirror of :class:`ParsedPaymentSchema` accepted by the commit endpoint."""

    client_inn: str
    client_name: str
    project_name: str
    service_type: str
    payment_date: date
    amount: Decimal
    payment_purpose: str
    invoice_number: str | None = None
    doc_number: str


class ImportPreview(APIModel):
    payments: list[ParsedPaymentSchema]


class ImportCommitRequest(WriteModel):
    payments: list[ParsedPaymentInput]


class ImportSummarySchema(APIModel):
    created_clients: int
    created_projects: int
    created_payments: int
    created_acts: int
