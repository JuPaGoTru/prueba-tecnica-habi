from app.application.dtos import LoginInputDTO, TokenOutputDTO
from app.application.exceptions import InactiveUserError, InvalidCredentialsError
from app.domain.repositories import UserRepository
from app.infrastructure.jwt_service import create_access_token, create_refresh_token
from app.infrastructure.password_service import verify_password


class LoginUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self._repo = user_repository

    async def execute(self, dto: LoginInputDTO) -> TokenOutputDTO:
        user = await self._repo.get_by_email(dto.email.lower().strip())
        if not user or not verify_password(dto.password, user.hashed_password):
            raise InvalidCredentialsError("Invalid email or password")

        if not user.is_active:
            raise InactiveUserError("User account is inactive")

        return TokenOutputDTO(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )
