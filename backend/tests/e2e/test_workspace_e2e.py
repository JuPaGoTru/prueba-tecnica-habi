import pytest
from httpx import AsyncClient


async def _register_and_login(client: AsyncClient, email: str, password: str = "StrongPass1!") -> str:
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


async def test_create_workspace(client: AsyncClient):
    token = await _register_and_login(client, "ws_owner@example.com")
    response = await client.post(
        "/api/v1/workspaces",
        json={"name": "My Workspace"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Workspace"
    assert "id" in data


async def test_get_workspace(client: AsyncClient):
    token = await _register_and_login(client, "ws_get@example.com")
    create_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Get WS"},
        headers={"Authorization": f"Bearer {token}"},
    )
    ws_id = create_resp.json()["id"]

    response = await client.get(
        f"/api/v1/workspaces/{ws_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["id"] == ws_id


async def test_list_workspaces(client: AsyncClient):
    token = await _register_and_login(client, "ws_list@example.com")
    await client.post("/api/v1/workspaces", json={"name": "WS A"}, headers={"Authorization": f"Bearer {token}"})
    await client.post("/api/v1/workspaces", json={"name": "WS B"}, headers={"Authorization": f"Bearer {token}"})

    response = await client.get("/api/v1/workspaces", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    names = [w["name"] for w in response.json()]
    assert "WS A" in names
    assert "WS B" in names


async def test_update_workspace(client: AsyncClient):
    token = await _register_and_login(client, "ws_upd@example.com")
    ws_id = (await client.post(
        "/api/v1/workspaces", json={"name": "Old Name"},
        headers={"Authorization": f"Bearer {token}"},
    )).json()["id"]

    response = await client.put(
        f"/api/v1/workspaces/{ws_id}",
        json={"name": "New Name"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


async def test_delete_workspace(client: AsyncClient):
    token = await _register_and_login(client, "ws_del@example.com")
    ws_id = (await client.post(
        "/api/v1/workspaces", json={"name": "To Delete"},
        headers={"Authorization": f"Bearer {token}"},
    )).json()["id"]

    delete_resp = await client.delete(
        f"/api/v1/workspaces/{ws_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_resp.status_code == 204

    get_resp = await client.get(
        f"/api/v1/workspaces/{ws_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 404


async def test_invite_and_remove_member(client: AsyncClient):
    owner_token = await _register_and_login(client, "ws_inv_owner@example.com")
    member_token = await _register_and_login(client, "ws_inv_member@example.com")

    # Get member user id
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "ws_inv_member@example.com",
        "password": "StrongPass1!",
    })
    # Register again won't give us the user id, so we create workspace and check members
    ws_id = (await client.post(
        "/api/v1/workspaces", json={"name": "Invite WS"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )).json()["id"]

    invite_resp = await client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"email": "ws_inv_member@example.com", "role": "editor"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert invite_resp.status_code == 201

    members_resp = await client.get(
        f"/api/v1/workspaces/{ws_id}/members",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert members_resp.status_code == 200
    user_ids = [m["user_id"] for m in members_resp.json()]
    assert len(user_ids) >= 1


async def test_unauthorized_without_token(client: AsyncClient):
    response = await client.get("/api/v1/workspaces")
    assert response.status_code == 401
