import uuid
from datetime import datetime, timezone

from app.application.dtos import InviteMemberInputDTO, WorkspaceMemberOutputDTO
from app.application.exceptions import (
    AccessDeniedError,
    AlreadyMemberError,
    CannotModifyOwnerError,
    NotFoundError,
)
from app.domain.entities import WorkspaceMember, WorkspaceRole
from app.domain.repositories import UserRepository, WorkspaceMemberRepository, WorkspaceRepository


class InviteMemberUseCase:
    def __init__(
        self,
        workspace_repo: WorkspaceRepository,
        member_repo: WorkspaceMemberRepository,
        user_repo: UserRepository,
    ):
        self._workspace_repo = workspace_repo
        self._member_repo = member_repo
        self._user_repo = user_repo

    async def execute(
        self, workspace_id: uuid.UUID, dto: InviteMemberInputDTO, inviter_id: uuid.UUID
    ) -> WorkspaceMemberOutputDTO:
        workspace = await self._workspace_repo.get_by_id(workspace_id)
        if not workspace:
            raise NotFoundError("Workspace not found")

        inviter_member = await self._member_repo.get(workspace_id, inviter_id)
        if not inviter_member or not inviter_member.role.can_manage_members():
            raise AccessDeniedError("Only owner or admin can invite members")

        if dto.role == WorkspaceRole.OWNER:
            raise CannotModifyOwnerError("Cannot assign owner role via invitation")

        target_user = await self._user_repo.get_by_email(dto.email.lower().strip())
        if not target_user or not target_user.is_active:
            raise NotFoundError("User not found")

        existing = await self._member_repo.get(workspace_id, target_user.id)
        if existing:
            raise AlreadyMemberError("User is already a member of this workspace")

        member = WorkspaceMember(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            user_id=target_user.id,
            role=dto.role,
            invited_by=inviter_id,
            joined_at=datetime.now(timezone.utc),
        )
        created = await self._member_repo.add(member)
        return WorkspaceMemberOutputDTO(**created.__dict__)
