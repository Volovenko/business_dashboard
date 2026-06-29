from __future__ import annotations

from decimal import Decimal

from app.schemas.common import APIModel


class SummaryRead(APIModel):
    total_amount: Decimal
    total_projects: int
    total_payments: int
    closed_amount: Decimal
    open_amount: Decimal
    acts_not_sent: int
    acts_waiting_signature: int
