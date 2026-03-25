import pytest
from httpx import AsyncClient


async def test_register_success(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json={
        "email": "alice@example.com",
        "password": "StrongPass1!",
        "full_name": "Alice",
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_register_duplicate_email(client: AsyncClient):
    payload = {"email": "dup_e2e@example.com", "password": "StrongPass1!"}
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


async def test_login_success(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "bob@example.com",
        "password": "StrongPass1!",
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "bob@example.com",
        "password": "StrongPass1!",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "carol@example.com",
        "password": "StrongPass1!",
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "carol@example.com",
        "password": "WrongPass99!",
    })
    assert response.status_code == 401


async def test_login_unknown_email(client: AsyncClient):
    response = await client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com",
        "password": "AnyPass1!",
    })
    assert response.status_code == 401


async def test_refresh_token(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "dave@example.com",
        "password": "StrongPass1!",
    })
    login = await client.post("/api/v1/auth/login", json={
        "email": "dave@example.com",
        "password": "StrongPass1!",
    })
    refresh_token = login.json()["refresh_token"]

    response = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_refresh_invalid_token(client: AsyncClient):
    response = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": "not.a.valid.token",
    })
    assert response.status_code == 401
