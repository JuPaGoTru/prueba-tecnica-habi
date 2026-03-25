from uuid import UUID
from pydantic import BaseModel, EmailStr


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
