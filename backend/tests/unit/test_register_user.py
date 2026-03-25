import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from app.application.dtos import RegisterInputDTO
from app.application.exceptions import EmailAlreadyExistsError
from app.application.use_cases.register_user import RegisterUserUseCase
from app.domain.entities import User


def make_user(**kwargs) -> User:
    defaults = dict(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed",
        full_name=None,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    return User(**{**defaults, **kwargs})


@pytest.fixture
def repo():
    mock = AsyncMock()
    mock.get_by_email = AsyncMock(return_value=None)
    mock.create = AsyncMock(side_effect=lambda user: user)
    return mock


async def test_register_returns_tokens(repo):
    dto = RegisterInputDTO(email="new@example.com", password="Secure1Pass")
    result = await RegisterUserUseCase(repo).execute(dto)

    assert result.access_token
    assert result.refresh_token
    assert result.token_type == "bearer"
    repo.create.assert_called_once()


async def test_register_duplicate_email_raises(repo):
    repo.get_by_email = AsyncMock(return_value=make_user())
    dto = RegisterInputDTO(email="existing@example.com", password="Secure1Pass")

    with pytest.raises(EmailAlreadyExistsError):
        await RegisterUserUseCase(repo).execute(dto)


async def test_register_invalid_password_raises(repo):
    dto = RegisterInputDTO(email="new@example.com", password="weak")

    with pytest.raises(ValueError):
        await RegisterUserUseCase(repo).execute(dto)
