import uuid

from app.application.dtos import MovementOutputDTO
from app.application.exceptions import AccessDeniedError, NotFoundError
from app.domain.repositories import MovementRepository, WorkspaceMemberRepository, WorkspaceRepository


class ListMovementsUseCase:
    def __init__(
        self,
        movement_repo: MovementRepository,
        workspace_repo: WorkspaceRepository,
        member_repo: WorkspaceMemberRepository,
    ):
        self._movement_repo = movement_repo
        self._workspace_repo = workspace_repo
        self._member_repo = member_repo

    async def execute(
        self,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        category: str | None = None,
        month: int | None = None,
        year: int | None = None,
    ) -> list[MovementOutputDTO]:
        workspace = await self._workspace_repo.get_by_id(workspace_id)
        if not workspace:
            raise NotFoundError("Workspace not found")

        member = await self._member_repo.get(workspace_id, user_id)
        if not member:
            raise AccessDeniedError("You are not a member of this workspace")

        movements = await self._movement_repo.list_by_workspace(workspace_id, category, month, year)
        return [MovementOutputDTO(**m.__dict__) for m in movements]
