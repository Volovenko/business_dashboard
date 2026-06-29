from __future__ import annotations

import pytest

from app.services.import_statement.invoice_extractor import InvoiceExtractor


@pytest.mark.parametrize(
    ("purpose", "expected"),
    [
        ("Оплата по счету № 742 от 09.07.2026 г.", ["742"]),
        ("Оплата по сч. № 728 от 15.07.2026", ["728"]),
        ("Оплата по счёту № 798 от 31.07.2026", ["798"]),
        ("по счёт-заказу № 5381124 от 01.08.2026", ["5381124"]),
        # Multiple invoices: "по счетам № 738, 791 и 792"
        ("Оплата по счетам № 738, 791 и 792", ["738", "791", "792"]),
        # Trailing punctuation should be stripped.
        ("Оплата по счету № 768.", ["768"]),
    ],
)
def test_extracts_invoice_numbers(purpose: str, expected: list[str]) -> None:
    assert InvoiceExtractor().extract(purpose) == expected


def test_returns_empty_when_no_invoice_keyword() -> None:
    assert InvoiceExtractor().extract("Прототипы для проектов") == []


def test_ignores_contract_numbers() -> None:
    # "договору № 418" is a contract, not invoice — must not be picked up.
    assert InvoiceExtractor().extract("услуги по договору № 418 от 02.03.2025") == []


def test_joined_returns_comma_separated_string() -> None:
    assert InvoiceExtractor().joined("Оплата по счетам № 738, 791 и 792") == "738, 791, 792"


def test_joined_returns_none_when_no_invoice() -> None:
    assert InvoiceExtractor().joined("Прототипы для проектов") is None
