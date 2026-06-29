"""``/api/summary`` — dashboard KPI snapshot."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import SummaryServiceDep
from app.schemas.summary import SummaryRead

router = APIRouter(prefix="/api/summary", tags=["summary"])


@router.get("", response_model=SummaryRead)
async def get_summary(service: SummaryServiceDep) -> SummaryRead:
    return await service.build()
