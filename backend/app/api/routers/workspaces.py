from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.dtos import (
    CreateWorkspaceInputDTO,
    InviteMemberInputDTO,
    UpdateMemberRoleInputDTO,
    UpdateWorkspaceInputDTO,
    WorkspaceMemberOutputDTO,
    WorkspaceOutputDTO,
)
from app.application.exceptions import (
    AccessDeniedError,
    AlreadyMemberError,
    CannotModifyOwnerError,
    NotFoundError,
)
from app.application.use_cases.create_workspace import CreateWorkspaceUseCase
from app.application.use_cases.delete_workspace import DeleteWorkspaceUseCase
from app.application.use_cases.get_workspace import GetWorkspaceUseCase
from app.application.use_cases.invite_member import InviteMemberUseCase
from app.application.use_cases.list_members import ListMembersUseCase
from app.application.use_cases.list_workspaces import ListWorkspacesUseCase
from app.application.use_cases.remove_member import RemoveMemberUseCase
from app.application.use_cases.update_member_role import UpdateMemberRoleUseCase
from app.application.use_cases.update_workspace import UpdateWorkspaceUseCase
from app.api.dependencies import (
    get_current_user,
    get_member_repository,
    get_user_repository,
    get_workspace_repository,
)
from app.domain.entities import User
from app.domain.repositories import UserRepository, WorkspaceMemberRepository, WorkspaceRepository

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


def _handle_errors(func):
    """Decorator that converts domain exceptions to HTTP responses."""
    from functools import wraps
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except NotFoundError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except AccessDeniedError as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        except (AlreadyMemberError, CannotModifyOwnerError) as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return wrapper


@router.post("", response_model=WorkspaceOutputDTO, status_code=status.HTTP_201_CREATED)
@_handle_errors
async def create_workspace(
    body: CreateWorkspaceInputDTO,
    current_user: User = Depends(get_current_user),
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository),
    member_repo: WorkspaceMemberRepository = Depends(get_member_repository),
    user_repo: UserRepository = Depends(get_user_repository),
):
    return await CreateWorkspaceUseCase(workspace_repo, member_repo, user_repo).execute(body, current_user.id)


@router.get("", response_model=list[WorkspaceOutputDTO])
async def list_workspaces(
    current_user: User = Depends(get_current_user),
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository),
):
    return await ListWorkspacesUseCase(workspace_repo).execute(current_user.id)


@router.get("/{workspace_id}", response_model=WorkspaceOutputDTO)
@_handle_errors
async def get_workspace(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository),
    member_repo: WorkspaceMemberRepository = Depends(get_member_repository),
):
    return await GetWorkspaceUseCase(workspace_repo, member_repo).execute(workspace_id, current_user.id)


@router.put("/{workspace_id}", response_model=WorkspaceOutputDTO)
@_handle_errors
async def update_workspace(
    workspace_id: UUID,
    body: UpdateWorkspaceInputDTO,
    current_user: User = Depends(get_current_user),
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository),
    member_repo: WorkspaceMemberRepository = Depends(get_member_repository),
):
    return await UpdateWorkspaceUseCase(workspace_repo, member_repo).execute(workspace_id, body, current_user.id)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
@_handle_errors
async def delete_workspace(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository),
    member_repo: WorkspaceMemberRepository = Depends(get_member_repository),
):
    await DeleteWorkspaceUseCase(workspace_repo, member_repo).execute(workspace_id, current_user.id)


@router.post("/{workspace_id}/members", response_model=WorkspaceMemberOutputDTO, status_code=status.HTTP_201_CREATED)
@_handle_errors
async def invite_member(
    workspace_id: UUID,
    body: InviteMemberInputDTO,
    current_user: User = Depends(get_current_user),
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository),
    member_repo: WorkspaceMemberRepository = Depends(get_member_repository),
    user_repo: UserRepository = Depends(get_user_repository),
):
    return await InviteMemberUseCase(workspace_repo, member_repo, user_repo).execute(workspace_id, body, current_user.id)


@router.get("/{workspace_id}/members", response_model=list[WorkspaceMemberOutputDTO])
@_handle_errors
async def list_members(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository),
    member_repo: WorkspaceMemberRepository = Depends(get_member_repository),
):
    return await ListMembersUseCase(workspace_repo, member_repo).execute(workspace_id, current_user.id)


@router.put("/{workspace_id}/members/{user_id}", response_model=WorkspaceMemberOutputDTO)
@_handle_errors
async def update_member_role(
    workspace_id: UUID,
    user_id: UUID,
    body: UpdateMemberRoleInputDTO,
    current_user: User = Depends(get_current_user),
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository),
    member_repo: WorkspaceMemberRepository = Depends(get_member_repository),
):
    return await UpdateMemberRoleUseCase(workspace_repo, member_repo).execute(workspace_id, user_id, body, current_user.id)


@router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@_handle_errors
async def remove_member(
    workspace_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository),
    member_repo: WorkspaceMemberRepository = Depends(get_member_repository),
):
    await RemoveMemberUseCase(workspace_repo, member_repo).execute(workspace_id, user_id, current_user.id)
