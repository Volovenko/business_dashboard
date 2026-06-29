from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    """Base for read schemas that hydrate from ORM attributes."""

    model_config = ConfigDict(from_attributes=True)


class WriteModel(BaseModel):
    """Base for write schemas — strict, no extra fields, no ORM coupling."""

    model_config = ConfigDict(extra="forbid")
