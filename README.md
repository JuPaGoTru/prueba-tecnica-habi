# Prueba Técnica — Habi: Sistema de Planificación Financiera

Backend REST API para gestión de presupuestos personales por workspace. Implementado en Python con FastAPI, PostgreSQL y arquitectura limpia.

## Requisitos

- Docker y Docker Compose

## Levantar el proyecto

```bash
docker compose up --build
```

La API queda disponible en `http://localhost:8000`.
Documentación interactiva: `http://localhost:8000/docs`

## Migraciones

Las migraciones se ejecutan una sola vez para crear el schema:

```bash
docker compose exec backend sh -c "cd /app && alembic upgrade head"
```

## Tests

Todos los tests corren dentro del contenedor contra una base de datos real `habi_test`.

```bash
# Crear la DB de test (solo la primera vez)
docker compose exec db psql -U habi -d habi_db -c "CREATE DATABASE habi_test;"

# Tests de integración (repositorios contra DB)
docker compose exec backend sh -c "cd /app && TEST_DATABASE_URL='postgresql+asyncpg://habi:habi@db:5432/habi_test' pytest tests/integration/ -v"

# Tests E2E (flujo HTTP completo)
docker compose exec backend sh -c "cd /app && TEST_DATABASE_URL='postgresql+asyncpg://habi:habi@db:5432/habi_test' pytest tests/e2e/ -v"

# Tests unitarios (sin DB)
docker compose exec backend pytest tests/unit/ -v

# Todos los tests
docker compose exec backend sh -c "cd /app && TEST_DATABASE_URL='postgresql+asyncpg://habi:habi@db:5432/habi_test' pytest tests/ -v"
```

## Módulos implementados

### Módulo 1 — Autenticación JWT
- `POST /api/v1/auth/register` — Registro de usuario (devuelve tokens)
- `POST /api/v1/auth/login` — Login con email y contraseña
- `POST /api/v1/auth/refresh` — Renovar access token con refresh token

### Módulo 2 — Workspaces
- `POST /api/v1/workspaces` — Crear workspace (el creador queda como OWNER)
- `GET /api/v1/workspaces` — Listar workspaces del usuario autenticado
- `GET /api/v1/workspaces/{id}` — Obtener workspace por ID
- `PUT /api/v1/workspaces/{id}` — Actualizar workspace (requiere ADMIN o OWNER)
- `DELETE /api/v1/workspaces/{id}` — Eliminar workspace (solo OWNER)
- `POST /api/v1/workspaces/{id}/members` — Invitar miembro por email
- `GET /api/v1/workspaces/{id}/members` — Listar miembros
- `PUT /api/v1/workspaces/{id}/members/{user_id}` — Cambiar rol
- `DELETE /api/v1/workspaces/{id}/members/{user_id}` — Remover miembro

### Módulo 3 — Presupuestos
- `POST /api/v1/budgets` — Crear presupuesto (único por workspace + categoría + periodo)
- `GET /api/v1/budgets?workspace_id=...` — Listar con filtros (categoría, mes, año) y paginación
- `GET /api/v1/budgets/{id}` — Obtener presupuesto con progreso calculado
- `PUT /api/v1/budgets/{id}` — Actualizar monto límite
- `DELETE /api/v1/budgets/{id}` — Soft delete

## Arquitectura

Arquitectura limpia en cuatro capas:

```
backend/app/
├── domain/         # Entidades, interfaces de repositorio, value objects
├── application/    # Casos de uso, DTOs, excepciones de dominio
├── infrastructure/ # Modelos SQLAlchemy, implementaciones de repositorios
└── api/            # Routers FastAPI, dependencias
```

### Decisiones técnicas

**Patrón Repository**: Las interfaces abstractas viven en `domain/repositories.py`. Los casos de uso dependen solo de esas interfaces. Las implementaciones PostgreSQL están en `infrastructure/` y se inyectan vía FastAPI `Depends()`.

**Value Objects**: `Email` normaliza a lowercase antes de validar. `Password` verifica complejidad mínima (mayúscula, número, símbolo). `BudgetPeriod` valida rango de mes (1-12) y año razonable.

**JWT**: Access token de vida corta (configurable, default 30 min) + refresh token de vida larga (default 7 días). Implementado con `python-jose`. No se usan cookies: los tokens van en `Authorization: Bearer`.

**bcrypt directo**: Se usa `bcrypt` directamente en lugar de `passlib` por incompatibilidad de `passlib` con `bcrypt >= 4.x` en Python 3.12+.

**Soft delete en presupuestos**: Los presupuestos nunca se eliminan físicamente; se marca `deleted_at`. Los queries filtran `WHERE deleted_at IS NULL`.

**Progreso dinámico**: El campo `progress_percentage` en presupuestos nunca se almacena. Se calcula en tiempo real como `sum(expenses) / limit_amount * 100` consultando la tabla `movements`.

**Roles de workspace**: Jerarquía `owner > admin > editor > viewer`. Los métodos de la entidad `WorkspaceRole` encapsulan las reglas de autorización (`can_manage_members`, `has_minimum_role`).

**Alembic async**: Las migraciones usan `async_engine_from_config` y `asyncio.run()` para compatibilidad con asyncpg. Se ejecutan desde dentro del contenedor.

## Variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://habi:habi@db:5432/habi_db` | URL de conexión |
| `SECRET_KEY` | `dev-secret-key-change-in-production` | Clave para firmar JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | TTL del access token |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | TTL del refresh token |
| `TEST_DATABASE_URL` | `postgresql+asyncpg://habi:habi@localhost:5432/habi_test` | URL para tests |

## Estructura de tests

```
tests/
├── unit/         # Casos de uso y value objects con mocks (sin DB)
├── integration/  # Repositorios contra DB real (habi_test)
└── e2e/          # Flujo HTTP completo vía AsyncClient
```

La fixture `db_session` hace rollback después de cada test para garantizar aislamiento. Los tests E2E usan `app.dependency_overrides` para inyectar la sesión de test.
