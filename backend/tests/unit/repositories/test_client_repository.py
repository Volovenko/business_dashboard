from __future__ import annotations

import uuid
from decimal import Decimal

from app.repositories.client import ClientAggregateRow, ClientRepository
from tests.factories import create_client, create_payment, create_project
from tests.sql_counter import count_queries


class TestGet:
    async def test_returns_client_by_id(self, db_session) -> None:
        client = await create_client(db_session)
        repo = ClientRepository(db_session)

        fetched = await repo.get(client.id)

        assert fetched is not None
        assert fetched.id == client.id

    async def test_returns_none_when_missing(self, db_session) -> None:
        repo = ClientRepository(db_session)

        assert await repo.get(uuid.uuid4()) is None


class TestGetByInn:
    async def test_returns_client_by_inn(self, db_session) -> None:
        client = await create_client(db_session, inn="1234567890")
        repo = ClientRepository(db_session)

        fetched = await repo.get_by_inn("1234567890")

        assert fetched is not None
        assert fetched.id == client.id

    async def test_returns_none_for_unknown_inn(self, db_session) -> None:
        repo = ClientRepository(db_session)

        assert await repo.get_by_inn("0000000000") is None


class TestListWithAggregates:
    async def test_returns_empty_when_no_clients(self, db_session) -> None:
        repo = ClientRepository(db_session)

        assert await repo.list_with_aggregates() == []

    async def test_zero_aggregates_for_client_without_projects(self, db_session) -> None:
        client = await create_client(db_session)
        repo = ClientRepository(db_session)

        rows = await repo.list_with_aggregates()

        assert rows == [
            ClientAggregateRow(
                client=client,
                project_count=0,
                payment_count=0,
                total_amount=Decimal("0"),
            )
        ]

    async def test_aggregates_projects_and_payments(self, db_session) -> None:
        client = await create_client(db_session)
        project_a = await create_project(db_session, client=client)
        project_b = await create_project(db_session, client=client)
        await create_payment(db_session, client=client, project=project_a, amount=Decimal("1000.50"))
        await create_payment(db_session, client=client, project=project_a, amount=Decimal("2000.00"))
        await create_payment(db_session, client=client, project=project_b, amount=Decimal("500.25"))

        rows = await ClientRepository(db_session).list_with_aggregates()

        assert len(rows) == 1
        row = rows[0]
        assert row.client.id == client.id
        assert row.project_count == 2
        assert row.payment_count == 3
        assert row.total_amount == Decimal("3500.75")

    async def test_aggregates_are_per_client_not_cross_polluted(self, db_session) -> None:
        client_a = await create_client(db_session, name="Альфа")
        client_b = await create_client(db_session, name="Бета")
        project_a = await create_project(db_session, client=client_a)
        project_b = await create_project(db_session, client=client_b)
        await create_payment(db_session, client=client_a, project=project_a, amount=Decimal("100"))
        await create_payment(db_session, client=client_b, project=project_b, amount=Decimal("200"))
        await create_payment(db_session, client=client_b, project=project_b, amount=Decimal("300"))

        rows = {r.client.id: r for r in await ClientRepository(db_session).list_with_aggregates()}

        assert rows[client_a.id].payment_count == 1
        assert rows[client_a.id].total_amount == Decimal("100")
        assert rows[client_b.id].payment_count == 2
        assert rows[client_b.id].total_amount == Decimal("500")

    async def test_list_runs_in_constant_number_of_queries(self, db_session, engine) -> None:
        # Five clients, each with two projects and two payments — exactly one
        # SELECT should fan out the aggregates.
        for _ in range(5):
            client = await create_client(db_session)
            for _ in range(2):
                project = await create_project(db_session, client=client)
                await create_payment(db_session, client=client, project=project)
                await create_payment(db_session, client=client, project=project)
        await db_session.flush()

        with count_queries(engine) as queries:
            rows = await ClientRepository(db_session).list_with_aggregates()

        assert len(rows) == 5
        assert len(queries) == 1, f"expected 1 query, got {len(queries)}: {queries}"


class TestGetWithProjects:
    async def test_eager_loads_projects_in_two_queries(self, db_session, engine) -> None:
        client = await create_client(db_session)
        await create_project(db_session, client=client)
        await create_project(db_session, client=client)
        await db_session.flush()

        with count_queries(engine) as queries:
            fetched = await ClientRepository(db_session).get_with_projects(client.id)

        assert fetched is not None
        assert len(fetched.projects) == 2
        # one SELECT for client + one SELECT-IN for projects (selectinload)
        assert len(queries) == 2, queries

    async def test_returns_none_when_missing(self, db_session) -> None:
        assert await ClientRepository(db_session).get_with_projects(uuid.uuid4()) is None


class TestAdd:
    async def test_persists_client(self, db_session) -> None:
        from app.models import Client

        repo = ClientRepository(db_session)
        client = Client(name="ООО Новый", inn="9876543210")

        await repo.add(client)

        fetched = await repo.get_by_inn("9876543210")
        assert fetched is not None
        assert fetched.name == "ООО Новый"
