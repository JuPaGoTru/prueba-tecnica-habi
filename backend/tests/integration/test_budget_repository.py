import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Budget, User, Workspace
from app.infrastructure.budget_repository import PostgresBudgetRepository, PostgresMovementRepository
from app.infrastructure.models import MovementModel
from app.infrastructure.user_repository import PostgresUserRepository
from app.infrastructure.workspace_repository import PostgresWorkspaceRepository


def make_user() -> User:
    now = datetime.now(timezone.utc)
    return User(
        id=uuid.uuid4(),
        email=f"b_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="hashed",
        full_name=None,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def make_workspace(owner_id: uuid.UUID) -> Workspace:
    now = datetime.now(timezone.utc)
    return Workspace(
        id=uuid.uuid4(), name="WS", description=None,
        owner_id=owner_id, settings=None, is_active=True,
        created_at=now, updated_at=now,
    )


def make_budget(user_id: uuid.UUID, workspace_id: uuid.UUID, category: str = "Food") -> Budget:
    now = datetime.now(timezone.utc)
    return Budget(
        id=uuid.uuid4(), user_id=user_id, workspace_id=workspace_id,
        category=category, limit_amount=500.0,
        period_month=3, period_year=2026,
        is_active=True, created_at=now, updated_at=now, deleted_at=None,
    )


async def test_create_and_get_budget(db_session: AsyncSession):
    user_repo = PostgresUserRepository(db_session)
    ws_repo = PostgresWorkspaceRepository(db_session)
    budget_repo = PostgresBudgetRepository(db_session)

    user = await user_repo.create(make_user())
    ws = await ws_repo.create(make_workspace(user.id))
    budget = await budget_repo.create(make_budget(user.id, ws.id))

    found = await budget_repo.get_by_id(budget.id)
    assert found is not None
    assert found.category == "Food"
    assert found.limit_amount == 500.0


async def test_unique_budget_period_constraint(db_session: AsyncSession):
    user_repo = PostgresUserRepository(db_session)
    ws_repo = PostgresWorkspaceRepository(db_session)
    budget_repo = PostgresBudgetRepository(db_session)

    user = await user_repo.create(make_user())
    ws = await ws_repo.create(make_workspace(user.id))

    await budget_repo.create(make_budget(user.id, ws.id, "Food"))
    with pytest.raises(Exception):
        await budget_repo.create(make_budget(user.id, ws.id, "Food"))


async def test_soft_delete_budget(db_session: AsyncSession):
    user_repo = PostgresUserRepository(db_session)
    ws_repo = PostgresWorkspaceRepository(db_session)
    budget_repo = PostgresBudgetRepository(db_session)

    user = await user_repo.create(make_user())
    ws = await ws_repo.create(make_workspace(user.id))
    budget = await budget_repo.create(make_budget(user.id, ws.id))

    await budget_repo.soft_delete(budget.id)
    found = await budget_repo.get_by_id(budget.id)
    assert found is None


async def test_list_budgets_with_filters(db_session: AsyncSession):
    user_repo = PostgresUserRepository(db_session)
    ws_repo = PostgresWorkspaceRepository(db_session)
    budget_repo = PostgresBudgetRepository(db_session)

    user = await user_repo.create(make_user())
    ws = await ws_repo.create(make_workspace(user.id))
    await budget_repo.create(make_budget(user.id, ws.id, "Food"))
    await budget_repo.create(make_budget(user.id, ws.id, "Transport"))

    budgets, total = await budget_repo.list_by_workspace(ws.id, None, None, None, 0, 10)
    assert total == 2

    budgets, total = await budget_repo.list_by_workspace(ws.id, "Food", None, None, 0, 10)
    assert total == 1
    assert budgets[0].category == "Food"


async def test_movement_total_expenses(db_session: AsyncSession):
    user_repo = PostgresUserRepository(db_session)
    ws_repo = PostgresWorkspaceRepository(db_session)
    movement_repo = PostgresMovementRepository(db_session)

    user = await user_repo.create(make_user())
    ws = await ws_repo.create(make_workspace(user.id))

    now = datetime.now(timezone.utc)
    for amount in [100.0, 50.0, 75.0]:
        db_session.add(MovementModel(
            id=uuid.uuid4(), workspace_id=ws.id, user_id=user.id,
            category="Food", amount=amount, type="expense",
            period_month=3, period_year=2026, created_at=now,
        ))
    await db_session.flush()

    total = await movement_repo.get_total_expenses(ws.id, "Food", 3, 2026)
    assert total == 225.0


async def test_movement_ignores_income(db_session: AsyncSession):
    user_repo = PostgresUserRepository(db_session)
    ws_repo = PostgresWorkspaceRepository(db_session)
    movement_repo = PostgresMovementRepository(db_session)

    user = await user_repo.create(make_user())
    ws = await ws_repo.create(make_workspace(user.id))
    now = datetime.now(timezone.utc)

    db_session.add(MovementModel(
        id=uuid.uuid4(), workspace_id=ws.id, user_id=user.id,
        category="Food", amount=200.0, type="income",
        period_month=3, period_year=2026, created_at=now,
    ))
    await db_session.flush()

    total = await movement_repo.get_total_expenses(ws.id, "Food", 3, 2026)
    assert total == 0.0
