import uuid
from datetime import datetime, timezone

from app.application.dtos import CreateWorkspaceInputDTO, WorkspaceOutputDTO
from app.application.exceptions import NotFoundError
from app.domain.entities import Workspace, WorkspaceMember, WorkspaceRole
from app.domain.repositories import UserRepository, WorkspaceMemberRepository, WorkspaceRepository


class CreateWorkspaceUseCase:
    def __init__(
        self,
        workspace_repo: WorkspaceRepository,
        member_repo: WorkspaceMemberRepository,
        user_repo: UserRepository,
    ):
        self._workspace_repo = workspace_repo
        self._member_repo = member_repo
        self._user_repo = user_repo

    async def execute(self, dto: CreateWorkspaceInputDTO, owner_id: uuid.UUID) -> WorkspaceOutputDTO:
        owner = await self._user_repo.get_by_id(owner_id)
        if not owner or not owner.is_active:
            raise NotFoundError("User not found or inactive")

        now = datetime.now(timezone.utc)
        workspace = Workspace(
            id=uuid.uuid4(),
            name=dto.name,
            description=dto.description,
            owner_id=owner_id,
            settings=dto.settings,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        created = await self._workspace_repo.create(workspace)

        owner_member = WorkspaceMember(
            id=uuid.uuid4(),
            workspace_id=created.id,
            user_id=owner_id,
            role=WorkspaceRole.OWNER,
            invited_by=None,
            joined_at=now,
        )
        await self._member_repo.add(owner_member)

        return WorkspaceOutputDTO(**created.__dict__)
