import pytest
from httpx import AsyncClient


async def _setup(client: AsyncClient, email: str) -> tuple[str, str]:
    """Register user, create workspace, return (token, workspace_id)."""
    await client.post("/api/v1/auth/register", json={"email": email, "password": "StrongPass1!"})
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "StrongPass1!"})
    token = resp.json()["access_token"]
    ws_resp = await client.post(
        "/api/v1/workspaces",
        json={"name": "Budget WS"},
        headers={"Authorization": f"Bearer {token}"},
    )
    ws_id = ws_resp.json()["id"]
    return token, ws_id


async def test_create_budget(client: AsyncClient):
    token, ws_id = await _setup(client, "budget_create@example.com")
    response = await client.post(
        "/api/v1/budgets",
        json={
            "workspace_id": ws_id,
            "category": "Food",
            "limit_amount": 500.0,
            "period_month": 3,
            "period_year": 2026,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["category"] == "Food"
    assert data["limit_amount"] == 500.0
    assert data["spent_amount"] == 0.0
    assert data["progress_percentage"] == 0.0


async def test_get_budget(client: AsyncClient):
    token, ws_id = await _setup(client, "budget_get@example.com")
    create_resp = await client.post(
        "/api/v1/budgets",
        json={"workspace_id": ws_id, "category": "Transport", "limit_amount": 200.0, "period_month": 3, "period_year": 2026},
        headers={"Authorization": f"Bearer {token}"},
    )
    budget_id = create_resp.json()["id"]

    response = await client.get(
        f"/api/v1/budgets/{budget_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["id"] == budget_id


async def test_list_budgets(client: AsyncClient):
    token, ws_id = await _setup(client, "budget_list@example.com")
    for category in ["Food", "Transport", "Health"]:
        await client.post(
            "/api/v1/budgets",
            json={"workspace_id": ws_id, "category": category, "limit_amount": 100.0, "period_month": 3, "period_year": 2026},
            headers={"Authorization": f"Bearer {token}"},
        )

    response = await client.get(
        f"/api/v1/budgets?workspace_id={ws_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


async def test_list_budgets_filter_by_category(client: AsyncClient):
    token, ws_id = await _setup(client, "budget_filter@example.com")
    for category in ["Food", "Entertainment"]:
        await client.post(
            "/api/v1/budgets",
            json={"workspace_id": ws_id, "category": category, "limit_amount": 100.0, "period_month": 3, "period_year": 2026},
            headers={"Authorization": f"Bearer {token}"},
        )

    response = await client.get(
        f"/api/v1/budgets?workspace_id={ws_id}&category=Food",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["category"] == "Food"


async def test_update_budget(client: AsyncClient):
    token, ws_id = await _setup(client, "budget_upd@example.com")
    create_resp = await client.post(
        "/api/v1/budgets",
        json={"workspace_id": ws_id, "category": "Misc", "limit_amount": 150.0, "period_month": 3, "period_year": 2026},
        headers={"Authorization": f"Bearer {token}"},
    )
    budget_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/budgets/{budget_id}",
        json={"limit_amount": 300.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["limit_amount"] == 300.0


async def test_delete_budget(client: AsyncClient):
    token, ws_id = await _setup(client, "budget_del@example.com")
    create_resp = await client.post(
        "/api/v1/budgets",
        json={"workspace_id": ws_id, "category": "Delete Me", "limit_amount": 50.0, "period_month": 3, "period_year": 2026},
        headers={"Authorization": f"Bearer {token}"},
    )
    budget_id = create_resp.json()["id"]

    delete_resp = await client.delete(
        f"/api/v1/budgets/{budget_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_resp.status_code == 204

    get_resp = await client.get(
        f"/api/v1/budgets/{budget_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 404


async def test_duplicate_budget_period_rejected(client: AsyncClient):
    token, ws_id = await _setup(client, "budget_dup@example.com")
    payload = {"workspace_id": ws_id, "category": "Food", "limit_amount": 100.0, "period_month": 3, "period_year": 2026}
    await client.post("/api/v1/budgets", json=payload, headers={"Authorization": f"Bearer {token}"})
    response = await client.post("/api/v1/budgets", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 409


# --- Permission / role enforcement ---

async def _setup_with_viewer(
    client: AsyncClient, owner_email: str, viewer_email: str
) -> tuple[str, str, str, str]:
    """Returns (owner_token, viewer_token, workspace_id, budget_id)."""
    owner_token, ws_id = await _setup(client, owner_email)

    await client.post(
        "/api/v1/auth/register",
        json={"email": viewer_email, "password": "StrongPass1!"},
    )
    await client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"email": viewer_email, "role": "viewer"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    viewer_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": viewer_email, "password": "StrongPass1!"},
    )
    viewer_token = viewer_resp.json()["access_token"]

    budget_resp = await client.post(
        "/api/v1/budgets",
        json={
            "workspace_id": ws_id,
            "category": "Groceries",
            "limit_amount": 100.0,
            "period_month": 3,
            "period_year": 2026,
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    budget_id = budget_resp.json()["id"]

    return owner_token, viewer_token, ws_id, budget_id


async def test_viewer_cannot_update_budget(client: AsyncClient):
    _, viewer_token, _, budget_id = await _setup_with_viewer(
        client, "budget_perm_vupd_owner@example.com", "budget_perm_vupd_viewer@example.com"
    )
    response = await client.put(
        f"/api/v1/budgets/{budget_id}",
        json={"limit_amount": 999.0},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert response.status_code == 403


async def test_viewer_cannot_delete_budget(client: AsyncClient):
    _, viewer_token, _, budget_id = await _setup_with_viewer(
        client, "budget_perm_vdel_owner@example.com", "budget_perm_vdel_viewer@example.com"
    )
    response = await client.delete(
        f"/api/v1/budgets/{budget_id}",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert response.status_code == 403


async def test_non_member_cannot_create_budget(client: AsyncClient):
    owner_token, ws_id = await _setup(client, "budget_perm_nmcreate_owner@example.com")

    await client.post(
        "/api/v1/auth/register",
        json={"email": "budget_perm_stranger@example.com", "password": "StrongPass1!"},
    )
    stranger_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "budget_perm_stranger@example.com", "password": "StrongPass1!"},
    )
    stranger_token = stranger_resp.json()["access_token"]

    response = await client.post(
        "/api/v1/budgets",
        json={
            "workspace_id": ws_id,
            "category": "Food",
            "limit_amount": 100.0,
            "period_month": 3,
            "period_year": 2026,
        },
        headers={"Authorization": f"Bearer {stranger_token}"},
    )
    assert response.status_code == 403
