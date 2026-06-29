"""Detail schemas that combine multiple aggregates — kept in their own module
to side-step the schema-level import cycle between :mod:`project` and
:mod:`payment`."""

from __future__ import annotations

from app.schemas.client import ClientRead
from app.schemas.payment import PaymentRead
from app.schemas.project import ProjectRead


class ClientWithProjects(ClientRead):
    projects: list[ProjectRead]


class ProjectWithPayments(ProjectRead):
    payments: list[PaymentRead]
