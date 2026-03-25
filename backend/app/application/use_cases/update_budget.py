import uuid

from app.application.dtos import BudgetOutputDTO, UpdateBudgetInputDTO
from app.application.exceptions import AccessDeniedError, NotFoundError
from app.domain.entities import WorkspaceRole
from app.domain.repositories import BudgetRepository, MovementRepository, WorkspaceMemberRepository


class UpdateBudgetUseCase:
    def __init__(
        self,
        budget_repo: BudgetRepository,
        member_repo: WorkspaceMemberRepository,
        movement_repo: MovementRepository,
    ):
        self._budget_repo = budget_repo
        self._member_repo = member_repo
        self._movement_repo = movement_repo

    async def execute(
        self, budget_id: uuid.UUID, dto: UpdateBudgetInputDTO, user_id: uuid.UUID
    ) -> BudgetOutputDTO:
        if dto.limit_amount <= 0:
            raise ValueError("limit_amount must be greater than 0")

        budget = await self._budget_repo.get_by_id(budget_id)
        if not budget:
            raise NotFoundError("Budget not found")

        member = await self._member_repo.get(budget.workspace_id, user_id)
        if not member or not member.role.has_minimum_role(WorkspaceRole.EDITOR):
            raise AccessDeniedError("Minimum role required: editor")

        budget.limit_amount = dto.limit_amount
        updated = await self._budget_repo.update(budget)

        spent = await self._movement_repo.get_total_expenses(
            updated.workspace_id, updated.category, updated.period_month, updated.period_year
        )
        progress = (spent / updated.limit_amount * 100) if updated.limit_amount > 0 else 0.0

        return BudgetOutputDTO(
            **updated.__dict__,
            spent_amount=spent,
            progress_percentage=round(progress, 2),
        )
