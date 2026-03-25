import uuid

from app.application.dtos import UpdateWorkspaceInputDTO, WorkspaceOutputDTO
from app.application.exceptions import AccessDeniedError, NotFoundError
from app.domain.entities import WorkspaceRole
from app.domain.repositories import WorkspaceMemberRepository, WorkspaceRepository


class UpdateWorkspaceUseCase:
    def __init__(self, workspace_repo: WorkspaceRepository, member_repo: WorkspaceMemberRepository):
        self._workspace_repo = workspace_repo
        self._member_repo = member_repo

    async def execute(
        self, workspace_id: uuid.UUID, dto: UpdateWorkspaceInputDTO, user_id: uuid.UUID
    ) -> WorkspaceOutputDTO:
        workspace = await self._workspace_repo.get_by_id(workspace_id)
        if not workspace:
            raise NotFoundError("Workspace not found")

        member = await self._member_repo.get(workspace_id, user_id)
        if not member or not member.role.has_minimum_role(WorkspaceRole.ADMIN):
            raise AccessDeniedError("Only owner or admin can update the workspace")

        if dto.name is not None:
            workspace.name = dto.name
        if dto.description is not None:
            workspace.description = dto.description
        if dto.settings is not None:
            workspace.settings = dto.settings

        updated = await self._workspace_repo.update(workspace)
        return WorkspaceOutputDTO(**updated.__dict__)
