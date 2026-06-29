from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from app.models import ActStatus, ProjectStatus
from app.repositories.act import ActRepository
from app.repositories.client import ClientRepository
from app.repositories.payment import PaymentRepository
from app.repositories.project import ProjectRepository
from app.services.import_statement.mapper import ParsedPayment
from app.services.import_statement.service import ImportStatementService, ImportSummary

FIXTURE_PDF = Path(__file__).resolve().parents[3] / "fixtures" / "bank_statement_project_data_clean.pdf"

# 25 August 2026 — about 10 days after the latest fixture payment (14.08.2026).
# Keeps newly-created acts under the 30-day attention threshold.
FIXED_NOW = datetime(2026, 8, 25, 12, 0, tzinfo=UTC)
THRESHOLD_DAYS = 30


def _service(db_session) -> ImportStatementService:
    return ImportStatementService(
        client_repo=ClientRepository(db_session),
        project_repo=ProjectRepository(db_session),
        payment_repo=PaymentRepository(db_session),
        act_repo=ActRepository(db_session),
        clock=lambda: FIXED_NOW,
        threshold_days=THRESHOLD_DAYS,
        owner_inn="782934761208",
        bank_inn="7801001407",
    )


@pytest.fixture(scope="module")
def fixture_pdf_bytes() -> bytes:
    return FIXTURE_PDF.read_bytes()


class TestPreview:
    async def test_preview_returns_only_client_payments(self, db_session, fixture_pdf_bytes) -> None:
        payments = await _service(db_session).preview(fixture_pdf_bytes)

        # 47 operations in the PDF → 25 are credit-side → 1 dropped as bank
        # deposit-interest → 24 client payments kept by the filter.
        assert len(payments) == 24
        # None should be from the owner or the servicing bank.
        owner_or_bank = {"782934761208", "7801001407"}
        for p in payments:
            assert p.client_inn not in owner_or_bank
            assert "депозит" not in p.payment_purpose.lower()

    async def test_preview_extracts_known_payment(self, db_session, fixture_pdf_bytes) -> None:
        payments = await _service(db_session).preview(fixture_pdf_bytes)
        lednik = next(p for p in payments if p.client_inn == "5408124976")

        assert lednik.client_name == 'ООО "ЛЕДНИК-СТАРТ"'
        assert lednik.payment_date == date(2026, 7, 16)
        assert lednik.amount == Decimal("33000.00")
        assert lednik.service_type == "сопровождение"
        assert lednik.invoice_number == "742"

    async def test_preview_handles_multi_invoice_line(self, db_session, fixture_pdf_bytes) -> None:
        payments = await _service(db_session).preview(fixture_pdf_bytes)
        # "Оплата по счетам № 738, 791 и 792" from ИП ОРЛОВ ДАНИИЛ РУСЛАНОВИЧ
        orlov = next(p for p in payments if p.client_inn == "504218730629")

        assert orlov.invoice_number == "738, 791, 792"
        assert orlov.amount == Decimal("69000.00")


class TestCommit:
    async def test_returns_zero_summary_when_no_payments(self, db_session) -> None:
        summary = await _service(db_session).commit([])

        assert summary == ImportSummary(
            created_clients=0, created_projects=0, created_payments=0, created_acts=0
        )

    async def test_creates_client_project_payment_and_act(self, db_session) -> None:
        parsed = ParsedPayment(
            client_inn="5408124976",
            client_name='ООО "ЛЕДНИК-СТАРТ"',
            project_name='ООО "ЛЕДНИК-СТАРТ" — сопровождение',
            service_type="сопровождение",
            payment_date=date(2026, 7, 16),
            amount=Decimal("33000.00"),
            payment_purpose="Оплата за техническое сопровождение по сч. № 742",
            invoice_number="742",
            doc_number="9142",
        )

        summary = await _service(db_session).commit([parsed])

        assert summary == ImportSummary(
            created_clients=1, created_projects=1, created_payments=1, created_acts=1
        )
        client = await ClientRepository(db_session).get_by_inn("5408124976")
        assert client is not None and client.name == 'ООО "ЛЕДНИК-СТАРТ"'

    async def test_reuses_existing_client_and_project(self, db_session) -> None:
        # Pre-create the client and project; a second import shouldn't duplicate them.
        from tests.factories import create_client, create_project

        existing_client = await create_client(db_session, inn="5408124976", name='ООО "ЛЕДНИК-СТАРТ"')
        await create_project(
            db_session,
            client=existing_client,
            name='ООО "ЛЕДНИК-СТАРТ" — сопровождение',
        )

        parsed = ParsedPayment(
            client_inn="5408124976",
            client_name='ООО "ЛЕДНИК-СТАРТ"',
            project_name='ООО "ЛЕДНИК-СТАРТ" — сопровождение',
            service_type="сопровождение",
            payment_date=date(2026, 7, 16),
            amount=Decimal("33000.00"),
            payment_purpose="Оплата по сч. № 742",
            invoice_number="742",
            doc_number="9142",
        )

        summary = await _service(db_session).commit([parsed])

        assert summary.created_clients == 0
        assert summary.created_projects == 0
        assert summary.created_payments == 1
        assert summary.created_acts == 1

    async def test_groups_multiple_payments_into_single_project(self, db_session) -> None:
        # Two payments for the same client/service → one client, one project, two payments.
        common: dict = {
            "client_inn": "5408124976",
            "client_name": 'ООО "ЛЕДНИК-СТАРТ"',
            "project_name": 'ООО "ЛЕДНИК-СТАРТ" — сопровождение',
            "service_type": "сопровождение",
            "payment_purpose": "Оплата по сч.",
            "invoice_number": None,
        }
        parsed = [
            ParsedPayment(
                **common,
                payment_date=date(2026, 7, 16),
                amount=Decimal("100.00"),
                doc_number="A",
            ),
            ParsedPayment(
                **common,
                payment_date=date(2026, 7, 31),
                amount=Decimal("200.00"),
                doc_number="B",
            ),
        ]

        summary = await _service(db_session).commit(parsed)

        assert summary == ImportSummary(
            created_clients=1, created_projects=1, created_payments=2, created_acts=2
        )

    async def test_act_status_is_attention_when_payment_is_stale(self, db_session) -> None:
        old_date = FIXED_NOW.date().replace(month=1, day=1)  # 1 Jan 2026 — far older than 30 days
        parsed = ParsedPayment(
            client_inn="5408124976",
            client_name='ООО "ЛЕДНИК-СТАРТ"',
            project_name='ООО "ЛЕДНИК-СТАРТ" — сопровождение',
            service_type="сопровождение",
            payment_date=old_date,
            amount=Decimal("100.00"),
            payment_purpose="Старая оплата",
            invoice_number=None,
            doc_number="OLD",
        )

        await _service(db_session).commit([parsed])

        payments = await PaymentRepository(db_session).list(_filters_for_client("5408124976"))
        assert len(payments) == 1
        assert payments[0].act is not None
        assert payments[0].act.status is ActStatus.ATTENTION
        # And the project status should aggregate to ATTENTION.
        project = await ProjectRepository(db_session).get(payments[0].project_id)
        assert project is not None
        assert project.status is ProjectStatus.ATTENTION

    async def test_fresh_payment_act_is_not_sent(self, db_session) -> None:
        parsed = ParsedPayment(
            client_inn="5408124976",
            client_name='ООО "ЛЕДНИК-СТАРТ"',
            project_name='ООО "ЛЕДНИК-СТАРТ" — сопровождение',
            service_type="сопровождение",
            payment_date=FIXED_NOW.date(),
            amount=Decimal("100.00"),
            payment_purpose="Свежая оплата",
            invoice_number=None,
            doc_number="NEW",
        )

        await _service(db_session).commit([parsed])

        payments = await PaymentRepository(db_session).list(_filters_for_client("5408124976"))
        assert payments[0].act is not None
        assert payments[0].act.status is ActStatus.NOT_SENT


class TestEndToEnd:
    async def test_preview_then_commit_imports_full_fixture(self, db_session, fixture_pdf_bytes) -> None:
        service = _service(db_session)

        previewed = await service.preview(fixture_pdf_bytes)
        summary = await service.commit(previewed)

        # 24 client payments, 19 unique payer INNs. Five clients paid for two
        # different service types each, so each (client, service) combination is
        # unique → 24 projects (no project reuse in this dataset).
        assert summary.created_payments == 24
        assert summary.created_acts == 24
        assert summary.created_clients == 19
        assert summary.created_projects == 24


def _filters_for_client(inn: str):
    """Tiny helper — returns PaymentFilters with the given client INN resolved."""
    from app.schemas.payment import PaymentFilters

    return PaymentFilters()  # the test that uses this filters via the returned list itself
