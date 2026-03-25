import uuid

from app.application.exceptions import AccessDeniedError, NotFoundError
from app.domain.entities import WorkspaceRole
from app.domain.repositories import WorkspaceMemberRepository, WorkspaceRepository


class DeleteWorkspaceUseCase:
    def __init__(self, workspace_repo: WorkspaceRepository, member_repo: WorkspaceMemberRepository):
        self._workspace_repo = workspace_repo
        self._member_repo = member_repo

    async def execute(self, workspace_id: uuid.UUID, user_id: uuid.UUID) -> None:
        workspace = await self._workspace_repo.get_by_id(workspace_id)
        if not workspace:
            raise NotFoundError("Workspace not found")

        member = await self._member_repo.get(workspace_id, user_id)
        if not member or member.role != WorkspaceRole.OWNER:
            raise AccessDeniedError("Only the owner can delete the workspace")

        await self._workspace_repo.delete(workspace_id)
