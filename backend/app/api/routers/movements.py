from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application.dtos import CreateMovementInputDTO, MovementOutputDTO
from app.application.exceptions import AccessDeniedError, NotFoundError
from app.application.use_cases.create_movement import CreateMovementUseCase
from app.application.use_cases.list_movements import ListMovementsUseCase
from app.api.dependencies import (
    get_current_user,
    get_member_repository,
    get_movement_repository,
    get_workspace_repository,
)
from app.domain.entities import User
from app.domain.repositories import MovementRepository, WorkspaceMemberRepository, WorkspaceRepository

router = APIRouter(prefix="/movements", tags=["movements"])


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


@router.post("", response_model=MovementOutputDTO, status_code=status.HTTP_201_CREATED)
@_handle_errors
async def create_movement(
    body: CreateMovementInputDTO,
    current_user: User = Depends(get_current_user),
    movement_repo: MovementRepository = Depends(get_movement_repository),
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository),
    member_repo: WorkspaceMemberRepository = Depends(get_member_repository),
):
    return await CreateMovementUseCase(movement_repo, workspace_repo, member_repo).execute(body, current_user.id)


@router.get("", response_model=list[MovementOutputDTO])
@_handle_errors
async def list_movements(
    workspace_id: UUID = Query(...),
    category: str | None = Query(None),
    month: int | None = Query(None, ge=1, le=12),
    year: int | None = Query(None),
    current_user: User = Depends(get_current_user),
    movement_repo: MovementRepository = Depends(get_movement_repository),
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository),
    member_repo: WorkspaceMemberRepository = Depends(get_member_repository),
):
    return await ListMovementsUseCase(movement_repo, workspace_repo, member_repo).execute(
        workspace_id, current_user.id, category, month, year
    )
