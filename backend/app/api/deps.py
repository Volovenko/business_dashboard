"""FastAPI dependency wiring: session → repositories → services."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.repositories.act import ActRepository
from app.repositories.client import ClientRepository
from app.repositories.payment import PaymentRepository
from app.repositories.project import ProjectRepository
from app.repositories.summary import SummaryRepository
from app.services.import_statement.service import ImportStatementService
from app.services.summary_service import SummaryService
from app.services.update_act_service import UpdateActService

SessionDep = Annotated[AsyncSession, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_client_repo(session: SessionDep) -> ClientRepository:
    return ClientRepository(session)


def get_project_repo(session: SessionDep) -> ProjectRepository:
    return ProjectRepository(session)


def get_payment_repo(session: SessionDep) -> PaymentRepository:
    return PaymentRepository(session)


def get_act_repo(session: SessionDep) -> ActRepository:
    return ActRepository(session)


def get_summary_repo(session: SessionDep) -> SummaryRepository:
    return SummaryRepository(session)


ClientRepoDep = Annotated[ClientRepository, Depends(get_client_repo)]
ProjectRepoDep = Annotated[ProjectRepository, Depends(get_project_repo)]
PaymentRepoDep = Annotated[PaymentRepository, Depends(get_payment_repo)]
ActRepoDep = Annotated[ActRepository, Depends(get_act_repo)]
SummaryRepoDep = Annotated[SummaryRepository, Depends(get_summary_repo)]


def _utc_now() -> datetime:
    return datetime.now(UTC)


def get_summary_service(repo: SummaryRepoDep) -> SummaryService:
    return SummaryService(repo)


def get_update_act_service(
    act_repo: ActRepoDep,
    project_repo: ProjectRepoDep,
    settings: SettingsDep,
) -> UpdateActService:
    return UpdateActService(
        act_repo=act_repo,
        project_repo=project_repo,
        clock=_utc_now,
        threshold_days=settings.attention_threshold_days,
    )


def get_import_service(
    client_repo: ClientRepoDep,
    project_repo: ProjectRepoDep,
    payment_repo: PaymentRepoDep,
    act_repo: ActRepoDep,
    settings: SettingsDep,
) -> ImportStatementService:
    return ImportStatementService(
        client_repo=client_repo,
        project_repo=project_repo,
        payment_repo=payment_repo,
        act_repo=act_repo,
        clock=_utc_now,
        threshold_days=settings.attention_threshold_days,
        owner_inn=settings.owner_inn,
        bank_inn=settings.bank_inn,
    )


SummaryServiceDep = Annotated[SummaryService, Depends(get_summary_service)]
UpdateActServiceDep = Annotated[UpdateActService, Depends(get_update_act_service)]
ImportServiceDep = Annotated[ImportStatementService, Depends(get_import_service)]
