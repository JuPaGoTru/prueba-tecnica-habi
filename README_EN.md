# Technical Assessment — Habi: Financial Planning System

Backend REST API for personal budget management by workspace. Built with Python, FastAPI, PostgreSQL, and clean architecture.

## Requirements

- Docker and Docker Compose

## Initial Setup

```bash
# Copy the environment variables file
cp .env.example .env
```

The `.env` file included in the repo contains values for local development. In production, replace `SECRET_KEY` with a secure value.

## Running the Project

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.  
Interactive documentation: `http://localhost:8000/docs`

## Migrations

Migrations run once to create the schema:

```bash
docker compose exec backend sh -c "cd /app && alembic upgrade head"
```

## Tests

Tests run inside the container. The `TEST_DATABASE_URL` variable is read from `.env`.

```bash
# Create the test DB (first time only)
docker compose exec db psql -U habi -d habi_db -c "CREATE DATABASE habi_test;"

# Unit tests (no DB)
docker compose exec backend pytest tests/unit/ -v

# Integration tests (repositories against DB)
docker compose exec backend sh -c "cd /app && pytest tests/integration/ -v"

# E2E tests (full HTTP flow)
docker compose exec backend sh -c "cd /app && pytest tests/e2e/ -v"

# All tests
docker compose exec backend sh -c "cd /app && pytest tests/ -v"
```

## Implemented Modules

### Module 1 — JWT Authentication
- `POST /api/v1/auth/register` — User registration (returns tokens)
- `POST /api/v1/auth/login` — Login with email and password
- `POST /api/v1/auth/refresh` — Refresh access token using refresh token

### Module 2 — Workspaces
- `POST /api/v1/workspaces` — Create workspace (creator becomes OWNER)
- `GET /api/v1/workspaces` — List workspaces for the authenticated user
- `GET /api/v1/workspaces/{id}` — Get workspace by ID
- `PUT /api/v1/workspaces/{id}` — Update workspace (requires ADMIN or OWNER)
- `DELETE /api/v1/workspaces/{id}` — Delete workspace (OWNER only)
- `POST /api/v1/workspaces/{id}/members` — Invite member by email
- `GET /api/v1/workspaces/{id}/members` — List members
- `PUT /api/v1/workspaces/{id}/members/{user_id}` — Change member role
- `DELETE /api/v1/workspaces/{id}/members/{user_id}` — Remove member

### Module 3 — Budgets
- `POST /api/v1/budgets` — Create budget (unique per workspace + category + period)
- `GET /api/v1/budgets?workspace_id=...` — List with filters (category, month, year) and pagination
- `GET /api/v1/budgets/{id}` — Get budget with calculated progress
- `PUT /api/v1/budgets/{id}` — Update limit amount
- `DELETE /api/v1/budgets/{id}` — Soft delete

### Module 4 — Movements
- `POST /api/v1/movements` — Record a movement (income or expense) in a workspace
- `GET /api/v1/movements?workspace_id=...` — List movements with optional filters (category, month, year)

## Architecture

Clean architecture in four layers:

```
backend/app/
├── domain/         # Entities, repository interfaces, value objects
├── application/    # Use cases, DTOs, domain exceptions
├── infrastructure/ # SQLAlchemy models, repository implementations
└── api/            # FastAPI routers, dependencies
```

### Technical Decisions

**Repository Pattern**: Abstract interfaces live in `domain/repositories.py`. Use cases depend only on those interfaces. PostgreSQL implementations are in `infrastructure/` and injected via FastAPI `Depends()`.

**Value Objects**: `Email` normalizes to lowercase before validation. `Password` enforces minimum complexity (uppercase, number, symbol). `BudgetPeriod` validates month range (1–12) and a reasonable year range.

**JWT**: Short-lived access token (configurable, default 30 min) + long-lived refresh token (default 7 days). Implemented with `python-jose`. No cookies used: tokens are passed via `Authorization: Bearer`.

**Direct bcrypt**: `bcrypt` is used directly instead of `passlib` due to incompatibility between `passlib` and `bcrypt >= 4.x` on Python 3.12+.

**Soft delete on budgets**: Budgets are never physically deleted; `deleted_at` is set instead. All queries filter `WHERE deleted_at IS NULL`.

**Dynamic progress**: The `progress_percentage` field on budgets is never stored. It is calculated at runtime as `sum(expenses) / limit_amount * 100` by querying the `movements` table.

**Workspace roles**: Hierarchy `owner > admin > editor > viewer`. Authorization rules are encapsulated in `WorkspaceRole` entity methods (`can_manage_members`, `has_minimum_role`).

**Async Alembic**: Migrations use `async_engine_from_config` and `asyncio.run()` for compatibility with asyncpg. They are executed from inside the container.

**Movement endpoints**: The spec only required dynamically calculating progress from existing movements. `POST /movements` and `GET /movements` were added to demonstrate that calculation live — without them, `progress_percentage` would always be `0%` in any demo. The cost was low since the table, model, and repository interface already existed.

**Stateless refresh token**: The refresh token is a long-lived signed JWT. When used, a new token pair is issued, but the previous token remains technically valid until natural expiration. An implementation with immediate invalidation would require storing tokens in a database or a Redis blacklist; that complexity was intentionally omitted to keep the architecture stateless. The risk is mitigated with short access token TTLs (30 min) and reasonably short refresh TTLs (7 days).

**Library justification**:
- `bcrypt` (without `passlib`): passlib has incompatibility with bcrypt >= 4.x on Python 3.12+; bcrypt is used directly to avoid the issue.
- `python-jose`: standard JWT library in the FastAPI ecosystem.
- `asyncpg`: native async driver for PostgreSQL, required by SQLAlchemy async.
- `pydantic-settings`: typed configuration management with `.env` support.

## Test Users

No seed data is included. To create a user and explore the API:

```bash
# Register a user (returns access_token and refresh_token)
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test1234!", "full_name": "Test User"}'

# Alternatively, use the interactive documentation at:
# http://localhost:8000/docs
```

The access token obtained should be passed as `Authorization: Bearer <token>` on protected endpoints.

## Limitations and Out-of-Scope Items

- **Frontend**: Not implemented. The assessment was solved backend-only (Python/FastAPI). The React/TypeScript module is outside the scope of this submission.
- **Refresh token invalidation**: As described in the technical decisions, the refresh token is stateless. No blacklist or DB-persisted rotation was implemented.
- **Unit tests for repositories**: Repositories are covered by integration tests against a real DB. No additional unit tests with a mocked session were added, as behavioral coverage is already guaranteed by the integration tests.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://habi:habi@db:5432/habi_db` | Connection URL |
| `SECRET_KEY` | `dev-secret-key-change-in-production` | JWT signing key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL |
| `TEST_DATABASE_URL` | `postgresql+asyncpg://habi:habi@localhost:5432/habi_test` | Test DB URL |

## Test Structure

```
tests/
├── unit/         # Use cases and value objects with mocks (no DB)
├── integration/  # Repositories against real DB (habi_test)
└── e2e/          # Full HTTP flow via AsyncClient
```

The `db_session` fixture rolls back after each test to guarantee isolation. E2E tests use `app.dependency_overrides` to inject the test session.
