# Business Dashboard

Дашборд для digital-агентства

---

## Быстрый старт

**Требования:** Docker + Docker Compose.
```bash
git clone <repo>
cd business_dashboard
docker compose up --build
```

После сборки:

| Сервис   | Адрес                       | Что внутри                              |
|----------|-----------------------------|-----------------------------------------|
| Frontend | http://localhost:5173       | Vue 3 + Vite, hot-reload                |
| Backend  | http://localhost:8000       | FastAPI + uvicorn, hot-reload           |
| API docs | http://localhost:8000/docs  | Swagger UI (автогенерация)              |
| Postgres | localhost:5432              | PostgreSQL 16, данные в docker volume   |

Миграции накатываются автоматически при старте backend-контейнера (`alembic upgrade head`).

### Загрузить демо-данные

```bash
docker compose run --rm backend python -m app.seed
```

Создаёт 19 клиентов, 24 проекта, 24 платежа с датами **относительно сегодня**,
покрывая все четыре статуса актов:

| Статус               | Кол-во | Ситуация                                        |
|----------------------|--------|-------------------------------------------------|
| `closed`             | 7      | Платёж 68–75 дней назад, акт отправлен и подписан |
| `attention`          | 6      | Платёж 38–45 дней назад, акт не отправлен — просрочен |
| `waiting_signature`  | 5      | Платёж 18–22 дня назад, акт отправлен клиенту  |
| `not_sent`           | 6      | Платёж 2–6 дней назад, акт ещё не трогали      |

---

## Тесты

```bash
docker compose run --rm backend pytest
```

180 тестов на отдельной БД `dashboard_test` (создаётся/мигрируется один раз за
сессию, каждый тест изолирован через SAVEPOINT + rollback):

| Группа | Что покрыто |
|--------|-------------|
| Unit / сервисы | Логика статусов акта (4 сценария), агрегация статуса проекта, UpdateActService, SummaryService |
| Unit / репозитории | Фильтрация платежей по 7 параметрам, агрегаты клиентов и проектов (нет N+1) |
| Unit / импорт | PDF-парсер, фильтр операций, классификатор услуг, экстрактор номеров счетов, маппер, end-to-end на реальном PDF (24 платежа) |
| API | 26 тестов через httpx AsyncClient: все эндпоинты, фильтры, коды ошибок, изменение статусов актов |

---

## Импорт выписки через UI

1. Открыть **Сводка** → кнопка «Загрузить выписку»
2. Выбрать PDF-файл АО «ФИН-МОСТ БАНК»
3. Проверить список разобранных платежей в превью
4. Нажать «Сохранить в БД» — создадутся клиенты, проекты, платежи и акты

Импорт двухфазный: сначала preview (без записи в БД), затем commit по подтверждению.

---

## Что реализовано по ТЗ

### Бэкенд

- **Модели:** `Client`, `Project`, `Payment`, `Act` — PostgreSQL 16, UUID PK, все связи
- **Статус акта** вычисляется чистой функцией по правилам:
  - `is_signed` → `closed`
  - не closed + платёж старше 30 дней → `attention`
  - `is_sent` → `waiting_signature`
  - иначе → `not_sent`
- **Статус проекта** агрегируется из актов: все closed → `completed`, есть attention → `attention`, иначе → `active`; `on_hold` автоматически не перезаписывается
- **Импорт PDF** (формат АО «ФИН-МОСТ БАНК»): pdfplumber, regex, фильтрация банковских и собственных операций, классификация услуги по ключевым словам, извлечение номера счёта с учётом падежей
- **API:** `GET /api/clients`, `GET /api/clients/{id}`, `GET /api/projects`, `GET /api/projects/{id}`, `GET /api/payments` (7 фильтров), `PATCH /api/acts/{id}`, `GET /api/summary`, `POST /api/import/preview`, `POST /api/import/commit`

### Фронтенд

- **Сводка:** 7 KPI-карточек (суммы, счётчики актов по статусам) + кнопка импорта
- **Платежи:** таблица со всеми 7 фильтрами (поиск, даты, статус акта, тип услуги), кнопки «Отправить акт» / «Подписан» прямо в строке
- **Проекты:** список с агрегатами
- **Клиенты:** список с агрегатами

---

## Что сделано сверх ТЗ

| Фича | Описание |
|------|----------|
| **Детальная страница клиента** | `/clients/:id` — реквизиты + список проектов, каждый проект кликабелен |
| **Детальная страница проекта** | `/projects/:id` — платежи с управлением актами, итог (всего / закрыто / открыто), для статуса `attention` отображается сколько дней просрочено |
| **Кликабельные строки таблиц** | В списках клиентов и проектов любая строка ведёт на детальную страницу |
| **Two-phase import** | Preview без записи в БД → пользователь видит и проверяет данные до сохранения |
| **Seed-скрипт** | `python -m app.seed` — демо-данные с относительными датами, все 4 статуса всегда актуальны |
| **Полный API-тест слой** | 26 тестов через `httpx.AsyncClient` с реальным Postgres и dependency override |

---

## Архитектура бэкенда

```
backend/app/
├── api/                  роутеры — только HTTP: валидация, вызов сервиса, commit
│   ├── deps.py           DI-граф: Session → Repo → Service (Annotated + Depends)
│   ├── errors.py         маппинг DomainError → HTTP-статус (404 / 422 / 400)
│   ├── clients.py
│   ├── projects.py
│   ├── payments.py
│   ├── acts.py
│   ├── summary.py
│   └── import_statement.py
├── services/
│   ├── act_status_service.py      чистая функция, нет I/O, легко тестировать
│   ├── project_status_service.py  агрегация статусов актов
│   ├── summary_service.py         тонкая обёртка над репозиторием
│   ├── update_act_service.py      оркестрация: merge → timestamp → recompute → save
│   └── import_statement/
│       ├── parser.py              pdfplumber → RawOperation[]
│       ├── filter.py              фильтр входящих операций
│       ├── classifier.py          keyword-матч → тип услуги
│       ├── invoice_extractor.py   regex с падежами → номер счёта
│       ├── mapper.py              RawOperation → ParsedPayment[]
│       └── service.py             preview() / commit()
├── repositories/         AsyncSession, selectinload/joinedload, нет N+1
├── schemas/              Pydantic v2: APIModel (from_attributes) / WriteModel (extra=forbid)
├── models/               SQLAlchemy 2.0, Mapped[], native_enum
└── core/                 Settings (pydantic-settings), engine/session, исключения
```

