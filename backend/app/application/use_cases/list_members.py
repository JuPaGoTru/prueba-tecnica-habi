import uuid

from app.application.dtos import WorkspaceMemberOutputDTO
from app.application.exceptions import AccessDeniedError, NotFoundError
from app.domain.repositories import WorkspaceMemberRepository, WorkspaceRepository


class ListMembersUseCase:
    def __init__(self, workspace_repo: WorkspaceRepository, member_repo: WorkspaceMemberRepository):
        self._workspace_repo = workspace_repo
        self._member_repo = member_repo

    async def execute(self, workspace_id: uuid.UUID, user_id: uuid.UUID) -> list[WorkspaceMemberOutputDTO]:
        workspace = await self._workspace_repo.get_by_id(workspace_id)
        if not workspace:
            raise NotFoundError("Workspace not found")

        requester = await self._member_repo.get(workspace_id, user_id)
        if not requester:
            raise AccessDeniedError("You do not have access to this workspace")

        members = await self._member_repo.list_by_workspace(workspace_id)
        return [WorkspaceMemberOutputDTO(**m.__dict__) for m in members]
