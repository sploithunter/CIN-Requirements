import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
async def test_get_current_user(
    client: AsyncClient, auth_headers: dict, test_user: User
):
    """Test getting current user info."""
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["name"] == test_user.name
    assert data["id"] == str(test_user.id)


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(client: AsyncClient):
    """Test that /me endpoint requires authentication."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: AsyncClient):
    """Test that invalid token is rejected."""
    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_google_authorize_url(client: AsyncClient):
    """Test that Google OAuth authorize endpoint returns a URL."""
    response = await client.get("/api/v1/auth/google/authorize")
    assert response.status_code == 200
    data = response.json()
    assert "authorization_url" in data
    assert "accounts.google.com" in data["authorization_url"]


@pytest.mark.asyncio
async def test_microsoft_authorize_url(client: AsyncClient):
    """Test that Microsoft OAuth authorize endpoint returns a URL."""
    response = await client.get("/api/v1/auth/microsoft/authorize")
    assert response.status_code == 200
    data = response.json()
    assert "authorization_url" in data
    assert "login.microsoftonline.com" in data["authorization_url"]
