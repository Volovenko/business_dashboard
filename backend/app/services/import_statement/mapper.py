"""Maps filtered :class:`RawOperation`s into client-friendly :class:`ParsedPayment`s."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.services.import_statement.classifier import ServiceTypeClassifier
from app.services.import_statement.invoice_extractor import InvoiceExtractor
from app.services.import_statement.parser import RawOperation


@dataclass(frozen=True, slots=True)
class ParsedPayment:
    """Preview-friendly projection of a future :class:`Payment` row.

    Carries everything needed to identify (or create) the client and project,
    and to persist the payment + its act on commit.
    """

    client_inn: str
    client_name: str
    project_name: str
    service_type: str
    payment_date: date
    amount: Decimal
    payment_purpose: str
    invoice_number: str | None
    doc_number: str


class StatementMapper:
    """Stateless transformation: raw operation → parsed payment.

    Does *not* hit the database — that's the import service's job. This layer
    only enriches each row with derived fields (service type, invoice list,
    project name) so the persistence layer has everything it needs in one place.
    """

    def __init__(
        self,
        classifier: ServiceTypeClassifier | None = None,
        invoice_extractor: InvoiceExtractor | None = None,
    ) -> None:
        self._classifier = classifier or ServiceTypeClassifier()
        self._invoice_extractor = invoice_extractor or InvoiceExtractor()

    def map(self, operations: Iterable[RawOperation]) -> list[ParsedPayment]:
        return [self._map_one(op) for op in operations]

    def _map_one(self, op: RawOperation) -> ParsedPayment:
        assert op.credit_amount is not None, "filter must run before mapper"
        assert op.debit_inn is not None and op.debit_name is not None
        service_type = self._classifier.classify(op.payment_purpose)
        return ParsedPayment(
            client_inn=op.debit_inn,
            client_name=op.debit_name,
            project_name=f"{op.debit_name} — {service_type}",
            service_type=service_type,
            payment_date=op.payment_date,
            amount=op.credit_amount,
            payment_purpose=op.payment_purpose,
            invoice_number=self._invoice_extractor.joined(op.payment_purpose),
            doc_number=op.doc_number,
        )
