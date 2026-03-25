import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import User
from app.infrastructure.user_repository import PostgresUserRepository


def make_user(email: str = None) -> User:
    now = datetime.now(timezone.utc)
    return User(
        id=uuid.uuid4(),
        email=email or f"user_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="hashed",
        full_name="Test User",
        is_active=True,
        created_at=now,
        updated_at=now,
    )


async def test_create_and_get_by_email(db_session: AsyncSession):
    repo = PostgresUserRepository(db_session)
    user = make_user("integration@example.com")

    created = await repo.create(user)
    assert created.id == user.id
    assert created.email == "integration@example.com"

    found = await repo.get_by_email("integration@example.com")
    assert found is not None
    assert found.id == created.id


async def test_get_by_id(db_session: AsyncSession):
    repo = PostgresUserRepository(db_session)
    user = make_user()
    created = await repo.create(user)

    found = await repo.get_by_id(created.id)
    assert found is not None
    assert found.email == created.email


async def test_get_by_email_not_found(db_session: AsyncSession):
    repo = PostgresUserRepository(db_session)
    result = await repo.get_by_email("nonexistent@example.com")
    assert result is None


async def test_get_by_id_not_found(db_session: AsyncSession):
    repo = PostgresUserRepository(db_session)
    result = await repo.get_by_id(uuid.uuid4())
    assert result is None


async def test_duplicate_email_raises(db_session: AsyncSession):
    repo = PostgresUserRepository(db_session)
    user = make_user("dup@example.com")
    await repo.create(user)

    duplicate = make_user("dup@example.com")
    with pytest.raises(Exception):
        await repo.create(duplicate)
