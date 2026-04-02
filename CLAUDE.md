# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Fitbox** is a fitness/boxing training management platform. It provides a REST API for managing users, bookings, slots, records, transactions, and communicates with physical sensor/training devices over MQTT.

## Commands

### Running the Application

```bash
# Full stack via Docker Compose
cd ci/ && docker-compose up

# Local development
cd src
alembic upgrade head          # Run DB migrations first
python run.py                 # Default: port 8800, log_level=debug
python run.py -p 8850 -ll info
```

### Running Tests

```bash
cd src
pytest -q tests/
pytest tests/sensors/test_state.py        # Run a single test file
pytest tests/sensors/test_state.py::test_foo  # Run a single test
```

### Linting and Formatting

```bash
poetry run blue src/     # Code formatter
poetry run isort src/    # Import sorting
```

### Database Migrations

```bash
cd src
alembic upgrade head                      # Apply all migrations
alembic revision --autogenerate -m "msg"  # Create new migration
```

## Architecture

### Entry Points

- `src/run.py` — Uvicorn runner; creates the FastAPI app and starts the server
- `src/app.py` — `create_app()` factory: registers all routers, middleware, static files, startup/shutdown lifecycle hooks
- `src/routers.py` — Aggregates all feature routers under `/api/v1`

### Feature Module Layout

Each domain area under `src/web/{feature}/` follows the same pattern:

| File | Purpose |
|------|---------|
| `routers.py` | FastAPI `APIRouter` — endpoints and dependency injection |
| `schemas.py` | Pydantic request/response models |
| `services.py` | Business logic and database operations |
| `filters.py` | (optional) fastapi-filter definitions for list endpoints |

Features: `auth`, `users`, `bookings`, `slots`, `records`, `transactions`, `sensors`.

### Database (`src/database/`)

- `orm.py` — Async SQLAlchemy engine, session factory, and `BaseModel`
- `models/` — ORM models: `User`, `Booking`, `Slot`, `Record`, `Sprint`, `Transaction`
- `migrations/` — Alembic migrations

All models use UUID PKs and timezone-aware datetimes. The `User` model extends `SQLAlchemyBaseUserTableUUID` from fastapi-users.

### Dependency Injection (`src/dependencies.py`)

Shared FastAPI dependencies injected into routers:

- `get_db_session()` — yields `AsyncSession` with rollback on error
- `get_state()` — returns `SensorsState` from `app.state`
- `get_mqtt()` — returns MQTT client from `app.state`
- `get_cache()` — returns Redis cache wrapper from `app.state`

### Sensor / MQTT Integration

- On startup, the app connects to the MQTT broker and subscribes to `fitbox/ping`
- Incoming pings update `SensorsState` (`src/state.py`) with device IP and last-seen timestamp
- A background janitor task runs every 10 seconds to mark inactive / delete stale devices
- `SensorsState` tracks device connectivity and enforces IP mismatch policies (quarantine/update/drop)

### Authentication

- JWT-based via fastapi-users; access token TTL = 1 hour, refresh token TTL = 14 days
- Custom `UserManager` in `src/web/users/`
- Key dependencies: `current_user`, `current_superuser`

### Configuration (`src/settings.py`)

All configuration comes from environment variables. Key vars:

```
POSTGRES_USER, POSTGRES_PASSWORD, DB_HOST, DB_PORT, POSTGRES_DB
SECRET_KEY
MQTT_BROKER, MQTT_PORT
REDIS_URL
BASE_URL, SERVER_HOSTNAME
SUPERUSER_EMAIL, SUPERUSER_PASSWORD, SUPERUSER_NAME, SUPERUSER_LAST_NAME
```

### Caching

`src/core/simple_cache.py` wraps Redis with TTL support. The cache instance lives on `app.state.cache` and is injected via `get_cache()`.

### Monitoring

Prometheus metrics are exposed at `/metrics` (requires HTTP basic auth). Instrumentation is set up in `src/monitoring/instumentator.py`.

## Key Notes

- `PYTHONPATH` must include `src/` (set automatically in Docker; set manually for local dev)
- Tests use `pytest-asyncio` in `auto` mode — all async tests work without decorators
- The `ci/` directory contains Docker Compose, Dockerfile, and Jenkins pipeline configs — not application source
- `src/scripts/` has utility scripts: `create_user.py` (initial superuser) and `excel_to_hits.py` (data import)