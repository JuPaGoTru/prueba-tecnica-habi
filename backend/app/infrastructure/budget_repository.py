from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Budget, Movement, MovementType
from app.domain.repositories import BudgetRepository, MovementRepository
from app.infrastructure.models import BudgetModel, MovementModel


def _to_budget(m: BudgetModel) -> Budget:
    return Budget(
        id=m.id,
        user_id=m.user_id,
        workspace_id=m.workspace_id,
        category=m.category,
        limit_amount=m.limit_amount,
        period_month=m.period_month,
        period_year=m.period_year,
        is_active=m.is_active,
        created_at=m.created_at,
        updated_at=m.updated_at,
        deleted_at=m.deleted_at,
    )


class PostgresBudgetRepository(BudgetRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, budget: Budget) -> Budget:
        model = BudgetModel(
            id=budget.id,
            user_id=budget.user_id,
            workspace_id=budget.workspace_id,
            category=budget.category,
            limit_amount=budget.limit_amount,
            period_month=budget.period_month,
            period_year=budget.period_year,
            is_active=budget.is_active,
            created_at=budget.created_at,
            updated_at=budget.updated_at,
            deleted_at=budget.deleted_at,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_budget(model)

    async def get_by_id(self, budget_id: UUID) -> Budget | None:
        result = await self._session.execute(
            select(BudgetModel).where(BudgetModel.id == budget_id, BudgetModel.deleted_at.is_(None))
        )
        model = result.scalar_one_or_none()
        return _to_budget(model) if model else None

    async def get_by_period(
        self, workspace_id: UUID, category: str, month: int, year: int
    ) -> Budget | None:
        result = await self._session.execute(
            select(BudgetModel).where(
                BudgetModel.workspace_id == workspace_id,
                BudgetModel.category == category,
                BudgetModel.period_month == month,
                BudgetModel.period_year == year,
                BudgetModel.deleted_at.is_(None),
            )
        )
        model = result.scalar_one_or_none()
        return _to_budget(model) if model else None

    async def list_by_workspace(
        self,
        workspace_id: UUID,
        category: str | None,
        month: int | None,
        year: int | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Budget], int]:
        base_query = select(BudgetModel).where(
            BudgetModel.workspace_id == workspace_id,
            BudgetModel.deleted_at.is_(None),
        )
        if category:
            base_query = base_query.where(BudgetModel.category == category)
        if month:
            base_query = base_query.where(BudgetModel.period_month == month)
        if year:
            base_query = base_query.where(BudgetModel.period_year == year)

        count_result = await self._session.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = count_result.scalar_one()

        result = await self._session.execute(base_query.offset(offset).limit(limit))
        budgets = [_to_budget(m) for m in result.scalars().all()]
        return budgets, total

    async def update(self, budget: Budget) -> Budget:
        result = await self._session.execute(
            select(BudgetModel).where(BudgetModel.id == budget.id)
        )
        model = result.scalar_one()
        model.limit_amount = budget.limit_amount
        await self._session.flush()
        return _to_budget(model)

    async def soft_delete(self, budget_id: UUID) -> None:
        result = await self._session.execute(
            select(BudgetModel).where(BudgetModel.id == budget_id)
        )
        model = result.scalar_one()
        model.deleted_at = datetime.now(timezone.utc)
        model.is_active = False
        await self._session.flush()


class PostgresMovementRepository(MovementRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_total_expenses(
        self, workspace_id: UUID, category: str, month: int, year: int
    ) -> float:
        result = await self._session.execute(
            select(func.coalesce(func.sum(MovementModel.amount), 0.0)).where(
                MovementModel.workspace_id == workspace_id,
                MovementModel.category == category,
                MovementModel.period_month == month,
                MovementModel.period_year == year,
                MovementModel.type == MovementType.EXPENSE.value,
            )
        )
        return float(result.scalar_one())
