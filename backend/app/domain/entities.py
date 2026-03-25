from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID


@dataclass
class User:
    id: UUID
    email: str
    hashed_password: str
    full_name: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class WorkspaceRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"

    def can_manage_members(self) -> bool:
        return self in (WorkspaceRole.OWNER, WorkspaceRole.ADMIN)

    def can_edit_resources(self) -> bool:
        return self in (WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.EDITOR)

    def has_minimum_role(self, required: "WorkspaceRole") -> bool:
        hierarchy = [WorkspaceRole.VIEWER, WorkspaceRole.EDITOR, WorkspaceRole.ADMIN, WorkspaceRole.OWNER]
        return hierarchy.index(self) >= hierarchy.index(required)


@dataclass
class Workspace:
    id: UUID
    name: str
    description: str | None
    owner_id: UUID
    settings: dict | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class WorkspaceMember:
    id: UUID
    workspace_id: UUID
    user_id: UUID
    role: WorkspaceRole
    invited_by: UUID | None
    joined_at: datetime


class MovementType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


@dataclass
class Budget:
    id: UUID
    user_id: UUID
    workspace_id: UUID
    category: str
    limit_amount: float
    period_month: int   # 1-12
    period_year: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


@dataclass
class Movement:
    id: UUID
    workspace_id: UUID
    user_id: UUID
    category: str
    amount: float
    type: MovementType
    period_month: int
    period_year: int
    created_at: datetime
