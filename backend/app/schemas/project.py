from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from app.models import ProjectStatus
from app.schemas.client import ClientSummary
from app.schemas.common import APIModel


class ProjectRead(APIModel):
    id: uuid.UUID
    client_id: uuid.UUID
    name: str
    status: ProjectStatus
    created_at: datetime


class ProjectSummary(APIModel):
    """Lightweight project reference embedded into payment responses."""

    id: uuid.UUID
    name: str
    status: ProjectStatus


class ProjectWithAggregates(ProjectRead):
    client: ClientSummary
    payment_count: int
    total_amount: Decimal
    acts_closed: int
    acts_open: int
