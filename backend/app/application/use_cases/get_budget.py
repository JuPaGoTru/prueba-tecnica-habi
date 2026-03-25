import uuid

from app.application.dtos import BudgetOutputDTO
from app.application.exceptions import AccessDeniedError, NotFoundError
from app.domain.repositories import BudgetRepository, MovementRepository, WorkspaceMemberRepository


class GetBudgetUseCase:
    def __init__(
        self,
        budget_repo: BudgetRepository,
        member_repo: WorkspaceMemberRepository,
        movement_repo: MovementRepository,
    ):
        self._budget_repo = budget_repo
        self._member_repo = member_repo
        self._movement_repo = movement_repo

    async def execute(self, budget_id: uuid.UUID, user_id: uuid.UUID) -> BudgetOutputDTO:
        budget = await self._budget_repo.get_by_id(budget_id)
        if not budget:
            raise NotFoundError("Budget not found")

        member = await self._member_repo.get(budget.workspace_id, user_id)
        if not member:
            raise AccessDeniedError("You do not have access to this workspace")

        spent = await self._movement_repo.get_total_expenses(
            budget.workspace_id, budget.category, budget.period_month, budget.period_year
        )
        progress = (spent / budget.limit_amount * 100) if budget.limit_amount > 0 else 0.0

        return BudgetOutputDTO(
            **budget.__dict__,
            spent_amount=spent,
            progress_percentage=round(progress, 2),
        )
