import uuid

from app.application.dtos import WorkspaceOutputDTO
from app.domain.repositories import WorkspaceRepository


class ListWorkspacesUseCase:
    def __init__(self, workspace_repo: WorkspaceRepository):
        self._workspace_repo = workspace_repo

    async def execute(self, user_id: uuid.UUID) -> list[WorkspaceOutputDTO]:
        workspaces = await self._workspace_repo.list_by_user(user_id)
        return [WorkspaceOutputDTO(**w.__dict__) for w in workspaces]
