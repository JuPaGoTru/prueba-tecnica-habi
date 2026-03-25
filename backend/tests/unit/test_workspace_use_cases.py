import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

from app.application.dtos import (
    CreateWorkspaceInputDTO,
    InviteMemberInputDTO,
    UpdateMemberRoleInputDTO,
    UpdateWorkspaceInputDTO,
)
from app.application.exceptions import (
    AccessDeniedError,
    AlreadyMemberError,
    CannotModifyOwnerError,
    NotFoundError,
)
from app.application.use_cases.create_workspace import CreateWorkspaceUseCase
from app.application.use_cases.delete_workspace import DeleteWorkspaceUseCase
from app.application.use_cases.invite_member import InviteMemberUseCase
from app.application.use_cases.remove_member import RemoveMemberUseCase
from app.application.use_cases.update_member_role import UpdateMemberRoleUseCase
from app.application.use_cases.update_workspace import UpdateWorkspaceUseCase
from app.domain.entities import User, Workspace, WorkspaceMember, WorkspaceRole


def make_user(is_active=True) -> User:
    return User(
        id=uuid4(), email="u@example.com", hashed_password="x",
        full_name=None, is_active=is_active,
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )


def make_workspace(owner_id=None) -> Workspace:
    return Workspace(
        id=uuid4(), name="My WS", description=None,
        owner_id=owner_id or uuid4(), settings=None, is_active=True,
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )


def make_member(user_id=None, workspace_id=None, role=WorkspaceRole.EDITOR) -> WorkspaceMember:
    return WorkspaceMember(
        id=uuid4(), workspace_id=workspace_id or uuid4(),
        user_id=user_id or uuid4(), role=role,
        invited_by=None, joined_at=datetime.now(timezone.utc),
    )


# --- CreateWorkspace ---

async def test_create_workspace_adds_owner_as_member():
    user = make_user()
    workspace_repo = AsyncMock()
    member_repo = AsyncMock()
    user_repo = AsyncMock()

    created_ws = make_workspace(owner_id=user.id)
    user_repo.get_by_id = AsyncMock(return_value=user)
    workspace_repo.create = AsyncMock(return_value=created_ws)
    member_repo.add = AsyncMock()

    dto = CreateWorkspaceInputDTO(name="My WS")
    result = await CreateWorkspaceUseCase(workspace_repo, member_repo, user_repo).execute(dto, user.id)

    assert result.owner_id == user.id
    member_repo.add.assert_called_once()
    added_member = member_repo.add.call_args[0][0]
    assert added_member.role == WorkspaceRole.OWNER


async def test_create_workspace_inactive_user_raises():
    user = make_user(is_active=False)
    user_repo = AsyncMock()
    user_repo.get_by_id = AsyncMock(return_value=user)

    with pytest.raises(NotFoundError):
        await CreateWorkspaceUseCase(AsyncMock(), AsyncMock(), user_repo).execute(
            CreateWorkspaceInputDTO(name="WS"), user.id
        )


# --- UpdateWorkspace ---

async def test_update_workspace_owner_succeeds():
    owner_id = uuid4()
    ws = make_workspace(owner_id=owner_id)
    member = make_member(user_id=owner_id, workspace_id=ws.id, role=WorkspaceRole.OWNER)

    workspace_repo = AsyncMock()
    member_repo = AsyncMock()
    workspace_repo.get_by_id = AsyncMock(return_value=ws)
    member_repo.get = AsyncMock(return_value=member)
    workspace_repo.update = AsyncMock(return_value=ws)

    dto = UpdateWorkspaceInputDTO(name="New Name")
    await UpdateWorkspaceUseCase(workspace_repo, member_repo).execute(ws.id, dto, owner_id)
    workspace_repo.update.assert_called_once()


async def test_update_workspace_viewer_raises():
    user_id = uuid4()
    ws = make_workspace()
    member = make_member(user_id=user_id, role=WorkspaceRole.VIEWER)

    workspace_repo = AsyncMock()
    member_repo = AsyncMock()
    workspace_repo.get_by_id = AsyncMock(return_value=ws)
    member_repo.get = AsyncMock(return_value=member)

    with pytest.raises(AccessDeniedError):
        await UpdateWorkspaceUseCase(workspace_repo, member_repo).execute(
            ws.id, UpdateWorkspaceInputDTO(name="X"), user_id
        )


# --- DeleteWorkspace ---

async def test_delete_workspace_only_owner():
    owner_id = uuid4()
    ws = make_workspace(owner_id=owner_id)
    owner_member = make_member(user_id=owner_id, role=WorkspaceRole.OWNER)

    workspace_repo = AsyncMock()
    member_repo = AsyncMock()
    workspace_repo.get_by_id = AsyncMock(return_value=ws)
    member_repo.get = AsyncMock(return_value=owner_member)
    workspace_repo.delete = AsyncMock()

    await DeleteWorkspaceUseCase(workspace_repo, member_repo).execute(ws.id, owner_id)
    workspace_repo.delete.assert_called_once_with(ws.id)


async def test_delete_workspace_non_owner_raises():
    user_id = uuid4()
    ws = make_workspace()
    member = make_member(user_id=user_id, role=WorkspaceRole.ADMIN)

    workspace_repo = AsyncMock()
    member_repo = AsyncMock()
    workspace_repo.get_by_id = AsyncMock(return_value=ws)
    member_repo.get = AsyncMock(return_value=member)

    with pytest.raises(AccessDeniedError):
        await DeleteWorkspaceUseCase(workspace_repo, member_repo).execute(ws.id, user_id)


# --- InviteMember ---

async def test_invite_member_succeeds():
    inviter_id = uuid4()
    ws = make_workspace()
    inviter_member = make_member(user_id=inviter_id, role=WorkspaceRole.ADMIN)
    target_user = make_user()

    workspace_repo = AsyncMock()
    member_repo = AsyncMock()
    user_repo = AsyncMock()
    workspace_repo.get_by_id = AsyncMock(return_value=ws)
    member_repo.get = AsyncMock(side_effect=[inviter_member, None])
    user_repo.get_by_email = AsyncMock(return_value=target_user)
    new_member = make_member(user_id=target_user.id, role=WorkspaceRole.VIEWER)
    member_repo.add = AsyncMock(return_value=new_member)

    dto = InviteMemberInputDTO(email=target_user.email, role=WorkspaceRole.VIEWER)
    result = await InviteMemberUseCase(workspace_repo, member_repo, user_repo).execute(ws.id, dto, inviter_id)
    assert result.user_id == target_user.id


async def test_invite_owner_role_raises():
    inviter_id = uuid4()
    ws = make_workspace()
    inviter_member = make_member(user_id=inviter_id, role=WorkspaceRole.OWNER)

    workspace_repo = AsyncMock()
    member_repo = AsyncMock()
    user_repo = AsyncMock()
    workspace_repo.get_by_id = AsyncMock(return_value=ws)
    member_repo.get = AsyncMock(return_value=inviter_member)

    dto = InviteMemberInputDTO(email="x@x.com", role=WorkspaceRole.OWNER)
    with pytest.raises(CannotModifyOwnerError):
        await InviteMemberUseCase(workspace_repo, member_repo, user_repo).execute(ws.id, dto, inviter_id)


async def test_invite_already_member_raises():
    inviter_id = uuid4()
    ws = make_workspace()
    inviter_member = make_member(user_id=inviter_id, role=WorkspaceRole.ADMIN)
    target_user = make_user()
    existing_member = make_member(user_id=target_user.id)

    workspace_repo = AsyncMock()
    member_repo = AsyncMock()
    user_repo = AsyncMock()
    workspace_repo.get_by_id = AsyncMock(return_value=ws)
    member_repo.get = AsyncMock(side_effect=[inviter_member, existing_member])
    user_repo.get_by_email = AsyncMock(return_value=target_user)

    dto = InviteMemberInputDTO(email=target_user.email, role=WorkspaceRole.EDITOR)
    with pytest.raises(AlreadyMemberError):
        await InviteMemberUseCase(workspace_repo, member_repo, user_repo).execute(ws.id, dto, inviter_id)


# --- RemoveMember ---

async def test_remove_owner_raises():
    owner_id = uuid4()
    ws = make_workspace(owner_id=owner_id)
    owner_member = make_member(user_id=owner_id, role=WorkspaceRole.OWNER)

    workspace_repo = AsyncMock()
    member_repo = AsyncMock()
    workspace_repo.get_by_id = AsyncMock(return_value=ws)
    member_repo.get = AsyncMock(return_value=owner_member)

    with pytest.raises(CannotModifyOwnerError):
        await RemoveMemberUseCase(workspace_repo, member_repo).execute(ws.id, owner_id, uuid4())


# --- UpdateMemberRole ---

async def test_update_role_to_owner_raises():
    requester_id = uuid4()
    target_id = uuid4()
    ws = make_workspace()
    requester_member = make_member(user_id=requester_id, role=WorkspaceRole.OWNER)
    target_member = make_member(user_id=target_id, role=WorkspaceRole.EDITOR)

    workspace_repo = AsyncMock()
    member_repo = AsyncMock()
    workspace_repo.get_by_id = AsyncMock(return_value=ws)
    member_repo.get = AsyncMock(side_effect=[target_member, requester_member])

    with pytest.raises(CannotModifyOwnerError):
        await UpdateMemberRoleUseCase(workspace_repo, member_repo).execute(
            ws.id, target_id, UpdateMemberRoleInputDTO(role=WorkspaceRole.OWNER), requester_id
        )


async def test_update_owner_role_raises():
    requester_id = uuid4()
    owner_id = uuid4()
    ws = make_workspace(owner_id=owner_id)
    owner_member = make_member(user_id=owner_id, role=WorkspaceRole.OWNER)

    workspace_repo = AsyncMock()
    member_repo = AsyncMock()
    workspace_repo.get_by_id = AsyncMock(return_value=ws)
    member_repo.get = AsyncMock(return_value=owner_member)

    with pytest.raises(CannotModifyOwnerError):
        await UpdateMemberRoleUseCase(workspace_repo, member_repo).execute(
            ws.id, owner_id, UpdateMemberRoleInputDTO(role=WorkspaceRole.ADMIN), requester_id
        )
