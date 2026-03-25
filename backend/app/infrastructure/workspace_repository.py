from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Workspace, WorkspaceMember, WorkspaceRole
from app.domain.repositories import WorkspaceMemberRepository, WorkspaceRepository
from app.infrastructure.models import WorkspaceMemberModel, WorkspaceModel


def _to_workspace(m: WorkspaceModel) -> Workspace:
    return Workspace(
        id=m.id,
        name=m.name,
        description=m.description,
        owner_id=m.owner_id,
        settings=m.settings,
        is_active=m.is_active,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _to_member(m: WorkspaceMemberModel) -> WorkspaceMember:
    return WorkspaceMember(
        id=m.id,
        workspace_id=m.workspace_id,
        user_id=m.user_id,
        role=WorkspaceRole(m.role),
        invited_by=m.invited_by,
        joined_at=m.joined_at,
    )


class PostgresWorkspaceRepository(WorkspaceRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, workspace: Workspace) -> Workspace:
        model = WorkspaceModel(
            id=workspace.id,
            name=workspace.name,
            description=workspace.description,
            owner_id=workspace.owner_id,
            settings=workspace.settings,
            is_active=workspace.is_active,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_workspace(model)

    async def get_by_id(self, workspace_id: UUID) -> Workspace | None:
        result = await self._session.execute(
            select(WorkspaceModel).where(WorkspaceModel.id == workspace_id, WorkspaceModel.is_active == True)
        )
        model = result.scalar_one_or_none()
        return _to_workspace(model) if model else None

    async def list_by_user(self, user_id: UUID) -> list[Workspace]:
        result = await self._session.execute(
            select(WorkspaceModel)
            .join(WorkspaceMemberModel, WorkspaceMemberModel.workspace_id == WorkspaceModel.id)
            .where(WorkspaceMemberModel.user_id == user_id, WorkspaceModel.is_active == True)
        )
        return [_to_workspace(m) for m in result.scalars().all()]

    async def update(self, workspace: Workspace) -> Workspace:
        result = await self._session.execute(
            select(WorkspaceModel).where(WorkspaceModel.id == workspace.id)
        )
        model = result.scalar_one()
        model.name = workspace.name
        model.description = workspace.description
        model.settings = workspace.settings
        await self._session.flush()
        return _to_workspace(model)

    async def delete(self, workspace_id: UUID) -> None:
        result = await self._session.execute(
            select(WorkspaceModel).where(WorkspaceModel.id == workspace_id)
        )
        model = result.scalar_one()
        model.is_active = False
        await self._session.flush()


class PostgresWorkspaceMemberRepository(WorkspaceMemberRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, member: WorkspaceMember) -> WorkspaceMember:
        model = WorkspaceMemberModel(
            id=member.id,
            workspace_id=member.workspace_id,
            user_id=member.user_id,
            role=member.role.value,
            invited_by=member.invited_by,
            joined_at=member.joined_at,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_member(model)

    async def get(self, workspace_id: UUID, user_id: UUID) -> WorkspaceMember | None:
        result = await self._session.execute(
            select(WorkspaceMemberModel).where(
                WorkspaceMemberModel.workspace_id == workspace_id,
                WorkspaceMemberModel.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        return _to_member(model) if model else None

    async def list_by_workspace(self, workspace_id: UUID) -> list[WorkspaceMember]:
        result = await self._session.execute(
            select(WorkspaceMemberModel).where(WorkspaceMemberModel.workspace_id == workspace_id)
        )
        return [_to_member(m) for m in result.scalars().all()]

    async def update_role(self, workspace_id: UUID, user_id: UUID, role: WorkspaceRole) -> WorkspaceMember:
        result = await self._session.execute(
            select(WorkspaceMemberModel).where(
                WorkspaceMemberModel.workspace_id == workspace_id,
                WorkspaceMemberModel.user_id == user_id,
            )
        )
        model = result.scalar_one()
        model.role = role.value
        await self._session.flush()
        return _to_member(model)

    async def remove(self, workspace_id: UUID, user_id: UUID) -> None:
        result = await self._session.execute(
            select(WorkspaceMemberModel).where(
                WorkspaceMemberModel.workspace_id == workspace_id,
                WorkspaceMemberModel.user_id == user_id,
            )
        )
        model = result.scalar_one()
        await self._session.delete(model)
        await self._session.flush()
