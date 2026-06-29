"""``/api/acts`` — partial update of an act (is_sent/is_signed/manager_comment)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.api.deps import SessionDep, UpdateActServiceDep
from app.schemas.act import ActRead, ActUpdate

router = APIRouter(prefix="/api/acts", tags=["acts"])


@router.patch("/{act_id}", response_model=ActRead)
async def update_act(
    act_id: uuid.UUID,
    payload: ActUpdate,
    service: UpdateActServiceDep,
    session: SessionDep,
) -> ActRead:
    act = await service.update(act_id, payload)
    await session.commit()
    # `updated_at` is populated by Postgres via `onupdate=func.now()`, so the
    # in-memory value is expired after flush — refresh before serialising.
    await session.refresh(act)
    return ActRead.model_validate(act)
