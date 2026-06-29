from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.services.import_statement.filter import StatementFilter
from app.services.import_statement.parser import RawOperation

OWNER_INN = "782934761208"
BANK_INN = "7801001407"


def _op(**overrides) -> RawOperation:
    defaults = {
        "payment_date": date(2026, 7, 16),
        "debit_inn": "5408124976",
        "debit_name": 'ООО "ЛЕДНИК-СТАРТ"',
        "credit_inn": OWNER_INN,
        "credit_name": "ИП ГРОМОВ А.В.",
        "debit_amount": None,
        "credit_amount": Decimal("33000"),
        "doc_number": "9142",
        "bank": 'ООО "Речбанк"',
        "payment_purpose": "Оплата за техническое сопровождение сайта по сч. № 742",
    }
    return RawOperation(**(defaults | overrides))


def _filter() -> StatementFilter:
    return StatementFilter(owner_inn=OWNER_INN, bank_inn=BANK_INN)


class TestKeepsIncomingClientPayments:
    def test_keeps_typical_client_credit(self) -> None:
        op = _op()
        assert _filter().accepts(op) is True

    def test_keeps_when_credit_amount_is_set_and_debit_is_zero(self) -> None:
        # Even non-bank own credits would pass amount-wise — we only filter
        # on counterparty INN and purpose keywords.
        op = _op(debit_amount=Decimal("0"))
        assert _filter().accepts(op) is True


class TestDropsOutgoingPayments:
    def test_drops_when_credit_amount_is_none(self) -> None:
        op = _op(
            credit_amount=None,
            debit_amount=Decimal("324000"),
            debit_inn=OWNER_INN,
            credit_inn="781507438291",
            credit_name="КИСЕЛЕВ ПАВЕЛ ДМИТРИЕВИЧ",
        )
        assert _filter().accepts(op) is False


class TestDropsOwnTransfers:
    def test_drops_when_payer_inn_equals_owner_inn(self) -> None:
        op = _op(debit_inn=OWNER_INN, debit_name="ИП ГРОМОВ А.В.")
        assert _filter().accepts(op) is False


class TestDropsBankOperations:
    def test_drops_when_payer_is_servicing_bank(self) -> None:
        op = _op(
            debit_inn=BANK_INN,
            debit_name='АО "ФИН-МОСТ БАНК"',
            payment_purpose="Начисление процентов по депозитному договору",
        )
        assert _filter().accepts(op) is False


class TestDropsDepositRelatedPurposes:
    def test_drops_deposit_return(self) -> None:
        op = _op(
            debit_inn=OWNER_INN,
            payment_purpose="Возврат депозита по договору 981200-АНОН",
        )
        # Caught by either own-transfer rule or deposit-keyword rule.
        assert _filter().accepts(op) is False

    def test_drops_deposit_interest_even_from_unknown_payer(self) -> None:
        op = _op(
            debit_inn="9999999999",
            payment_purpose="Начисление процентов по депозитному договору",
        )
        assert _filter().accepts(op) is False

    def test_keyword_match_is_case_insensitive(self) -> None:
        op = _op(payment_purpose="ВОЗВРАТ ДЕПОЗИТА")
        assert _filter().accepts(op) is False


class TestApplyAll:
    def test_returns_only_accepted_operations(self) -> None:
        ops = [
            _op(),  # keep
            _op(debit_inn=OWNER_INN),  # own → drop
            _op(debit_inn=BANK_INN),  # bank → drop
            _op(payment_purpose="депозит"),  # keyword → drop
            _op(doc_number="999"),  # keep
        ]
        kept = _filter().apply(ops)
        assert [op.doc_number for op in kept] == ["9142", "999"]
