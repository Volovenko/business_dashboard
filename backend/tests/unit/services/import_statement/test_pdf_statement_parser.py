from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from app.services.import_statement.parser import PdfStatementParser, StatementParseError

FIXTURE_PDF = Path(__file__).resolve().parents[3] / "fixtures" / "bank_statement_project_data_clean.pdf"


@pytest.fixture(scope="module")
def parsed_operations():
    pdf_bytes = FIXTURE_PDF.read_bytes()
    return PdfStatementParser().parse(pdf_bytes)


class TestRowExtraction:
    def test_extracts_all_47_operations_from_fixture(self, parsed_operations) -> None:
        # The fixture's footer reads "Количество операций ... 47".
        assert len(parsed_operations) == 47

    def test_parses_first_row_fields(self, parsed_operations) -> None:
        op = parsed_operations[0]
        assert op.payment_date == date(2026, 7, 15)
        assert op.debit_inn == "782934761208"
        assert op.debit_name == "ИП ГРОМОВ А.В."
        assert op.credit_inn == "7801047935"
        assert op.credit_name == "УФК ПО АРКТИЧЕСКОМУ КРАЮ"
        assert op.debit_amount == Decimal("3280.00")
        assert op.credit_amount is None
        assert op.doc_number == "581"
        assert "НДФЛ" in op.payment_purpose

    def test_parses_incoming_payment_with_credit_amount(self, parsed_operations) -> None:
        # First credit-side payment in the statement: ООО "ЛЕДНИК-СТАРТ" on 16.07.
        match = next(
            op
            for op in parsed_operations
            if op.debit_name == 'ООО "ЛЕДНИК-СТАРТ"' and op.payment_date == date(2026, 7, 16)
        )
        assert match.debit_inn == "5408124976"
        assert match.credit_inn == "782934761208"
        assert match.credit_amount == Decimal("33000.00")
        assert match.debit_amount is None
        assert match.doc_number == "9142"
        assert "сч. № 742" in match.payment_purpose


class TestRobustness:
    def test_raises_when_pdf_has_no_operations(self) -> None:
        # An empty PDF stream — pdfplumber will return no tables.
        import io

        import pdfplumber

        # Build an empty PDF by re-saving the fixture's first page with no tables.
        # Easier: pass a minimal valid empty-ish PDF.
        empty_pdf = (
            b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Count 0/Kids[]>>endobj\n"
            b"xref\n0 3\n0000000000 65535 f\n0000000009 00000 n\n"
            b"0000000053 00000 n\ntrailer<</Size 3/Root 1 0 R>>\n"
            b"startxref\n92\n%%EOF\n"
        )
        # Sanity check: pdfplumber can open it.
        with pdfplumber.open(io.BytesIO(empty_pdf)) as pdf:
            assert len(pdf.pages) == 0

        with pytest.raises(StatementParseError):
            PdfStatementParser().parse(empty_pdf)
