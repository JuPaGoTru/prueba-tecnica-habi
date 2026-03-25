import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime, timezone

from app.application.dtos import LoginInputDTO
from app.application.exceptions import InactiveUserError, InvalidCredentialsError
from app.application.use_cases.login_user import LoginUserUseCase
from app.domain.entities import User
from app.infrastructure.password_service import hash_password


def make_user(password: str = "Secure1Pass", is_active: bool = True) -> User:
    return User(
        id=uuid4(),
        email="user@example.com",
        hashed_password=hash_password(password),
        full_name=None,
        is_active=is_active,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def repo():
    return AsyncMock()


async def test_login_valid_credentials_returns_tokens(repo):
    repo.get_by_email = AsyncMock(return_value=make_user())
    dto = LoginInputDTO(email="user@example.com", password="Secure1Pass")
    result = await LoginUserUseCase(repo).execute(dto)

    assert result.access_token
    assert result.refresh_token


async def test_login_wrong_password_raises(repo):
    repo.get_by_email = AsyncMock(return_value=make_user())
    dto = LoginInputDTO(email="user@example.com", password="WrongPass1")

    with pytest.raises(InvalidCredentialsError):
        await LoginUserUseCase(repo).execute(dto)


async def test_login_user_not_found_raises(repo):
    repo.get_by_email = AsyncMock(return_value=None)
    dto = LoginInputDTO(email="ghost@example.com", password="Secure1Pass")

    with pytest.raises(InvalidCredentialsError):
        await LoginUserUseCase(repo).execute(dto)


async def test_login_inactive_user_raises(repo):
    repo.get_by_email = AsyncMock(return_value=make_user(is_active=False))
    dto = LoginInputDTO(email="user@example.com", password="Secure1Pass")

    with pytest.raises(InactiveUserError):
        await LoginUserUseCase(repo).execute(dto)
