import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_happy_path(async_client: AsyncClient):
    response = await async_client.post(
        "/auth/register",
        json={"email": "alice@claimguard.com", "password": "secure_password_123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "alice@claimguard.com"
    assert data["role"] == "owner"
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email_fails(async_client: AsyncClient):
    # First registration
    await async_client.post(
        "/auth/register",
        json={"email": "duplicate@claimguard.com", "password": "password123"},
    )

    # Second registration with same email
    response = await async_client.post(
        "/auth/register",
        json={"email": "duplicate@claimguard.com", "password": "different_password"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_login_happy_path(async_client: AsyncClient):
    # Register first
    await async_client.post(
        "/auth/register",
        json={"email": "bob@claimguard.com", "password": "bob_password_123"},
    )

    # Login
    response = await async_client.post(
        "/auth/login",
        json={"email": "bob@claimguard.com", "password": "bob_password_123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 900  # 15 minutes


@pytest.mark.asyncio
async def test_login_invalid_password(async_client: AsyncClient):
    await async_client.post(
        "/auth/register",
        json={"email": "charlie@claimguard.com", "password": "correct_password"},
    )

    response = await async_client.post(
        "/auth/login",
        json={"email": "charlie@claimguard.com", "password": "WRONG_password"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_refresh_token_rotation(async_client: AsyncClient):
    await async_client.post(
        "/auth/register",
        json={"email": "rotation@claimguard.com", "password": "rotation_pass_123"},
    )

    login_resp = await async_client.post(
        "/auth/login",
        json={"email": "rotation@claimguard.com", "password": "rotation_pass_123"},
    )
    first_refresh = login_resp.json()["refresh_token"]

    # Rotate refresh token
    refresh_resp = await async_client.post(
        "/auth/refresh",
        json={"refresh_token": first_refresh},
    )
    assert refresh_resp.status_code == 200
    new_data = refresh_resp.json()
    assert "access_token" in new_data
    assert "refresh_token" in new_data
    assert new_data["refresh_token"] != first_refresh

    # Attempting to reuse old refresh token MUST fail
    reused_resp = await async_client.post(
        "/auth/refresh",
        json={"refresh_token": first_refresh},
    )
    assert reused_resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_profile(async_client: AsyncClient):
    await async_client.post(
        "/auth/register",
        json={"email": "me@claimguard.com", "password": "me_password_123"},
    )

    login_resp = await async_client.post(
        "/auth/login",
        json={"email": "me@claimguard.com", "password": "me_password_123"},
    )
    access_token = login_resp.json()["access_token"]

    # Valid profile fetch
    me_resp = await async_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "me@claimguard.com"

    # Missing auth header
    unauth_resp = await async_client.get("/auth/me")
    assert unauth_resp.status_code == 401

    # Bad token
    bad_resp = await async_client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid_garbage_token"},
    )
    assert bad_resp.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_token(async_client: AsyncClient):
    await async_client.post(
        "/auth/register",
        json={"email": "logout@claimguard.com", "password": "logout_password_123"},
    )

    login_resp = await async_client.post(
        "/auth/login",
        json={"email": "logout@claimguard.com", "password": "logout_password_123"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    # Logout
    logout_resp = await async_client.post(
        "/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert logout_resp.status_code == 200

    # Refresh should now be rejected
    refresh_resp = await async_client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 401
