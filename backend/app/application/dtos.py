from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.domain.entities import WorkspaceRole


# --- Auth ---

class RegisterInputDTO(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class LoginInputDTO(BaseModel):
    email: EmailStr
    password: str


class TokenOutputDTO(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOutputDTO(BaseModel):
    id: UUID
    email: str
    full_name: str | None
    is_active: bool


# --- Workspace ---

class CreateWorkspaceInputDTO(BaseModel):
    name: str
    description: str | None = None
    settings: dict | None = None


class UpdateWorkspaceInputDTO(BaseModel):
    name: str | None = None
    description: str | None = None
    settings: dict | None = None


class WorkspaceOutputDTO(BaseModel):
    id: UUID
    name: str
    description: str | None
    owner_id: UUID
    settings: dict | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class InviteMemberInputDTO(BaseModel):
    email: str
    role: WorkspaceRole = WorkspaceRole.VIEWER


class UpdateMemberRoleInputDTO(BaseModel):
    role: WorkspaceRole


class WorkspaceMemberOutputDTO(BaseModel):
    id: UUID
    workspace_id: UUID
    user_id: UUID
    role: WorkspaceRole
    invited_by: UUID | None
    joined_at: datetime
