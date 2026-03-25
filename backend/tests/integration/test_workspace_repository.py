import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import User, Workspace, WorkspaceMember, WorkspaceRole
from app.infrastructure.user_repository import PostgresUserRepository
from app.infrastructure.workspace_repository import (
    PostgresWorkspaceMemberRepository,
    PostgresWorkspaceRepository,
)


def make_user() -> User:
    now = datetime.now(timezone.utc)
    return User(
        id=uuid.uuid4(),
        email=f"u_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="hashed",
        full_name=None,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def make_workspace(owner_id: uuid.UUID) -> Workspace:
    now = datetime.now(timezone.utc)
    return Workspace(
        id=uuid.uuid4(),
        name="Test Workspace",
        description="A test workspace",
        owner_id=owner_id,
        settings=None,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


async def test_create_and_get_workspace(db_session: AsyncSession):
    user_repo = PostgresUserRepository(db_session)
    ws_repo = PostgresWorkspaceRepository(db_session)

    user = await user_repo.create(make_user())
    ws = await ws_repo.create(make_workspace(user.id))

    found = await ws_repo.get_by_id(ws.id)
    assert found is not None
    assert found.name == "Test Workspace"
    assert found.owner_id == user.id


async def test_list_workspaces_by_user(db_session: AsyncSession):
    user_repo = PostgresUserRepository(db_session)
    ws_repo = PostgresWorkspaceRepository(db_session)
    member_repo = PostgresWorkspaceMemberRepository(db_session)

    user = await user_repo.create(make_user())
    ws = await ws_repo.create(make_workspace(user.id))

    now = datetime.now(timezone.utc)
    member = WorkspaceMember(
        id=uuid.uuid4(), workspace_id=ws.id, user_id=user.id,
        role=WorkspaceRole.OWNER, invited_by=None, joined_at=now,
    )
    await member_repo.add(member)

    workspaces = await ws_repo.list_by_user(user.id)
    assert any(w.id == ws.id for w in workspaces)


async def test_delete_workspace_soft(db_session: AsyncSession):
    user_repo = PostgresUserRepository(db_session)
    ws_repo = PostgresWorkspaceRepository(db_session)

    user = await user_repo.create(make_user())
    ws = await ws_repo.create(make_workspace(user.id))

    await ws_repo.delete(ws.id)
    found = await ws_repo.get_by_id(ws.id)
    assert found is None


async def test_unique_member_constraint(db_session: AsyncSession):
    user_repo = PostgresUserRepository(db_session)
    ws_repo = PostgresWorkspaceRepository(db_session)
    member_repo = PostgresWorkspaceMemberRepository(db_session)

    user = await user_repo.create(make_user())
    ws = await ws_repo.create(make_workspace(user.id))
    now = datetime.now(timezone.utc)

    m1 = WorkspaceMember(
        id=uuid.uuid4(), workspace_id=ws.id, user_id=user.id,
        role=WorkspaceRole.OWNER, invited_by=None, joined_at=now,
    )
    await member_repo.add(m1)

    m2 = WorkspaceMember(
        id=uuid.uuid4(), workspace_id=ws.id, user_id=user.id,
        role=WorkspaceRole.EDITOR, invited_by=None, joined_at=now,
    )
    with pytest.raises(Exception):
        await member_repo.add(m2)


async def test_remove_member(db_session: AsyncSession):
    user_repo = PostgresUserRepository(db_session)
    ws_repo = PostgresWorkspaceRepository(db_session)
    member_repo = PostgresWorkspaceMemberRepository(db_session)

    owner = await user_repo.create(make_user())
    member_user = await user_repo.create(make_user())
    ws = await ws_repo.create(make_workspace(owner.id))
    now = datetime.now(timezone.utc)

    await member_repo.add(WorkspaceMember(
        id=uuid.uuid4(), workspace_id=ws.id, user_id=owner.id,
        role=WorkspaceRole.OWNER, invited_by=None, joined_at=now,
    ))
    await member_repo.add(WorkspaceMember(
        id=uuid.uuid4(), workspace_id=ws.id, user_id=member_user.id,
        role=WorkspaceRole.EDITOR, invited_by=owner.id, joined_at=now,
    ))

    await member_repo.remove(ws.id, member_user.id)
    found = await member_repo.get(ws.id, member_user.id)
    assert found is None
