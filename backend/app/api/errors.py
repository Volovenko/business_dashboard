"""Maps :mod:`app.core.exceptions` domain errors onto HTTP responses.

The handlers live in one module so routers stay free of try/except noise — they
raise domain exceptions and FastAPI's middleware converts them at the edge.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    DomainError,
    EntityNotFoundError,
    ImportError as DomainImportError,
    ValidationError,
)


def _problem(status_code: int, message: str, **extra: object) -> JSONResponse:
    payload: dict[str, object] = {"detail": message}
    payload.update(extra)
    return JSONResponse(status_code=status_code, content=payload)


async def _handle_not_found(_: Request, exc: EntityNotFoundError) -> JSONResponse:
    return _problem(404, str(exc), entity=exc.entity, entity_id=str(exc.entity_id))


async def _handle_validation(_: Request, exc: ValidationError) -> JSONResponse:
    return _problem(422, str(exc))


async def _handle_import_error(_: Request, exc: DomainImportError) -> JSONResponse:
    return _problem(400, str(exc))


async def _handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
    return _problem(400, str(exc))


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(EntityNotFoundError, _handle_not_found)
    app.add_exception_handler(ValidationError, _handle_validation)
    app.add_exception_handler(DomainImportError, _handle_import_error)
    app.add_exception_handler(DomainError, _handle_domain_error)
