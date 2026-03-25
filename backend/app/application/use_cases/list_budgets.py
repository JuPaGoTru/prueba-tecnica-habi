import uuid

from app.application.dtos import BudgetListOutputDTO, BudgetOutputDTO
from app.application.exceptions import AccessDeniedError, NotFoundError
from app.domain.repositories import (
    BudgetRepository,
    MovementRepository,
    WorkspaceMemberRepository,
    WorkspaceRepository,
)


class ListBudgetsUseCase:
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

    async def execute(
        self,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        category: str | None = None,
        month: int | None = None,
        year: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> BudgetListOutputDTO:
        workspace = await self._workspace_repo.get_by_id(workspace_id)
        if not workspace:
            raise NotFoundError("Workspace not found")

        member = await self._member_repo.get(workspace_id, user_id)
        if not member:
            raise AccessDeniedError("You do not have access to this workspace")

        offset = (page - 1) * page_size
        budgets, total = await self._budget_repo.list_by_workspace(
            workspace_id, category, month, year, offset, page_size
        )

        items = []
        for budget in budgets:
            spent = await self._movement_repo.get_total_expenses(
                budget.workspace_id, budget.category, budget.period_month, budget.period_year
            )
            progress = (spent / budget.limit_amount * 100) if budget.limit_amount > 0 else 0.0
            items.append(BudgetOutputDTO(
                **budget.__dict__,
                spent_amount=spent,
                progress_percentage=round(progress, 2),
            ))

        return BudgetListOutputDTO(items=items, total=total, page=page, page_size=page_size)
