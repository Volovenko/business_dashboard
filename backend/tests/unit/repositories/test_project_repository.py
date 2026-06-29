from __future__ import annotations

import uuid
from decimal import Decimal

from app.models import ProjectStatus
from app.repositories.project import ProjectAggregateRow, ProjectRepository
from tests.factories import create_client, create_payment, create_project
from tests.sql_counter import count_queries


class TestGet:
    async def test_returns_project_by_id(self, db_session) -> None:
        client = await create_client(db_session)
        project = await create_project(db_session, client=client)

        fetched = await ProjectRepository(db_session).get(project.id)

        assert fetched is not None
        assert fetched.id == project.id

    async def test_returns_none_when_missing(self, db_session) -> None:
        assert await ProjectRepository(db_session).get(uuid.uuid4()) is None


class TestListWithAggregates:
    async def test_returns_empty_when_no_projects(self, db_session) -> None:
        assert await ProjectRepository(db_session).list_with_aggregates() == []

    async def test_zero_aggregates_for_project_without_payments(self, db_session) -> None:
        client = await create_client(db_session)
        project = await create_project(db_session, client=client)

        rows = await ProjectRepository(db_session).list_with_aggregates()

        assert rows == [
            ProjectAggregateRow(
                project=project,
                client=client,
                payment_count=0,
                total_amount=Decimal("0"),
                acts_closed=0,
                acts_open=0,
            )
        ]

    async def test_aggregates_payments_per_project(self, db_session) -> None:
        client = await create_client(db_session)
        project_a = await create_project(db_session, client=client, name="Альфа")
        project_b = await create_project(db_session, client=client, name="Бета")
        await create_payment(db_session, client=client, project=project_a, amount=Decimal("100"))
        await create_payment(db_session, client=client, project=project_a, amount=Decimal("250"))
        await create_payment(db_session, client=client, project=project_b, amount=Decimal("700"))

        rows = {r.project.id: r for r in await ProjectRepository(db_session).list_with_aggregates()}

        assert rows[project_a.id].payment_count == 2
        assert rows[project_a.id].total_amount == Decimal("350")
        assert rows[project_a.id].client.id == client.id
        assert rows[project_b.id].payment_count == 1
        assert rows[project_b.id].total_amount == Decimal("700")

    async def test_list_runs_in_constant_number_of_queries(self, db_session, engine) -> None:
        for _ in range(4):
            client = await create_client(db_session)
            for _ in range(3):
                project = await create_project(db_session, client=client)
                await create_payment(db_session, client=client, project=project)
                await create_payment(db_session, client=client, project=project)
        await db_session.flush()

        with count_queries(engine) as queries:
            rows = await ProjectRepository(db_session).list_with_aggregates()

        assert len(rows) == 12
        assert len(queries) == 1, f"expected 1 query, got {len(queries)}: {queries}"

    async def test_filter_by_client(self, db_session) -> None:
        client_a = await create_client(db_session)
        client_b = await create_client(db_session)
        project_a = await create_project(db_session, client=client_a)
        await create_project(db_session, client=client_b)

        rows = await ProjectRepository(db_session).list_with_aggregates(client_id=client_a.id)

        assert len(rows) == 1
        assert rows[0].project.id == project_a.id


class TestGetWithPayments:
    async def test_eager_loads_payments_in_two_queries(self, db_session, engine) -> None:
        client = await create_client(db_session)
        project = await create_project(db_session, client=client)
        await create_payment(db_session, client=client, project=project)
        await create_payment(db_session, client=client, project=project)
        await db_session.flush()

        with count_queries(engine) as queries:
            fetched = await ProjectRepository(db_session).get_with_payments(project.id)

        assert fetched is not None
        assert len(fetched.payments) == 2
        assert len(queries) == 2, queries

    async def test_returns_none_when_missing(self, db_session) -> None:
        assert await ProjectRepository(db_session).get_with_payments(uuid.uuid4()) is None


class TestGetByClientAndName:
    async def test_returns_project_when_match_exists(self, db_session) -> None:
        client = await create_client(db_session)
        project = await create_project(db_session, client=client, name="Сайт")

        fetched = await ProjectRepository(db_session).get_by_client_and_name(client.id, "Сайт")

        assert fetched is not None
        assert fetched.id == project.id

    async def test_returns_none_when_name_differs(self, db_session) -> None:
        client = await create_client(db_session)
        await create_project(db_session, client=client, name="Сайт")

        fetched = await ProjectRepository(db_session).get_by_client_and_name(client.id, "Лендинг")

        assert fetched is None

    async def test_returns_none_when_client_differs(self, db_session) -> None:
        client_a = await create_client(db_session)
        client_b = await create_client(db_session)
        await create_project(db_session, client=client_a, name="Сайт")

        fetched = await ProjectRepository(db_session).get_by_client_and_name(client_b.id, "Сайт")

        assert fetched is None


class TestAdd:
    async def test_persists_project(self, db_session) -> None:
        from app.models import Project

        client = await create_client(db_session)
        repo = ProjectRepository(db_session)
        project = Project(client_id=client.id, name="Новый проект", status=ProjectStatus.ACTIVE)

        await repo.add(project)

        fetched = await repo.get(project.id)
        assert fetched is not None
        assert fetched.name == "Новый проект"


class TestUpdateStatus:
    async def test_changes_status(self, db_session) -> None:
        client = await create_client(db_session)
        project = await create_project(db_session, client=client, status=ProjectStatus.ACTIVE)
        repo = ProjectRepository(db_session)

        await repo.update_status(project, ProjectStatus.ON_HOLD)

        fetched = await repo.get(project.id)
        assert fetched is not None
        assert fetched.status is ProjectStatus.ON_HOLD
