# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal financial planning system (Prueba Técnica - Habi). Backend-focused implementation using Python/FastAPI + PostgreSQL + Docker Compose. Three modules: Authentication, Workspaces, Budgets.

## Project Structure

```
backend/       # Python/FastAPI application
frontend/      # React/TypeScript (out of scope for this implementation)
migrations/    # Alembic DB migration scripts
docker-compose.yml
```

## Infrastructure

```bash
# Start all services (PostgreSQL + backend)
docker compose up

# Start in background
docker compose up -d

# Rebuild after code changes
docker compose up --build
```

## Database Migrations (Alembic)

```bash
cd backend
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

## Testing

```bash
cd backend

# Run all tests
pytest

# Run with async support
pytest --asyncio-mode=auto

# Run a single test file
pytest tests/unit/test_auth_use_cases.py -v

# Run a single test by name
pytest tests/unit/test_auth_use_cases.py::test_register_user -v

# Run integration tests (requires DB running)
pytest tests/integration/ -v

# Run E2E tests
pytest tests/e2e/ -v

# Run with coverage
pytest --cov=app --cov-report=term-missing
```

## Architecture: Clean Architecture with Layer Separation

The backend follows clean architecture. Flow: `Router → Use Case → Repository → DB`

```
backend/app/
├── domain/           # Entities, Value Objects, Repository interfaces
├── application/      # Use Cases (business logic), DTOs
├── infrastructure/   # Repository implementations, DB models (SQLAlchemy)
└── api/              # FastAPI routers, dependency injection
```

**Key patterns:**
- **Repository Pattern**: `domain/` defines interfaces; `infrastructure/` implements them with SQLAlchemy
- **Use Cases**: one class per business operation, injected with repository interfaces
- **Value Objects**: encapsulate domain validations (e.g., `Email`, `Password`, `Money`)
- **DTOs**: Pydantic models for API input/output, separate from domain entities
- **Dependency Injection**: FastAPI `Depends()` wires use cases and repositories

## Module Relationships

```
Auth → issues JWT (access + refresh tokens)
       ↓
Workspace → validates user access + roles (owner > admin > editor > viewer)
       ↓
Budget → belongs to a workspace, validates workspace membership before any operation
```

Budget progress is **always calculated dynamically**: `(sum of expense movements in category/period) / limit_amount * 100`. Never stored.

## Business Rules to Enforce

**Auth:**
- Email must be unique; password hashed (bcrypt), never stored plain
- Access token: short-lived; Refresh token: long-lived, invalidated after use
- On register, user is immediately active

**Workspace roles hierarchy:** `owner > admin > editor > viewer`
- Only `owner` can delete workspace or be removed (cannot be removed)
- Only `owner`/`admin` can invite members or change roles
- Cannot assign `owner` role via invitation
- A user can only be a member of a workspace once

**Budget:**
- One budget per (workspace, category, period month+year) — enforced by DB unique constraint
- `limit_amount > 0`; month between 1-12
- Soft delete (logical deletion) to preserve history
- Minimum role to create: `viewer`; to update/delete: `editor`

## Testing Strategy

- **Unit tests** (`tests/unit/`): mock repositories, test use cases and value objects in isolation
- **Integration tests** (`tests/integration/`): real DB (test container or test DB), validate CRUD + constraints
- **E2E tests** (`tests/e2e/`): full HTTP flow via FastAPI `TestClient`, includes auth helpers to obtain valid JWT tokens

## Environment Variables

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/habi_db
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Tool Versions Verified

- Git 2.53.0
- Docker 29.3.0 / Docker Compose v5.1.0
- Python 3.14.0 / pip 25.3
- Node 24.14.1 / npm 11.11.0
