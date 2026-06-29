"""Orchestrator for the two-phase bank statement import (preview → commit)."""

from __future__ import annotations

import uuid
from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.models import Act, ActStatus, Client, Payment, Project
from app.services.act_status_service import ActStatusService
from app.services.import_statement.filter import StatementFilter
from app.services.import_statement.mapper import ParsedPayment, StatementMapper
from app.services.import_statement.parser import PdfStatementParser
from app.services.project_status_service import ProjectStatusService


@dataclass(frozen=True, slots=True)
class ImportSummary:
    """Counters returned by :meth:`ImportStatementService.commit`."""

    created_clients: int
    created_projects: int
    created_payments: int
    created_acts: int


class _ClientRepo(Protocol):
    async def get_by_inn(self, inn: str) -> Client | None: ...
    async def add(self, client: Client) -> None: ...


class _ProjectRepo(Protocol):
    async def get_by_client_and_name(self, client_id: uuid.UUID, name: str) -> Project | None: ...
    async def add(self, project: Project) -> None: ...
    async def get(self, project_id: uuid.UUID) -> Project | None: ...
    async def update_status(self, project: Project, status) -> None: ...


class _PaymentRepo(Protocol):
    async def add(self, payment: Payment) -> None: ...


class _ActRepo(Protocol):
    async def add(self, act: Act) -> None: ...
    async def list_statuses_for_project(self, project_id: uuid.UUID) -> list[ActStatus]: ...


class ImportStatementService:
    """Two-phase import:

    * :meth:`preview` — parses the PDF, applies filtering and mapping; returns
      what *would* be created. No DB writes.
    * :meth:`commit` — takes the preview output (or a manually edited subset),
      creates clients/projects/payments/acts, and recomputes each touched
      project's aggregate status.

    Splitting the two lets the UI show a confirmation step before persisting.
    """

    def __init__(
        self,
        *,
        client_repo: _ClientRepo,
        project_repo: _ProjectRepo,
        payment_repo: _PaymentRepo,
        act_repo: _ActRepo,
        clock: Callable[[], datetime],
        threshold_days: int,
        owner_inn: str,
        bank_inn: str,
        parser: PdfStatementParser | None = None,
        mapper: StatementMapper | None = None,
    ) -> None:
        self._client_repo = client_repo
        self._project_repo = project_repo
        self._payment_repo = payment_repo
        self._act_repo = act_repo
        self._clock = clock
        self._threshold_days = threshold_days
        self._parser = parser or PdfStatementParser()
        self._filter = StatementFilter(owner_inn=owner_inn, bank_inn=bank_inn)
        self._mapper = mapper or StatementMapper()

    async def preview(self, pdf_bytes: bytes) -> list[ParsedPayment]:
        raw = self._parser.parse(pdf_bytes)
        filtered = self._filter.apply(raw)
        return self._mapper.map(filtered)

    async def commit(self, payments: Iterable[ParsedPayment]) -> ImportSummary:
        counters = _Counters()
        touched_project_ids: set[uuid.UUID] = set()

        for parsed in payments:
            client = await self._upsert_client(parsed, counters)
            project = await self._upsert_project(client, parsed, counters)
            await self._create_payment_and_act(client, project, parsed, counters)
            touched_project_ids.add(project.id)

        for project_id in touched_project_ids:
            await self._reaggregate_project_status(project_id)

        return counters.to_summary()

    async def _upsert_client(self, parsed: ParsedPayment, counters: _Counters) -> Client:
        existing = await self._client_repo.get_by_inn(parsed.client_inn)
        if existing is not None:
            return existing
        client = Client(name=parsed.client_name, inn=parsed.client_inn)
        await self._client_repo.add(client)
        counters.clients += 1
        return client

    async def _upsert_project(
        self, client: Client, parsed: ParsedPayment, counters: _Counters
    ) -> Project:
        existing = await self._project_repo.get_by_client_and_name(client.id, parsed.project_name)
        if existing is not None:
            return existing
        project = Project(client_id=client.id, name=parsed.project_name)
        await self._project_repo.add(project)
        counters.projects += 1
        return project

    async def _create_payment_and_act(
        self,
        client: Client,
        project: Project,
        parsed: ParsedPayment,
        counters: _Counters,
    ) -> None:
        payment = Payment(
            client_id=client.id,
            project_id=project.id,
            payment_date=parsed.payment_date,
            amount=parsed.amount,
            payment_purpose=parsed.payment_purpose,
            service_type=parsed.service_type,
            invoice_number=parsed.invoice_number,
            doc_number=parsed.doc_number,
        )
        await self._payment_repo.add(payment)
        counters.payments += 1

        now = self._clock()
        status = ActStatusService.compute(
            is_sent=False,
            is_signed=False,
            payment_date=parsed.payment_date,
            today=now.date(),
            threshold_days=self._threshold_days,
        )
        act = Act(payment_id=payment.id, status=status)
        await self._act_repo.add(act)
        counters.acts += 1

    async def _reaggregate_project_status(self, project_id: uuid.UUID) -> None:
        project = await self._project_repo.get(project_id)
        if project is None:
            return
        statuses = await self._act_repo.list_statuses_for_project(project_id)
        new_status = ProjectStatusService.aggregate(
            current_status=project.status,
            act_statuses=statuses,
        )
        if new_status is not project.status:
            await self._project_repo.update_status(project, new_status)


@dataclass
class _Counters:
    clients: int = 0
    projects: int = 0
    payments: int = 0
    acts: int = 0

    def to_summary(self) -> ImportSummary:
        return ImportSummary(
            created_clients=self.clients,
            created_projects=self.projects,
            created_payments=self.payments,
            created_acts=self.acts,
        )
