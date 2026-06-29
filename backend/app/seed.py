"""Seed the database with demo data derived from the real bank statement.

Dates are set relative to today so all four act statuses are represented:
  - closed            : paid 75 days ago, акт отправлен и подписан
  - attention         : paid 45 days ago, акт не отправлен (просрочен)
  - waiting_signature : paid 20 days ago, акт отправлен, не подписан
  - not_sent          : paid 5 days ago, акт ещё не отправлен

Run:
    docker compose run --rm backend python -m app.seed
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import build_engine, build_session_factory
from app.core.config import get_settings
from app.models import Act, ActStatus, Client, Payment, Project, ProjectStatus
from app.services.act_status_service import ActStatusService
from app.services.project_status_service import ProjectStatusService


def _days_ago(n: int) -> date:
    return date.today() - timedelta(days=n)


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass
class _PaymentSpec:
    amount: Decimal
    service_type: str
    payment_purpose: str
    days_ago: int
    is_sent: bool
    is_signed: bool
    invoice_number: str | None = None
    doc_number: str = "000"


@dataclass
class _ClientSpec:
    name: str
    inn: str
    payments: list[_PaymentSpec]


SEED_DATA: list[_ClientSpec] = [
    _ClientSpec("ООО «ПЛАТФОРМА-ЛК»", "9707142689", [
        _PaymentSpec(Decimal("266000"), "разработка",
                     "Оплата по сч. №801 за разработку личного кабинета", 75, True, True, "801", "П-801"),
    ]),
    _ClientSpec("АНО «СВЕТЛЫЙ КВАРТАЛ»", "7810291634", [
        _PaymentSpec(Decimal("77200"),  "SEO",
                     "Оплата по сч. №762 за продвижение SEO", 75, True, True, "762", "П-762"),
        _PaymentSpec(Decimal("86000"),  "лендинг",
                     "Оплата по сч. №791 за разработку лендинга", 68, True, True, "791", "П-791"),
    ]),
    _ClientSpec("ООО «ГРАНИТ-СИСТЕМ»", "7819420657", [
        _PaymentSpec(Decimal("60500"),  "разработка",
                     "Оплата по сч. №738 за разработку сайта", 75, True, True, "738", "П-738"),
    ]),
    _ClientSpec("ИП Федотов Р.Н.", "590214785306", [
        _PaymentSpec(Decimal("66600"),  "SEO",
                     "Оплата по сч. №771 за SEO-продвижение", 70, True, True, "771", "П-771"),
    ]),
    _ClientSpec("ООО «СТАЛЬСНАБ-РЕСУРС»", "5047192865", [
        _PaymentSpec(Decimal("107500"), "маркетинг",
                     "Оплата по сч. №744 за маркетинговое сопровождение", 72, True, True, "744", "П-744"),
    ]),
    _ClientSpec("ООО «ВЕРТИКАЛЬ МОДУЛЬ»", "7720195384", [
        _PaymentSpec(Decimal("82400"),  "дизайн",
                     "Оплата по сч. №783 дизайн финальный этап", 68, True, True, "783", "П-783"),
    ]),

    _ClientSpec("ООО «СИГМА-МАРКЕТ»", "7725136498", [
        _PaymentSpec(Decimal("54400"),  "объявления",
                     "Оплата по сч. №742 размещение объявлений эт.1", 45, False, False, "742", "П-742"),
        _PaymentSpec(Decimal("56300"),  "контекст",
                     "Оплата по сч. №756 контекстная реклама эт.1", 42, False, False, "756", "П-756"),
    ]),
    _ClientSpec("ООО «ОБЛАКО-ИМИДЖ»", "5031198742", [
        _PaymentSpec(Decimal("19800"),  "SERM",
                     "Оплата по сч. №731 за SERM-сопровождение", 45, False, False, "731", "П-731"),
        _PaymentSpec(Decimal("47000"),  "контекст",
                     "Оплата по сч. №749 контекстная реклама", 40, False, False, "749", "П-749"),
    ]),
    _ClientSpec("ИП Косарева Д.А.", "500914637205", [
        _PaymentSpec(Decimal("64800"),  "SMM",
                     "Оплата по сч. №768 за SMM-продвижение", 43, False, False, "768", "П-768"),
    ]),
    _ClientSpec("АО «ТЕРМИНАЛ СЕВЕРНЫЙ»", "7815082904", [
        _PaymentSpec(Decimal("45500"),  "сопровождение",
                     "Оплата по сч. №739 сопровождение сайта", 38, False, False, "739", "П-739"),
    ]),

    _ClientSpec("ООО «ОРБИТА-ПРОМО»", "7706412805", [
        _PaymentSpec(Decimal("36400"),  "Директ",
                     "Оплата по сч. №774 Яндекс.Директ", 20, True, False, "774", "П-774"),
        _PaymentSpec(Decimal("27600"),  "тексты",
                     "Оплата по сч. №779 тексты и копирайт", 18, True, False, "779", "П-779"),
    ]),
    _ClientSpec("ООО «ЭКОПРАВО-КОНСАЛТ»", "7728619405", [
        _PaymentSpec(Decimal("58200"),  "прочее",
                     "Оплата по сч. №793 проектирование и копирайтинг", 22, True, False, "793", "П-793"),
    ]),
    _ClientSpec("ИП Орлов Д.Р.", "504218730629", [
        _PaymentSpec(Decimal("69000"),  "сопровождение",
                     "Оплата по сч. №786 сопровождение и наполнение", 19, True, False, "786", "П-786"),
    ]),
    _ClientSpec("ИП Соколова Н.А.", "773019284607", [
        _PaymentSpec(Decimal("32400"),  "прочее",
                     "Оплата по сч. №771 реклама в соц.сетях", 21, True, False, "771", "П-771b"),
    ]),

    _ClientSpec("ООО «ЛЕДНИК-СТАРТ»", "5408124976", [
        _PaymentSpec(Decimal("33000"),  "сопровождение",
                     "Оплата по сч. №802 техническое сопровождение", 5, False, False, "802", "П-802"),
        _PaymentSpec(Decimal("1830"),   "лицензия",
                     "Оплата по сч. №803 лицензия ПО", 5, False, False, "803", "П-803"),
    ]),
    _ClientSpec("ООО «ВЕКТОР-ТУР»", "7813492063", [
        _PaymentSpec(Decimal("8190"),   "публикация",
                     "Оплата по сч. №804 публикация материалов", 3, False, False, "804", "П-804"),
    ]),
    _ClientSpec("ООО «ИНЖЕНЕРНЫЙ КОНТУР»", "6679083142", [
        _PaymentSpec(Decimal("45000"),  "прочее",
                     "Оплата по сч. №739 за услуги", 4, False, False, "739", "П-739b"),
    ]),
    _ClientSpec("ООО «ЛАЙНЕР-АВТО»", "5409207165", [
        _PaymentSpec(Decimal("18200"),  "прочее",
                     "Оплата по сч. №768 за услуги", 6, False, False, "768", "П-768b"),
    ]),
    _ClientSpec("ООО «ПРЕЗЕНТАРИУМ»", "7813560472", [
        _PaymentSpec(Decimal("42000"),  "презентация",
                     "Оплата по сч. №792 презентация аванс", 2, False, False, "792", "П-792"),
    ]),
]


async def _clear(session: AsyncSession) -> None:
    # Cascade handles FK order automatically.
    await session.execute(text("TRUNCATE acts, payments, projects, clients RESTART IDENTITY CASCADE"))
    await session.commit()
    print("✓ Таблицы очищены")


async def _seed(session: AsyncSession, threshold_days: int) -> None:
    today = date.today()
    now = _now()
    totals = {"clients": 0, "projects": 0, "payments": 0, "acts": 0}

    for cspec in SEED_DATA:
        client = Client(name=cspec.name, inn=cspec.inn)
        session.add(client)
        await session.flush()
        totals["clients"] += 1

        by_service: dict[str, list[_PaymentSpec]] = {}
        for pspec in cspec.payments:
            by_service.setdefault(pspec.service_type, []).append(pspec)

        for service_type, pspecs in by_service.items():
            project_name = f"{cspec.name} — {service_type}"
            project = Project(client_id=client.id, name=project_name)
            session.add(project)
            await session.flush()
            totals["projects"] += 1

            act_statuses: list[ActStatus] = []

            for pspec in pspecs:
                payment_date = _days_ago(pspec.days_ago)
                payment = Payment(
                    client_id=client.id,
                    project_id=project.id,
                    payment_date=payment_date,
                    amount=pspec.amount,
                    payment_purpose=pspec.payment_purpose,
                    service_type=pspec.service_type,
                    invoice_number=pspec.invoice_number,
                    doc_number=pspec.doc_number,
                )
                session.add(payment)
                await session.flush()
                totals["payments"] += 1

                status = ActStatusService.compute(
                    is_sent=pspec.is_sent,
                    is_signed=pspec.is_signed,
                    payment_date=payment_date,
                    today=today,
                    threshold_days=threshold_days,
                )
                act = Act(
                    payment_id=payment.id,
                    is_sent=pspec.is_sent,
                    is_signed=pspec.is_signed,
                    sent_at=now if pspec.is_sent else None,
                    signed_at=now if pspec.is_signed else None,
                    status=status,
                )
                session.add(act)
                await session.flush()
                totals["acts"] += 1
                act_statuses.append(status)

            project_status = ProjectStatusService.aggregate(
                current_status=project.status,
                act_statuses=act_statuses,
            )
            project.status = project_status

        await session.flush()

    await session.commit()

    print(f"✓ Создано: {totals['clients']} клиентов, {totals['projects']} проектов, "
          f"{totals['payments']} платежей, {totals['acts']} актов")


async def main() -> None:
    settings = get_settings()
    engine = build_engine(settings.database_url)
    factory = build_session_factory(engine)

    async with factory() as session:
        await _clear(session)
        await _seed(session, threshold_days=settings.attention_threshold_days)

    await engine.dispose()

    status_counts: dict[str, int] = {}
    for cspec in SEED_DATA:
        for pspec in cspec.payments:
            payment_date = _days_ago(pspec.days_ago)
            status = ActStatusService.compute(
                is_sent=pspec.is_sent,
                is_signed=pspec.is_signed,
                payment_date=payment_date,
                today=date.today(),
                threshold_days=settings.attention_threshold_days,
            )
            status_counts[status.value] = status_counts.get(status.value, 0) + 1

    print("\nСтатусы актов:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")


if __name__ == "__main__":
    asyncio.run(main())
