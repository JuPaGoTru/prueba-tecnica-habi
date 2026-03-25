import uuid

from app.application.exceptions import AccessDeniedError, CannotModifyOwnerError, NotFoundError
from app.domain.entities import WorkspaceRole
from app.domain.repositories import WorkspaceMemberRepository, WorkspaceRepository


class RemoveMemberUseCase:
    def __init__(self, workspace_repo: WorkspaceRepository, member_repo: WorkspaceMemberRepository):
        self._workspace_repo = workspace_repo
        self._member_repo = member_repo

    async def execute(
        self, workspace_id: uuid.UUID, target_user_id: uuid.UUID, requester_id: uuid.UUID
    ) -> None:
        workspace = await self._workspace_repo.get_by_id(workspace_id)
        if not workspace:
            raise NotFoundError("Workspace not found")

        target_member = await self._member_repo.get(workspace_id, target_user_id)
        if not target_member:
            raise NotFoundError("Member not found in workspace")

        if target_member.role == WorkspaceRole.OWNER:
            raise CannotModifyOwnerError("The owner cannot be removed from the workspace")

        requester_member = await self._member_repo.get(workspace_id, requester_id)
        if not requester_member or not requester_member.role.can_manage_members():
            raise AccessDeniedError("Only owner or admin can remove members")

        await self._member_repo.remove(workspace_id, target_user_id)
