from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field, model_validator

from app.models import ActStatus
from app.schemas.common import APIModel, WriteModel


class ActUpdate(WriteModel):
    is_sent: bool | None = None
    is_signed: bool | None = None
    manager_comment: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def _signed_requires_sent(self) -> ActUpdate:
        # A client cannot sign a document that was never delivered. The pure
        # status function tolerates this combination, but the API rejects it
        # so invalid state never enters the database.
        if self.is_signed is True and self.is_sent is False:
            raise ValueError("is_signed=True is not allowed together with is_sent=False")
        return self


class ActRead(APIModel):
    id: uuid.UUID
    payment_id: uuid.UUID
    is_sent: bool
    sent_at: datetime | None
    is_signed: bool
    signed_at: datetime | None
    status: ActStatus
    manager_comment: str | None
    created_at: datetime
    updated_at: datetime
