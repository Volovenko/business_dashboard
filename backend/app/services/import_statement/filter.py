"""Decides which raw operations represent real client payments."""

from __future__ import annotations

from collections.abc import Iterable

from app.services.import_statement.parser import RawOperation

# Lowercased substrings — any match in the payment purpose drops the row.
_DEPOSIT_KEYWORDS: tuple[str, ...] = (
    "депозит",
    "проценты по депозит",
    "возврат депозит",
)


class StatementFilter:
    """Keeps only incoming client payments, dropping:

    * Outgoing operations (we look at credit-side only).
    * Own transfers (payer INN == owner INN — depot returns, payroll moves).
    * Operations whose counterparty is the servicing bank itself.
    * Deposit-related operations, regardless of payer.
    """

    def __init__(self, *, owner_inn: str, bank_inn: str) -> None:
        self._owner_inn = owner_inn
        self._bank_inn = bank_inn

    def apply(self, operations: Iterable[RawOperation]) -> list[RawOperation]:
        return [op for op in operations if self.accepts(op)]

    def accepts(self, op: RawOperation) -> bool:
        if op.credit_amount is None:
            return False
        if op.debit_inn == self._owner_inn:
            return False
        if op.debit_inn == self._bank_inn:
            return False
        if self._mentions_deposit(op.payment_purpose):
            return False
        return True

    @staticmethod
    def _mentions_deposit(purpose: str) -> bool:
        haystack = purpose.lower()
        return any(keyword in haystack for keyword in _DEPOSIT_KEYWORDS)
