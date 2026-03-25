from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.exceptions import InvalidTokenError
from app.domain.entities import User
from app.domain.repositories import UserRepository
from app.infrastructure.database import get_db
from app.infrastructure.jwt_service import decode_token
from app.infrastructure.user_repository import PostgresUserRepository

bearer_scheme = HTTPBearer()


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return PostgresUserRepository(db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    repo: UserRepository = Depends(get_user_repository),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise credentials_exception

    if payload.get("type") != "access":
        raise credentials_exception

    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception

    user = await repo.get_by_id(UUID(user_id))
    if not user or not user.is_active:
        raise credentials_exception

    return user
