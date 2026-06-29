"""PDF parser for ФИН-МОСТ БАНК account statements.

Returns a flat list of :class:`RawOperation` rows — every line in the statement,
without any filtering or business interpretation. Filtering and mapping live in
separate modules so the parser stays narrowly responsible for "PDF text → rows".
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import pdfplumber


@dataclass(frozen=True, slots=True)
class RawOperation:
    """One row of the bank statement, as extracted from the PDF.

    Either ``debit_amount`` or ``credit_amount`` is set (never both).
    """

    payment_date: date
    debit_inn: str | None
    debit_name: str | None
    credit_inn: str | None
    credit_name: str | None
    debit_amount: Decimal | None
    credit_amount: Decimal | None
    doc_number: str
    bank: str
    payment_purpose: str


_DATE_RE = re.compile(r"^(\d{2})\.(\d{2})\.(\d{4})$")
_INN_RE = re.compile(r"ИНН\s+(\d+)")
_AMOUNT_RE = re.compile(r"^\s*([\d\s]+,\d{2})\s*$")


class StatementParseError(Exception):
    """Raised when the PDF doesn't look like the expected ФИН-МОСТ format."""


class PdfStatementParser:
    """Extracts rows from a ФИН-МОСТ БАНК PDF statement via pdfplumber.

    Layout assumed (verified against the fixture statement):

    * Column 0 — transaction date (``DD.MM.YYYY``).
    * Column 1 — debit (payer) account block: account number, INN, OGRN, name.
    * Column 2 — credit (recipient) account block: same shape.
    * Column 3 — debit amount, column 4 — credit amount (one of the two filled).
    * Column 5 — document number, column 7 — bank, column 8 — purpose.

    Header rows (first two of every page) are skipped by detecting the literal
    "Дата" header text in column 0.
    """

    def parse(self, pdf_bytes: bytes) -> list[RawOperation]:
        import io

        operations: list[RawOperation] = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                for table in page.extract_tables():
                    operations.extend(self._rows_from_table(table))
        if not operations:
            raise StatementParseError("no operations parsed from PDF")
        return operations

    def _rows_from_table(self, table: list[list[str | None]]) -> list[RawOperation]:
        rows: list[RawOperation] = []
        for raw_row in table:
            row = [cell or "" for cell in raw_row]
            if not self._looks_like_data_row(row):
                continue
            rows.append(self._row_to_operation(row))
        return rows

    @staticmethod
    def _looks_like_data_row(row: list[str]) -> bool:
        return bool(row) and bool(_DATE_RE.match(row[0].strip()))

    def _row_to_operation(self, row: list[str]) -> RawOperation:
        debit_inn, debit_name = self._parse_account_block(row[1])
        credit_inn, credit_name = self._parse_account_block(row[2])
        return RawOperation(
            payment_date=self._parse_date(row[0].strip()),
            debit_inn=debit_inn,
            debit_name=debit_name,
            credit_inn=credit_inn,
            credit_name=credit_name,
            debit_amount=self._parse_amount(row[3]),
            credit_amount=self._parse_amount(row[4]),
            doc_number=row[5].strip(),
            bank=" ".join(row[7].split()),
            payment_purpose=" ".join(row[8].split()),
        )

    @staticmethod
    def _parse_date(text: str) -> date:
        match = _DATE_RE.match(text)
        if match is None:
            raise StatementParseError(f"unparseable date: {text!r}")
        day, month, year = match.groups()
        return date(int(year), int(month), int(day))

    @staticmethod
    def _parse_amount(text: str) -> Decimal | None:
        match = _AMOUNT_RE.match(text)
        if match is None:
            return None
        normalized = match.group(1).replace(" ", "").replace(",", ".")
        return Decimal(normalized)

    @staticmethod
    def _parse_account_block(text: str) -> tuple[str | None, str | None]:
        """Account blocks look like::

            40802810937184056213
            ИНН 782934761208
            ОГРНИП 326784500918273
            ИП ГРОМОВ А.В.

        The name is the last non-empty line; the INN is captured from its label.
        """
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return None, None
        inn_match = _INN_RE.search(text)
        inn = inn_match.group(1) if inn_match else None
        name = lines[-1]
        return inn, name
