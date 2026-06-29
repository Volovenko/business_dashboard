from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from app.models import ActStatus
from app.repositories.payment import PaymentRepository
from app.schemas.payment import PaymentFilters
from tests.factories import create_act, create_client, create_payment, create_project
from tests.sql_counter import count_queries


class TestGet:
    async def test_returns_payment_by_id(self, db_session) -> None:
        client = await create_client(db_session)
        project = await create_project(db_session, client=client)
        payment = await create_payment(db_session, client=client, project=project)

        fetched = await PaymentRepository(db_session).get(payment.id)

        assert fetched is not None
        assert fetched.id == payment.id

    async def test_returns_none_when_missing(self, db_session) -> None:
        assert await PaymentRepository(db_session).get(uuid.uuid4()) is None


class TestGetWithRelations:
    async def test_eager_loads_client_project_act(self, db_session, engine) -> None:
        client = await create_client(db_session)
        project = await create_project(db_session, client=client)
        payment = await create_payment(db_session, client=client, project=project)
        await create_act(db_session, payment=payment)
        await db_session.flush()

        with count_queries(engine) as queries:
            fetched = await PaymentRepository(db_session).get_with_relations(payment.id)
            # Touch the eager-loaded attributes — should not trigger any extra SELECTs.
            assert fetched is not None
            assert fetched.client.id == client.id
            assert fetched.project.id == project.id
            assert fetched.act is not None

        # one SELECT with joinedload covers everything
        assert len(queries) == 1, queries


class TestList:
    async def _scaffold(self, db_session):
        client_a = await create_client(db_session, name="Альфа")
        client_b = await create_client(db_session, name="Бета")
        project_a = await create_project(db_session, client=client_a, name="Сайт")
        project_b = await create_project(db_session, client=client_b, name="SEO")
        p_a1 = await create_payment(
            db_session,
            client=client_a,
            project=project_a,
            payment_date=date(2026, 1, 10),
            amount=Decimal("1000"),
            service_type="разработка",
            payment_purpose="Оплата по счёту №100 за разработку",
        )
        p_a2 = await create_payment(
            db_session,
            client=client_a,
            project=project_a,
            payment_date=date(2026, 2, 15),
            amount=Decimal("2000"),
            service_type="разработка",
            payment_purpose="Аванс по счёту №101",
        )
        p_b1 = await create_payment(
            db_session,
            client=client_b,
            project=project_b,
            payment_date=date(2026, 3, 5),
            amount=Decimal("500"),
            service_type="SEO",
            payment_purpose="SEO-продвижение",
        )
        await create_act(db_session, payment=p_a1, status=ActStatus.CLOSED, is_sent=True, is_signed=True)
        await create_act(db_session, payment=p_a2, status=ActStatus.WAITING_SIGNATURE, is_sent=True)
        await create_act(db_session, payment=p_b1, status=ActStatus.NOT_SENT)
        return client_a, client_b, project_a, project_b, p_a1, p_a2, p_b1

    async def test_returns_all_payments_without_filters(self, db_session) -> None:
        await self._scaffold(db_session)

        rows = await PaymentRepository(db_session).list(PaymentFilters())

        assert len(rows) == 3

    async def test_orders_by_payment_date_desc(self, db_session) -> None:
        _, _, _, _, p_a1, p_a2, p_b1 = await self._scaffold(db_session)

        rows = await PaymentRepository(db_session).list(PaymentFilters())

        assert [r.id for r in rows] == [p_b1.id, p_a2.id, p_a1.id]

    async def test_filter_by_client(self, db_session) -> None:
        client_a, _, _, _, p_a1, p_a2, _ = await self._scaffold(db_session)

        rows = await PaymentRepository(db_session).list(PaymentFilters(client_id=client_a.id))

        assert {r.id for r in rows} == {p_a1.id, p_a2.id}

    async def test_filter_by_project(self, db_session) -> None:
        _, _, _, project_b, _, _, p_b1 = await self._scaffold(db_session)

        rows = await PaymentRepository(db_session).list(PaymentFilters(project_id=project_b.id))

        assert [r.id for r in rows] == [p_b1.id]

    async def test_filter_by_date_from_inclusive(self, db_session) -> None:
        _, _, _, _, _, p_a2, p_b1 = await self._scaffold(db_session)

        rows = await PaymentRepository(db_session).list(PaymentFilters(date_from=date(2026, 2, 15)))

        assert {r.id for r in rows} == {p_a2.id, p_b1.id}

    async def test_filter_by_date_to_inclusive(self, db_session) -> None:
        _, _, _, _, p_a1, p_a2, _ = await self._scaffold(db_session)

        rows = await PaymentRepository(db_session).list(PaymentFilters(date_to=date(2026, 2, 15)))

        assert {r.id for r in rows} == {p_a1.id, p_a2.id}

    async def test_filter_by_date_range(self, db_session) -> None:
        _, _, _, _, _, p_a2, _ = await self._scaffold(db_session)

        rows = await PaymentRepository(db_session).list(
            PaymentFilters(date_from=date(2026, 2, 1), date_to=date(2026, 2, 28))
        )

        assert [r.id for r in rows] == [p_a2.id]

    async def test_filter_by_act_status(self, db_session) -> None:
        _, _, _, _, p_a1, _, _ = await self._scaffold(db_session)

        rows = await PaymentRepository(db_session).list(PaymentFilters(act_status=ActStatus.CLOSED))

        assert [r.id for r in rows] == [p_a1.id]

    async def test_filter_by_act_status_not_sent(self, db_session) -> None:
        _, _, _, _, _, _, p_b1 = await self._scaffold(db_session)

        rows = await PaymentRepository(db_session).list(PaymentFilters(act_status=ActStatus.NOT_SENT))

        assert [r.id for r in rows] == [p_b1.id]

    async def test_filter_by_service_type(self, db_session) -> None:
        _, _, _, _, _, _, p_b1 = await self._scaffold(db_session)

        rows = await PaymentRepository(db_session).list(PaymentFilters(service_type="SEO"))

        assert [r.id for r in rows] == [p_b1.id]

    async def test_search_matches_payment_purpose_case_insensitive(self, db_session) -> None:
        _, _, _, _, _, _, p_b1 = await self._scaffold(db_session)

        rows = await PaymentRepository(db_session).list(PaymentFilters(search="продвижен"))

        assert [r.id for r in rows] == [p_b1.id]

    async def test_search_matches_client_name(self, db_session) -> None:
        _, _, _, _, p_a1, p_a2, _ = await self._scaffold(db_session)

        rows = await PaymentRepository(db_session).list(PaymentFilters(search="Альфа"))

        assert {r.id for r in rows} == {p_a1.id, p_a2.id}

    async def test_combined_filters(self, db_session) -> None:
        client_a, _, _, _, _, p_a2, _ = await self._scaffold(db_session)

        rows = await PaymentRepository(db_session).list(
            PaymentFilters(
                client_id=client_a.id,
                date_from=date(2026, 2, 1),
                act_status=ActStatus.WAITING_SIGNATURE,
            )
        )

        assert [r.id for r in rows] == [p_a2.id]

    async def test_list_avoids_n_plus_one(self, db_session, engine) -> None:
        for _ in range(4):
            client = await create_client(db_session)
            project = await create_project(db_session, client=client)
            for _ in range(2):
                payment = await create_payment(db_session, client=client, project=project)
                await create_act(db_session, payment=payment)
        await db_session.flush()

        with count_queries(engine) as queries:
            rows = await PaymentRepository(db_session).list(PaymentFilters())
            for row in rows:
                assert row.client is not None
                assert row.project is not None
                assert row.act is not None

        assert len(rows) == 8
        assert len(queries) == 1, f"expected 1 query, got {len(queries)}: {queries}"


class TestAdd:
    async def test_persists_payment(self, db_session) -> None:
        from app.models import Payment

        client = await create_client(db_session)
        project = await create_project(db_session, client=client)
        repo = PaymentRepository(db_session)
        payment = Payment(
            client_id=client.id,
            project_id=project.id,
            payment_date=date(2026, 4, 1),
            amount=Decimal("9999"),
            payment_purpose="Тест",
            service_type="разработка",
        )

        await repo.add(payment)

        fetched = await repo.get(payment.id)
        assert fetched is not None
        assert fetched.amount == Decimal("9999")
