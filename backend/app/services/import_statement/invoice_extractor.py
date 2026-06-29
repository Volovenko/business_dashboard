"""Pulls invoice numbers (счёт №…) out of a payment-purpose string.

Contracts ("договор № …") are deliberately ignored — they're a different field.
"""

from __future__ import annotations

import re

# Matches any «сч…» word followed by «№ NUM[, NUM, … и NUM]» — covers
# "сч.", "счет", "счёт", "счету", "счетам", "счёт-заказу" and friends.
# The leading `(?:^|\W)` keeps us from picking up «счетчик» mid-word.
_INVOICE_BLOCK = re.compile(
    r"(?:^|\W)сч(?:\.|[её]т[а-яё]*(?:-?[а-яё]+)?)\s*№\s*([0-9 ,и]+)",
    flags=re.IGNORECASE,
)
_NUMBER = re.compile(r"\d+")


class InvoiceExtractor:
    """Returns the list of invoice numbers mentioned next to a сч./счёт keyword."""

    def extract(self, payment_purpose: str) -> list[str]:
        numbers: list[str] = []
        for match in _INVOICE_BLOCK.finditer(payment_purpose):
            numbers.extend(_NUMBER.findall(match.group(1)))
        return numbers

    def joined(self, payment_purpose: str) -> str | None:
        numbers = self.extract(payment_purpose)
        return ", ".join(numbers) if numbers else None
