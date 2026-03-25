from uuid import UUID

from jose import JWTError

from app.application.dtos import TokenOutputDTO
from app.application.exceptions import InvalidTokenError, InactiveUserError
from app.domain.repositories import UserRepository
from app.infrastructure.jwt_service import create_access_token, create_refresh_token, decode_token


class RefreshTokenUseCase:
    def __init__(self, user_repository: UserRepository):
        self._repo = user_repository

    async def execute(self, refresh_token: str) -> TokenOutputDTO:
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            raise InvalidTokenError("Invalid or expired refresh token")

        if payload.get("type") != "refresh":
            raise InvalidTokenError("Token is not a refresh token")

        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenError("Token missing subject")

        user = await self._repo.get_by_id(UUID(user_id))
        if not user:
            raise InvalidTokenError("User not found")
        if not user.is_active:
            raise InactiveUserError("User account is inactive")

        return TokenOutputDTO(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )
