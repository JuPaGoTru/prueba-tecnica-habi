import uuid

from app.application.exceptions import AccessDeniedError, NotFoundError
from app.domain.entities import WorkspaceRole
from app.domain.repositories import BudgetRepository, WorkspaceMemberRepository


class DeleteBudgetUseCase:
    def __init__(self, budget_repo: BudgetRepository, member_repo: WorkspaceMemberRepository):
        self._budget_repo = budget_repo
        self._member_repo = member_repo

    async def execute(self, budget_id: uuid.UUID, user_id: uuid.UUID) -> None:
        budget = await self._budget_repo.get_by_id(budget_id)
        if not budget:
            raise NotFoundError("Budget not found")

        member = await self._member_repo.get(budget.workspace_id, user_id)
        if not member or not member.role.has_minimum_role(WorkspaceRole.EDITOR):
            raise AccessDeniedError("Minimum role required: editor")

        await self._budget_repo.soft_delete(budget_id)
