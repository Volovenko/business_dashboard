"""``/api/import`` — two-phase bank statement import (preview → commit)."""

from __future__ import annotations

from fastapi import APIRouter, File, UploadFile

from app.api.deps import ImportServiceDep, SessionDep
from app.core.exceptions import ImportError as DomainImportError
from app.schemas.import_statement import (
    ImportCommitRequest,
    ImportPreview,
    ImportSummarySchema,
    ParsedPaymentSchema,
)
from app.services.import_statement.mapper import ParsedPayment

router = APIRouter(prefix="/api/import", tags=["import"])


@router.post("/preview", response_model=ImportPreview)
async def preview_import(
    service: ImportServiceDep,
    file: UploadFile = File(..., description="Bank statement PDF"),
) -> ImportPreview:
    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise DomainImportError("Uploaded file is empty")
    parsed = await service.preview(pdf_bytes)
    return ImportPreview(payments=[ParsedPaymentSchema.model_validate(p) for p in parsed])


@router.post("/commit", response_model=ImportSummarySchema)
async def commit_import(
    payload: ImportCommitRequest,
    service: ImportServiceDep,
    session: SessionDep,
) -> ImportSummarySchema:
    parsed = [
        ParsedPayment(
            client_inn=item.client_inn,
            client_name=item.client_name,
            project_name=item.project_name,
            service_type=item.service_type,
            payment_date=item.payment_date,
            amount=item.amount,
            payment_purpose=item.payment_purpose,
            invoice_number=item.invoice_number,
            doc_number=item.doc_number,
        )
        for item in payload.payments
    ]
    summary = await service.commit(parsed)
    await session.commit()
    return ImportSummarySchema.model_validate(summary)
