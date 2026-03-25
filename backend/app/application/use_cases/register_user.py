import uuid
from datetime import datetime, timezone

from app.application.dtos import RegisterInputDTO, TokenOutputDTO
from app.application.exceptions import EmailAlreadyExistsError
from app.domain.entities import User
from app.domain.repositories import UserRepository
from app.domain.value_objects import Email, Password
from app.infrastructure.jwt_service import create_access_token, create_refresh_token
from app.infrastructure.password_service import hash_password


class RegisterUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self._repo = user_repository

    async def execute(self, dto: RegisterInputDTO) -> TokenOutputDTO:
        email = Email(dto.email)
        Password(dto.password)  # validates complexity rules

        existing = await self._repo.get_by_email(email.value)
        if existing:
            raise EmailAlreadyExistsError(f"Email {email.value} is already registered")

        now = datetime.now(timezone.utc)
        user = User(
            id=uuid.uuid4(),
            email=email.value,
            hashed_password=hash_password(dto.password),
            full_name=dto.full_name,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        created = await self._repo.create(user)

        return TokenOutputDTO(
            access_token=create_access_token(created.id),
            refresh_token=create_refresh_token(created.id),
        )
