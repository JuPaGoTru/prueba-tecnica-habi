# Prueba Técnica — Habi: Sistema de Planificación Financiera

Backend REST API para gestión de presupuestos personales por workspace. Implementado en Python con FastAPI, PostgreSQL y arquitectura limpia.

## Requisitos

- Docker y Docker Compose

## Configuración inicial

```bash
# Copiar el archivo de variables de entorno
cp .env.example .env
```

El `.env` incluido en el repo contiene valores para desarrollo local. En producción reemplazar `SECRET_KEY` por un valor seguro.

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

Los tests corren dentro del contenedor. La variable `TEST_DATABASE_URL` se lee del `.env`.

```bash
# Crear la DB de test (solo la primera vez)
docker compose exec db psql -U habi -d habi_db -c "CREATE DATABASE habi_test;"

# Tests unitarios (sin DB)
docker compose exec backend pytest tests/unit/ -v

# Tests de integración (repositorios contra DB)
docker compose exec backend sh -c "cd /app && pytest tests/integration/ -v"

# Tests E2E (flujo HTTP completo)
docker compose exec backend sh -c "cd /app && pytest tests/e2e/ -v"

# Todos los tests
docker compose exec backend sh -c "cd /app && pytest tests/ -v"
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

**Refresh token stateless**: El refresh token es un JWT firmado de larga duración. Al usarlo se emite un nuevo par de tokens, pero el token anterior permanece técnicamente válido hasta su expiración natural. Una implementación con invalidación inmediata requeriría almacenar tokens en base de datos o una blacklist en Redis; esa complejidad se omitió intencionalmente para mantener la arquitectura stateless. El riesgo se mitiga con TTL cortos en el access token (30 min) y razonablemente cortos en el refresh (7 días).

**Justificación de librerías**:
- `bcrypt` directo (sin `passlib`): passlib tiene incompatibilidad con bcrypt >= 4.x en Python 3.12+; se usa bcrypt directamente para evitar el problema.
- `python-jose`: librería estándar del ecosistema FastAPI para JWT.
- `asyncpg`: driver async nativo para PostgreSQL, requerido por SQLAlchemy async.
- `pydantic-settings`: gestión de configuración con tipado y soporte a `.env`.

## Usuarios de prueba

No hay datos precargados. Para crear un usuario y explorar la API:

```bash
# Registrar un usuario (devuelve access_token y refresh_token)
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test1234!", "full_name": "Test User"}'

# Alternativamente, usar la documentación interactiva en:
# http://localhost:8000/docs
```

El access token obtenido se pasa como `Authorization: Bearer <token>` en los endpoints protegidos.

## Limitaciones y aspectos no implementados

- **Frontend**: No implementado. La prueba se resolvió backend-only (Python/FastAPI). El módulo React/TypeScript queda fuera del alcance de esta entrega.
- **Invalidación de refresh token**: Como se describe en las decisiones técnicas, el refresh token es stateless. No se implementó blacklist ni rotación con persistencia en DB.
- **Endpoints de movimientos**: La tabla `movements` existe en el schema y el repositorio `MovementRepository` está implementado para calcular el progreso de presupuestos, pero no se exponen endpoints CRUD para movimientos (no eran requeridos por el enunciado).
- **Tests unitarios para repositorios**: Los repositorios se cubren con tests de integración contra DB real. No se agregaron tests unitarios adicionales con sesión mockeada, ya que la cobertura de comportamiento queda garantizada por los integration tests.

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
