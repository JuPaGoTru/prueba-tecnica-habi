from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application.dtos import (
    BudgetListOutputDTO,
    BudgetOutputDTO,
    CreateBudgetInputDTO,
    UpdateBudgetInputDTO,
)
from app.application.exceptions import AccessDeniedError, NotFoundError
from app.application.use_cases.create_budget import CreateBudgetUseCase
from app.application.use_cases.delete_budget import DeleteBudgetUseCase
from app.application.use_cases.get_budget import GetBudgetUseCase
from app.application.use_cases.list_budgets import ListBudgetsUseCase
from app.application.use_cases.update_budget import UpdateBudgetUseCase
from app.api.dependencies import (
    get_budget_repository,
    get_current_user,
    get_member_repository,
    get_movement_repository,
    get_workspace_repository,
)
from app.domain.entities import User
from app.domain.repositories import (
    BudgetRepository,
    MovementRepository,
    WorkspaceMemberRepository,
    WorkspaceRepository,
)

router = APIRouter(prefix="/budgets", tags=["budgets"])


def _handle_errors(func):
    from functools import wraps
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except NotFoundError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except AccessDeniedError as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return wrapper


@router.post("", response_model=BudgetOutputDTO, status_code=status.HTTP_201_CREATED)
@_handle_errors
async def create_budget(
    body: CreateBudgetInputDTO,
    current_user: User = Depends(get_current_user),
    budget_repo: BudgetRepository = Depends(get_budget_repository),
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository),
    member_repo: WorkspaceMemberRepository = Depends(get_member_repository),
    movement_repo: MovementRepository = Depends(get_movement_repository),
):
    return await CreateBudgetUseCase(budget_repo, workspace_repo, member_repo, movement_repo).execute(
        body, current_user.id
    )


@router.get("", response_model=BudgetListOutputDTO)
@_handle_errors
async def list_budgets(
    workspace_id: UUID = Query(...),
    category: str | None = Query(None),
    month: int | None = Query(None, ge=1, le=12),
    year: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    budget_repo: BudgetRepository = Depends(get_budget_repository),
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository),
    member_repo: WorkspaceMemberRepository = Depends(get_member_repository),
    movement_repo: MovementRepository = Depends(get_movement_repository),
):
    return await ListBudgetsUseCase(budget_repo, workspace_repo, member_repo, movement_repo).execute(
        workspace_id, current_user.id, category, month, year, page, page_size
    )


@router.get("/{budget_id}", response_model=BudgetOutputDTO)
@_handle_errors
async def get_budget(
    budget_id: UUID,
    current_user: User = Depends(get_current_user),
    budget_repo: BudgetRepository = Depends(get_budget_repository),
    member_repo: WorkspaceMemberRepository = Depends(get_member_repository),
    movement_repo: MovementRepository = Depends(get_movement_repository),
):
    return await GetBudgetUseCase(budget_repo, member_repo, movement_repo).execute(budget_id, current_user.id)


@router.put("/{budget_id}", response_model=BudgetOutputDTO)
@_handle_errors
async def update_budget(
    budget_id: UUID,
    body: UpdateBudgetInputDTO,
    current_user: User = Depends(get_current_user),
    budget_repo: BudgetRepository = Depends(get_budget_repository),
    member_repo: WorkspaceMemberRepository = Depends(get_member_repository),
    movement_repo: MovementRepository = Depends(get_movement_repository),
):
    return await UpdateBudgetUseCase(budget_repo, member_repo, movement_repo).execute(
        budget_id, body, current_user.id
    )


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
@_handle_errors
async def delete_budget(
    budget_id: UUID,
    current_user: User = Depends(get_current_user),
    budget_repo: BudgetRepository = Depends(get_budget_repository),
    member_repo: WorkspaceMemberRepository = Depends(get_member_repository),
):
    await DeleteBudgetUseCase(budget_repo, member_repo).execute(budget_id, current_user.id)
