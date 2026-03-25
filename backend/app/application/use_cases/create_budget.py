import uuid
from datetime import datetime, timezone

from app.application.dtos import BudgetOutputDTO, CreateBudgetInputDTO
from app.application.exceptions import AccessDeniedError, ConflictError, NotFoundError
from app.domain.entities import Budget, WorkspaceRole
from app.domain.repositories import (
    BudgetRepository,
    MovementRepository,
    WorkspaceMemberRepository,
    WorkspaceRepository,
)
from app.domain.value_objects import BudgetPeriod


class CreateBudgetUseCase:
    def __init__(
        self,
        budget_repo: BudgetRepository,
        workspace_repo: WorkspaceRepository,
        member_repo: WorkspaceMemberRepository,
        movement_repo: MovementRepository,
    ):
        self._budget_repo = budget_repo
        self._workspace_repo = workspace_repo
        self._member_repo = member_repo
        self._movement_repo = movement_repo

    async def execute(self, dto: CreateBudgetInputDTO, user_id: uuid.UUID) -> BudgetOutputDTO:
        BudgetPeriod(dto.period_month, dto.period_year)  # validates month/year
        if dto.limit_amount <= 0:
            raise ValueError("limit_amount must be greater than 0")
        if not dto.category or not dto.category.strip():
            raise ValueError("category must not be empty")

        workspace = await self._workspace_repo.get_by_id(dto.workspace_id)
        if not workspace:
            raise NotFoundError("Workspace not found")

        member = await self._member_repo.get(dto.workspace_id, user_id)
        if not member or not member.role.has_minimum_role(WorkspaceRole.VIEWER):
            raise AccessDeniedError("You do not have access to this workspace")

        existing = await self._budget_repo.get_by_period(
            dto.workspace_id, dto.category.strip(), dto.period_month, dto.period_year
        )
        if existing:
            raise ConflictError(
                f"A budget for category '{dto.category}' in {dto.period_month}/{dto.period_year} already exists"
            )

        now = datetime.now(timezone.utc)
        budget = Budget(
            id=uuid.uuid4(),
            user_id=user_id,
            workspace_id=dto.workspace_id,
            category=dto.category.strip(),
            limit_amount=dto.limit_amount,
            period_month=dto.period_month,
            period_year=dto.period_year,
            is_active=True,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )
        created = await self._budget_repo.create(budget)

        spent = await self._movement_repo.get_total_expenses(
            created.workspace_id, created.category, created.period_month, created.period_year
        )
        progress = (spent / created.limit_amount * 100) if created.limit_amount > 0 else 0.0

        return BudgetOutputDTO(
            **created.__dict__,
            spent_amount=spent,
            progress_percentage=round(progress, 2),
        )
