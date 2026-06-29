from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import pytest

from app.repositories.summary import SummaryRow
from app.schemas.summary import SummaryRead
from app.services.summary_service import SummaryService


@dataclass
class _FakeSummaryRepo:
    row: SummaryRow

    async def snapshot(self) -> SummaryRow:
        return self.row


@pytest.fixture
def sample_row() -> SummaryRow:
    return SummaryRow(
        total_amount=Decimal("1234567.00"),
        total_projects=19,
        total_payments=25,
        closed_amount=Decimal("800000.00"),
        open_amount=Decimal("434567.00"),
        acts_not_sent=5,
        acts_waiting_signature=3,
    )


class TestBuild:
    async def test_returns_summary_read_with_repo_values(self, sample_row: SummaryRow) -> None:
        service = SummaryService(_FakeSummaryRepo(sample_row))

        result = await service.build()

        assert isinstance(result, SummaryRead)
        assert result.total_amount == sample_row.total_amount
        assert result.total_projects == sample_row.total_projects
        assert result.total_payments == sample_row.total_payments
        assert result.closed_amount == sample_row.closed_amount
        assert result.open_amount == sample_row.open_amount
        assert result.acts_not_sent == sample_row.acts_not_sent
        assert result.acts_waiting_signature == sample_row.acts_waiting_signature
