import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

from app.application.dtos import CreateBudgetInputDTO, UpdateBudgetInputDTO
from app.application.exceptions import AccessDeniedError, ConflictError, NotFoundError
from app.application.use_cases.create_budget import CreateBudgetUseCase
from app.application.use_cases.delete_budget import DeleteBudgetUseCase
from app.application.use_cases.get_budget import GetBudgetUseCase
from app.application.use_cases.update_budget import UpdateBudgetUseCase
from app.domain.entities import Budget, Workspace, WorkspaceMember, WorkspaceRole
from app.domain.value_objects import BudgetPeriod


def make_workspace(id=None) -> Workspace:
    return Workspace(
        id=id or uuid4(), name="WS", description=None, owner_id=uuid4(),
        settings=None, is_active=True,
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )


def make_member(role=WorkspaceRole.EDITOR, workspace_id=None, user_id=None) -> WorkspaceMember:
    return WorkspaceMember(
        id=uuid4(), workspace_id=workspace_id or uuid4(),
        user_id=user_id or uuid4(), role=role,
        invited_by=None, joined_at=datetime.now(timezone.utc),
    )


def make_budget(workspace_id=None, limit_amount=100.0) -> Budget:
    return Budget(
        id=uuid4(), user_id=uuid4(), workspace_id=workspace_id or uuid4(),
        category="Food", limit_amount=limit_amount,
        period_month=3, period_year=2026,
        is_active=True,
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
        deleted_at=None,
    )


# --- BudgetPeriod value object ---

def test_budget_period_valid():
    bp = BudgetPeriod(month=6, year=2026)
    assert bp.month == 6 and bp.year == 2026


def test_budget_period_invalid_month():
    with pytest.raises(ValueError, match="period_month"):
        BudgetPeriod(month=13, year=2026)


def test_budget_period_invalid_year():
    with pytest.raises(ValueError, match="period_year"):
        BudgetPeriod(month=1, year=1800)


# --- CreateBudget ---

async def test_create_budget_success():
    user_id = uuid4()
    ws = make_workspace()
    member = make_member(role=WorkspaceRole.VIEWER, workspace_id=ws.id, user_id=user_id)
    budget = make_budget(workspace_id=ws.id)

    budget_repo = AsyncMock()
    workspace_repo = AsyncMock()
    member_repo = AsyncMock()
    movement_repo = AsyncMock()

    workspace_repo.get_by_id = AsyncMock(return_value=ws)
    member_repo.get = AsyncMock(return_value=member)
    budget_repo.get_by_period = AsyncMock(return_value=None)
    budget_repo.create = AsyncMock(return_value=budget)
    movement_repo.get_total_expenses = AsyncMock(return_value=50.0)

    dto = CreateBudgetInputDTO(
        workspace_id=ws.id, category="Food",
        limit_amount=100.0, period_month=3, period_year=2026
    )
    result = await CreateBudgetUseCase(budget_repo, workspace_repo, member_repo, movement_repo).execute(dto, user_id)

    assert result.spent_amount == 50.0
    assert result.progress_percentage == 50.0


async def test_create_budget_no_access_raises():
    user_id = uuid4()
    ws = make_workspace()

    workspace_repo = AsyncMock()
    member_repo = AsyncMock()
    workspace_repo.get_by_id = AsyncMock(return_value=ws)
    member_repo.get = AsyncMock(return_value=None)

    dto = CreateBudgetInputDTO(
        workspace_id=ws.id, category="Food",
        limit_amount=100.0, period_month=3, period_year=2026
    )
    with pytest.raises(AccessDeniedError):
        await CreateBudgetUseCase(AsyncMock(), workspace_repo, member_repo, AsyncMock()).execute(dto, user_id)


async def test_create_budget_duplicate_raises():
    user_id = uuid4()
    ws = make_workspace()
    member = make_member(role=WorkspaceRole.VIEWER, workspace_id=ws.id, user_id=user_id)
    existing = make_budget(workspace_id=ws.id)

    workspace_repo = AsyncMock()
    member_repo = AsyncMock()
    budget_repo = AsyncMock()
    workspace_repo.get_by_id = AsyncMock(return_value=ws)
    member_repo.get = AsyncMock(return_value=member)
    budget_repo.get_by_period = AsyncMock(return_value=existing)

    dto = CreateBudgetInputDTO(
        workspace_id=ws.id, category="Food",
        limit_amount=100.0, period_month=3, period_year=2026
    )
    with pytest.raises(ConflictError, match="already exists"):
        await CreateBudgetUseCase(budget_repo, workspace_repo, member_repo, AsyncMock()).execute(dto, user_id)


async def test_create_budget_zero_amount_raises():
    user_id = uuid4()
    ws = make_workspace()
    member = make_member(role=WorkspaceRole.VIEWER, workspace_id=ws.id, user_id=user_id)

    workspace_repo = AsyncMock()
    member_repo = AsyncMock()
    workspace_repo.get_by_id = AsyncMock(return_value=ws)
    member_repo.get = AsyncMock(return_value=member)

    dto = CreateBudgetInputDTO(
        workspace_id=ws.id, category="Food",
        limit_amount=0.0, period_month=3, period_year=2026
    )
    with pytest.raises(ValueError, match="greater than 0"):
        await CreateBudgetUseCase(AsyncMock(), workspace_repo, member_repo, AsyncMock()).execute(dto, user_id)


# --- GetBudget ---

async def test_get_budget_calculates_progress():
    user_id = uuid4()
    budget = make_budget(limit_amount=200.0)
    member = make_member(workspace_id=budget.workspace_id, user_id=user_id)

    budget_repo = AsyncMock()
    member_repo = AsyncMock()
    movement_repo = AsyncMock()
    budget_repo.get_by_id = AsyncMock(return_value=budget)
    member_repo.get = AsyncMock(return_value=member)
    movement_repo.get_total_expenses = AsyncMock(return_value=100.0)

    result = await GetBudgetUseCase(budget_repo, member_repo, movement_repo).execute(budget.id, user_id)
    assert result.progress_percentage == 50.0
    assert result.spent_amount == 100.0


async def test_get_budget_not_found_raises():
    budget_repo = AsyncMock()
    budget_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(NotFoundError):
        await GetBudgetUseCase(budget_repo, AsyncMock(), AsyncMock()).execute(uuid4(), uuid4())


# --- UpdateBudget ---

async def test_update_budget_viewer_raises():
    user_id = uuid4()
    budget = make_budget()
    member = make_member(role=WorkspaceRole.VIEWER, workspace_id=budget.workspace_id, user_id=user_id)

    budget_repo = AsyncMock()
    member_repo = AsyncMock()
    budget_repo.get_by_id = AsyncMock(return_value=budget)
    member_repo.get = AsyncMock(return_value=member)

    with pytest.raises(AccessDeniedError):
        await UpdateBudgetUseCase(budget_repo, member_repo, AsyncMock()).execute(
            budget.id, UpdateBudgetInputDTO(limit_amount=500.0), user_id
        )


async def test_update_budget_zero_raises():
    budget_repo = AsyncMock()
    with pytest.raises(ValueError, match="greater than 0"):
        await UpdateBudgetUseCase(budget_repo, AsyncMock(), AsyncMock()).execute(
            uuid4(), UpdateBudgetInputDTO(limit_amount=0.0), uuid4()
        )


# --- DeleteBudget ---

async def test_delete_budget_editor_succeeds():
    user_id = uuid4()
    budget = make_budget()
    member = make_member(role=WorkspaceRole.EDITOR, workspace_id=budget.workspace_id, user_id=user_id)

    budget_repo = AsyncMock()
    member_repo = AsyncMock()
    budget_repo.get_by_id = AsyncMock(return_value=budget)
    member_repo.get = AsyncMock(return_value=member)
    budget_repo.soft_delete = AsyncMock()

    await DeleteBudgetUseCase(budget_repo, member_repo).execute(budget.id, user_id)
    budget_repo.soft_delete.assert_called_once_with(budget.id)


async def test_delete_budget_viewer_raises():
    user_id = uuid4()
    budget = make_budget()
    member = make_member(role=WorkspaceRole.VIEWER, workspace_id=budget.workspace_id, user_id=user_id)

    budget_repo = AsyncMock()
    member_repo = AsyncMock()
    budget_repo.get_by_id = AsyncMock(return_value=budget)
    member_repo.get = AsyncMock(return_value=member)

    with pytest.raises(AccessDeniedError):
        await DeleteBudgetUseCase(budget_repo, member_repo).execute(budget.id, user_id)
