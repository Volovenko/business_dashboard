from __future__ import annotations

from decimal import Decimal

from app.models import ActStatus
from app.repositories.summary import SummaryRepository, SummaryRow
from tests.factories import create_act, create_client, create_payment, create_project
from tests.sql_counter import count_queries


class TestSnapshot:
    async def test_returns_zeros_on_empty_database(self, db_session) -> None:
        snapshot = await SummaryRepository(db_session).snapshot()

        assert snapshot == SummaryRow(
            total_amount=Decimal("0"),
            total_projects=0,
            total_payments=0,
            closed_amount=Decimal("0"),
            open_amount=Decimal("0"),
            acts_not_sent=0,
            acts_waiting_signature=0,
        )

    async def test_counts_projects_payments_and_amounts(self, db_session) -> None:
        client = await create_client(db_session)
        project_a = await create_project(db_session, client=client)
        project_b = await create_project(db_session, client=client)
        p1 = await create_payment(db_session, client=client, project=project_a, amount=Decimal("100"))
        p2 = await create_payment(db_session, client=client, project=project_a, amount=Decimal("250"))
        p3 = await create_payment(db_session, client=client, project=project_b, amount=Decimal("700"))
        await create_act(db_session, payment=p1, status=ActStatus.CLOSED, is_sent=True, is_signed=True)
        await create_act(db_session, payment=p2, status=ActStatus.WAITING_SIGNATURE, is_sent=True)
        await create_act(db_session, payment=p3, status=ActStatus.NOT_SENT)

        snapshot = await SummaryRepository(db_session).snapshot()

        assert snapshot.total_projects == 2
        assert snapshot.total_payments == 3
        assert snapshot.total_amount == Decimal("1050")
        assert snapshot.closed_amount == Decimal("100")
        assert snapshot.open_amount == Decimal("950")
        assert snapshot.acts_not_sent == 1
        assert snapshot.acts_waiting_signature == 1

    async def test_payment_without_act_counts_as_open(self, db_session) -> None:
        client = await create_client(db_session)
        project = await create_project(db_session, client=client)
        await create_payment(db_session, client=client, project=project, amount=Decimal("500"))

        snapshot = await SummaryRepository(db_session).snapshot()

        assert snapshot.total_payments == 1
        assert snapshot.closed_amount == Decimal("0")
        assert snapshot.open_amount == Decimal("500")
        assert snapshot.acts_not_sent == 0

    async def test_attention_act_counted_as_open_not_in_other_buckets(self, db_session) -> None:
        client = await create_client(db_session)
        project = await create_project(db_session, client=client)
        payment = await create_payment(db_session, client=client, project=project, amount=Decimal("400"))
        await create_act(db_session, payment=payment, status=ActStatus.ATTENTION)

        snapshot = await SummaryRepository(db_session).snapshot()

        assert snapshot.acts_not_sent == 0
        assert snapshot.acts_waiting_signature == 0
        assert snapshot.closed_amount == Decimal("0")
        assert snapshot.open_amount == Decimal("400")

    async def test_runs_in_constant_number_of_queries(self, db_session, engine) -> None:
        for _ in range(6):
            client = await create_client(db_session)
            project = await create_project(db_session, client=client)
            for _ in range(3):
                payment = await create_payment(db_session, client=client, project=project)
                await create_act(db_session, payment=payment)
        await db_session.flush()

        with count_queries(engine) as queries:
            await SummaryRepository(db_session).snapshot()

        # A single round-trip is enough; we don't want O(clients) round-trips.
        assert len(queries) <= 2, queries
