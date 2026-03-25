import uuid

from app.application.dtos import UpdateMemberRoleInputDTO, WorkspaceMemberOutputDTO
from app.application.exceptions import AccessDeniedError, CannotModifyOwnerError, NotFoundError
from app.domain.entities import WorkspaceRole
from app.domain.repositories import WorkspaceMemberRepository, WorkspaceRepository


class UpdateMemberRoleUseCase:
    def __init__(self, workspace_repo: WorkspaceRepository, member_repo: WorkspaceMemberRepository):
        self._workspace_repo = workspace_repo
        self._member_repo = member_repo

    async def execute(
        self,
        workspace_id: uuid.UUID,
        target_user_id: uuid.UUID,
        dto: UpdateMemberRoleInputDTO,
        requester_id: uuid.UUID,
    ) -> WorkspaceMemberOutputDTO:
        workspace = await self._workspace_repo.get_by_id(workspace_id)
        if not workspace:
            raise NotFoundError("Workspace not found")

        target_member = await self._member_repo.get(workspace_id, target_user_id)
        if not target_member:
            raise NotFoundError("Member not found in workspace")

        if target_member.role == WorkspaceRole.OWNER:
            raise CannotModifyOwnerError("Cannot change the owner's role")

        if dto.role == WorkspaceRole.OWNER:
            raise CannotModifyOwnerError("Cannot assign owner role")

        requester_member = await self._member_repo.get(workspace_id, requester_id)
        if not requester_member or not requester_member.role.can_manage_members():
            raise AccessDeniedError("Only owner or admin can update member roles")

        updated = await self._member_repo.update_role(workspace_id, target_user_id, dto.role)
        return WorkspaceMemberOutputDTO(**updated.__dict__)
