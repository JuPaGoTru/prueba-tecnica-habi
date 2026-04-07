import uuid
from datetime import datetime, timezone

from app.application.dtos import CreateMovementInputDTO, MovementOutputDTO
from app.application.exceptions import AccessDeniedError, NotFoundError
from app.domain.entities import Movement
from app.domain.repositories import MovementRepository, WorkspaceMemberRepository, WorkspaceRepository
from app.domain.value_objects import BudgetPeriod


class CreateMovementUseCase:
    def __init__(
        self,
        movement_repo: MovementRepository,
        workspace_repo: WorkspaceRepository,
        member_repo: WorkspaceMemberRepository,
    ):
        self._movement_repo = movement_repo
        self._workspace_repo = workspace_repo
        self._member_repo = member_repo

    async def execute(self, dto: CreateMovementInputDTO, user_id: uuid.UUID) -> MovementOutputDTO:
        if dto.amount <= 0:
            raise ValueError("amount must be greater than 0")
        if not dto.category or not dto.category.strip():
            raise ValueError("category must not be empty")

        BudgetPeriod(dto.period_month, dto.period_year)

        workspace = await self._workspace_repo.get_by_id(dto.workspace_id)
        if not workspace:
            raise NotFoundError("Workspace not found")

        member = await self._member_repo.get(dto.workspace_id, user_id)
        if not member:
            raise AccessDeniedError("You are not a member of this workspace")

        movement = Movement(
            id=uuid.uuid4(),
            workspace_id=dto.workspace_id,
            user_id=user_id,
            category=dto.category.strip(),
            amount=dto.amount,
            type=dto.type,
            period_month=dto.period_month,
            period_year=dto.period_year,
            created_at=datetime.now(timezone.utc),
        )
        created = await self._movement_repo.create(movement)
        return MovementOutputDTO(**created.__dict__)
