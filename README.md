# FastAPI Blueprint

A production-ready FastAPI starter template with async SQLAlchemy, JWT auth, RBAC, pagination, filtering, seeder system, command scheduler, and full test coverage.

Copy this repo to start a new project — everything is wired up. Add models, delete what you don't need.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Runtime | Python 3.12 |
| Framework | FastAPI |
| ORM | SQLAlchemy (async) |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Auth | python-jose + bcrypt |
| DB (production) | MySQL via aiomysql |
| DB (tests) | SQLite via aiosqlite |
| Testing | pytest + pytest-asyncio + httpx + faker |
| Scheduling | croniter (cron expression matching) |

---

## What's Included

### Core infrastructure

| Package | What it does |
|---------|-------------|
| `app/core/config.py` | Pydantic-settings — reads `.env`, typed settings object |
| `app/core/exceptions.py` | Domain exception hierarchy (`NotFoundError`, `ConflictError`, `AuthenticationError`, `InactiveAccountError`) |
| `app/core/exception_handler.py` | Translates domain exceptions → consistent JSON envelope |
| `app/core/response.py` | `ok()`, `created()`, `no_content()` — uniform response helpers |
| `app/core/security.py` | JWT access + refresh tokens, bcrypt password hashing |
| `app/core/permissions.py` | RBAC engine + FastAPI dependency factories |
| `app/core/dependencies.py` | `get_current_user`, service dependency factories |
| `app/core/logging.py` | Structured console + syslog logging |
| `app/core/middleware.py` | `RequestLoggingMiddleware` — logs every request with UUID and duration |
| `app/db/session.py` | Async engine, session factory, `get_db` dependency |
| `app/db/pagination.py` | `PaginationParams`, `Page[T]`, `paginate()` |
| `app/filters/base.py` | `BaseFilter` — composable query-param filtering + sorting |

### Domain (RBAC — users / roles / permissions)

The built-in domain is a complete, production-tested RBAC system. Use it as-is or as a reference when building your own domain.

| Layer | Files |
|-------|-------|
| Models | `app/models/user.py`, `role.py`, `permission.py` |
| Repositories | `app/repositories/user_repository.py`, `role_repository.py`, `permission_repository.py` |
| Services | `app/services/user_service.py`, `role_service.py`, `permission_service.py` |
| Schemas | `app/schemas/admin/`, `app/schemas/client/`, `app/schemas/shared/` |
| Routers | `app/api/v1/routers/admin/`, `app/api/v1/routers/client/` |
| Filters | `app/filters/user_filter.py`, `role_filter.py`, `permission_filter.py` |

### Supporting systems

| System | Location | Docs |
|--------|----------|------|
| Seeder system | `app/seeders/` | See [Seeder System](#seeder-system) below |
| Command scheduler | `app/commands/` | See [Command Scheduler](#command-scheduler) below |
| Test infrastructure | `app/tests/` | See [Tests](#tests) below |
| Docker setup | `docker/`, `docker-compose.yml` | See [Docker](#docker) below |

---

## Starting a New Project from This Blueprint

```bash
# 1. Copy to your new project directory
cp -r /path/to/fastapi-blueprint /path/to/my-new-project
cd /path/to/my-new-project

# 2. Init a new git repo
git init && git add . && git commit -m "init: from fastapi-blueprint"

# 3. Create your .env
cp .env.example .env
# Set DATABASE_URL, SECRET_KEY (min 32 chars), APP_NAME

# 4. Install dependencies
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt

# 5. Run migrations and seed
alembic upgrade head
python seed.py

# 6. Start the server
python run.py
```

Or use Docker — see [Docker](#docker) below.

---

## Quick Start (Docker)

```bash
cp .env.example .env        # set SECRET_KEY
docker compose up --build   # app at http://localhost:8000
```

Default admin credentials: `admin@example.com` / `Admin1234` (change immediately in production).

---

## Configuration

All settings live in `app/core/config.py` and are read from `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `MyApp` | Application name shown in Swagger |
| `DATABASE_URL` | — | Async MySQL connection string |
| `SECRET_KEY` | — | JWT signing key — min 32 random characters |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `PRODUCTION` | `false` | Disables `/docs`, `/redoc`, `/health` when `true` |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `SEED_ADMIN_EMAIL` | `admin@example.com` | Override before first `seed.py` run |
| `SEED_ADMIN_PASSWORD` | `Admin1234` | Override before first `seed.py` run |

---

## Response Envelope

Every response uses the same JSON envelope:

```json
{ "success": true,  "code": 200, "message": "Ok",      "data":  { ... } }
{ "success": true,  "code": 201, "message": "Created",  "data":  { ... } }
{ "success": false, "code": 404, "message": "Not Found","error": { "detail": "..." } }
{ "success": false, "code": 422, "message": "Validation Exception", "error": { "field": ["msg"] } }
```

Use the helpers in every route — never return raw dicts or Pydantic models:

```python
from app.core.response import ok, created, no_content

return ok(MySchema.model_validate(obj))
return created(MySchema.model_validate(obj))
return no_content()
```

---

## RBAC

A user holds a permission if any of their assigned **roles** has it, or it is **directly assigned** to the user.

### Protecting routes

```python
from app.core.permissions import require_permission, require_any_permission

@router.get("/items", dependencies=[Depends(require_permission("items.read"))])
@router.delete("/items/{id}", dependencies=[Depends(require_any_permission("items.delete", "admin.all"))])
```

### Checking inside a handler

```python
from app.core.permissions import can

async def my_handler(user: User = Depends(get_current_user)):
    if not can(user, "orders.refund"):
        raise PermissionDeniedError()
```

### Permission helpers

```python
get_all_permissions(user)        # → set[str]
can(user, "perm")                # bool
can_any(user, "p1", "p2")       # bool — OR
can_all(user, "p1", "p2")       # bool — AND
has_role(user, "name")           # bool
has_any_role(user, "a", "b")    # bool
```

---

## Adding a New Domain Resource

1. **Model** — `app/models/your_model.py`, register in `app/models/__init__.py`
2. **Migration** — `alembic revision --autogenerate -m "add your_model"`, then `alembic upgrade head`
3. **Repository** — `app/repositories/your_repository.py` extending `BaseRepository[YourModel]`
4. **Service** — `app/services/your_service.py` extending `BaseService[YourModel]`
5. **Schemas** — `app/schemas/your_model.py`
6. **Filter** — `app/filters/your_filter.py` extending `BaseFilter` + `YourFilterParams`
7. **Router** — `app/api/v1/routers/your_router.py`, include in `app/api/v1/router/__init__.py`
8. **Dependency** — add `get_your_service()` to `app/core/dependencies.py`
9. **Tests** — factories + test files under `app/tests/`
10. **Permissions** — add new permission names to `app/seeders/permission_seeder.py` and re-run `seed.py`

---

## Seeder System

Seeders live in `app/seeders/`. Each is a class; run all at once or one at a time.

```bash
python manage.py seed:list         # list registered seeders
python manage.py seed:run          # run all seeders (atomic transaction)
python manage.py seed:run users    # run a single seeder by name
```

### Creating a seeder

```python
# app/seeders/your_seeder.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.seeders.base import BaseSeeder

class YourSeeder(BaseSeeder):
    name = "your-seeder"
    description = "What this seeder creates"

    async def run(self, db: AsyncSession) -> None:
        pass  # idempotent DB logic
```

Register in `app/seeders/kernel.py` — append to `SEEDERS` in dependency order.

---

## Command Scheduler

Commands live in `app/commands/`. Copy `example_command.py` as a starting point.

```bash
python manage.py list                    # list all commands
python manage.py run example:run         # run a command manually
python manage.py schedule:run            # run commands due right now (cron)
```

Register in `app/commands/kernel.py`. Add a cron expression to `SCHEDULE` for automatic scheduling.

OS cron entry (runs every minute, Laravel-style):
```
* * * * * cd /path/to/project && venv/bin/python manage.py schedule:run >> /var/log/scheduler.log 2>&1
```

---

## Tests

Tests use in-memory SQLite — no MySQL, no `.env`, no Docker required.

```bash
venv/bin/pytest              # all tests
venv/bin/pytest -v           # verbose
venv/bin/pytest --tb=short   # short tracebacks
```

### Test structure

```
app/tests/
├── conftest.py                    # DB engine, fixtures, admin_headers, user_headers
├── factories/                     # Faker + uuid4 data factories (make_*, *_payload)
├── test_repositories/             # Repository layer tests
├── test_services/                 # Service layer tests
├── client/                        # Auth route tests
└── admin/                         # Admin route tests
```

### Factory pattern

```python
# DB fixture — persists to in-memory SQLite
perm = await make_permission(db_session)
role = await make_role(db_session, name="editor")

# HTTP payload dict — for route tests
resp = await client.post("/api/v1/admin/permissions", headers=admin_headers, json=permission_payload())
```

---

## Docker

```bash
cp .env.example .env            # set SECRET_KEY
docker compose up --build       # app + MySQL, auto-migrated and seeded
docker compose up -d            # background
docker compose logs -f app      # follow logs
docker compose down             # stop, preserve data
docker compose down -v          # stop, wipe data
docker compose exec app python manage.py seed:list
```

For live reload during development, uncomment the volume mount in `docker-compose.yml`:
```yaml
volumes:
  - ./app:/app/app
```

---

## Project Structure

```
fastapi-blueprint/
├── app/
│   ├── api/v1/
│   │   ├── router/          # Top-level aggregated router
│   │   └── routers/
│   │       ├── client/      # Auth / public routes
│   │       └── admin/       # Admin routes (permission-gated)
│   ├── commands/            # Scheduler commands (BaseCommand)
│   ├── seeders/             # DB seeders (BaseSeeder)
│   ├── core/                # Config, exceptions, auth, RBAC, logging, response helpers
│   ├── db/                  # Session, Base, pagination
│   ├── filters/             # BaseFilter + per-resource FilterParams
│   ├── models/              # SQLAlchemy ORM models
│   ├── repositories/        # Data access (BaseRepository)
│   ├── services/            # Business logic (BaseService)
│   ├── schemas/             # Pydantic request/response schemas
│   ├── migrations/          # Alembic env + versions/
│   └── tests/               # Full test suite
├── docker/
│   ├── Dockerfile           # Production image (cache-optimised, non-root)
│   └── entrypoint.sh        # migrate → seed → start
├── main.py                  # App factory
├── run.py                   # Uvicorn entry point
├── manage.py                # Commands + seeders CLI
├── seed.py                  # Thin seeder runner
├── docker-compose.yml
├── alembic.ini
├── pytest.ini
├── requirements.txt         # Production deps
├── requirements-dev.txt     # Dev/test deps
└── .env.example
```
