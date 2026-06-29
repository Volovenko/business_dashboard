"""FastAPI application entrypoint — assembles routers, CORS, and error handlers."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import acts, clients, import_statement, payments, projects, summary
from app.api.errors import register_exception_handlers
from app.core.config import get_settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="Business Dashboard API",
        version="0.1.0",
        description="Payments, projects, clients, and acts for ИП Громов А.В.",
    )

    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    for router in (
        summary.router,
        clients.router,
        projects.router,
        payments.router,
        acts.router,
        import_statement.router,
    ):
        app.include_router(router)

    @app.get("/healthz", tags=["meta"])
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
