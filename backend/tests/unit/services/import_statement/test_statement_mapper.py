from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.services.import_statement.mapper import ParsedPayment, StatementMapper
from app.services.import_statement.parser import RawOperation


def _op(**overrides) -> RawOperation:
    defaults = {
        "payment_date": date(2026, 7, 16),
        "debit_inn": "5408124976",
        "debit_name": 'ООО "ЛЕДНИК-СТАРТ"',
        "credit_inn": "782934761208",
        "credit_name": "ИП ГРОМОВ А.В.",
        "debit_amount": None,
        "credit_amount": Decimal("33000.00"),
        "doc_number": "9142",
        "bank": 'ООО "Речбанк"',
        "payment_purpose": (
            "Оплата за техническое сопровождение сайта по сч. № 742 от 09.07.2026"
        ),
    }
    return RawOperation(**(defaults | overrides))


class TestMap:
    def test_maps_single_operation_to_parsed_payment(self) -> None:
        result = StatementMapper().map([_op()])

        assert len(result) == 1
        payment = result[0]
        assert isinstance(payment, ParsedPayment)
        assert payment.client_inn == "5408124976"
        assert payment.client_name == 'ООО "ЛЕДНИК-СТАРТ"'
        assert payment.payment_date == date(2026, 7, 16)
        assert payment.amount == Decimal("33000.00")
        assert payment.service_type == "сопровождение"
        # Project name combines client + service type for readability in the UI.
        assert payment.project_name == 'ООО "ЛЕДНИК-СТАРТ" — сопровождение'
        assert payment.invoice_number == "742"
        assert payment.doc_number == "9142"

    def test_classifies_service_type_from_purpose(self) -> None:
        op = _op(
            payment_purpose="SEO-продвижение сайта",
            debit_name='ООО "АЛЬФА"',
            debit_inn="1111111111",
        )

        payment = StatementMapper().map([op])[0]

        assert payment.service_type == "SEO"
        assert payment.project_name == 'ООО "АЛЬФА" — SEO'

    def test_keeps_separate_payments_per_input_row(self) -> None:
        # Two payments from the same client for the same service stay as two
        # separate Payment rows — they're different bank operations.
        op1 = _op(doc_number="100", credit_amount=Decimal("1000"))
        op2 = _op(doc_number="101", credit_amount=Decimal("2000"))

        payments = StatementMapper().map([op1, op2])

        assert [p.doc_number for p in payments] == ["100", "101"]
        assert [p.amount for p in payments] == [Decimal("1000"), Decimal("2000")]

    def test_multi_invoice_purpose_produces_one_payment_with_joined_numbers(self) -> None:
        # Mirrors the real "по счетам № 738, 791 и 792" entry — single Payment.
        op = _op(
            payment_purpose="Оплата по счетам № 738, 791 и 792. сопровождение",
            credit_amount=Decimal("69000"),
        )

        payments = StatementMapper().map([op])

        assert len(payments) == 1
        assert payments[0].invoice_number == "738, 791, 792"
        assert payments[0].amount == Decimal("69000")

    def test_invoice_number_is_none_when_purpose_has_no_invoice(self) -> None:
        op = _op(payment_purpose="Прототипы для проектов")

        payment = StatementMapper().map([op])[0]

        assert payment.invoice_number is None
        assert payment.service_type == "прочее"
        assert payment.project_name.endswith("— прочее")
