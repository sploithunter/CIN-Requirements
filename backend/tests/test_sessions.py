import pytest
from httpx import AsyncClient
from uuid import uuid4

from app.models.user import User
from app.models.session import Session


@pytest.mark.asyncio
async def test_create_session(client: AsyncClient, auth_headers: dict):
    """Test creating a new session."""
    response = await client.post(
        "/api/v1/sessions",
        json={
            "title": "New Test Session",
            "description": "A session created via API test",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Test Session"
    assert data["description"] == "A session created via API test"
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_create_session_unauthorized(client: AsyncClient):
    """Test that creating a session requires authentication."""
    response = await client.post(
        "/api/v1/sessions",
        json={"title": "Unauthorized Session"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_sessions(
    client: AsyncClient, auth_headers: dict, test_session: Session
):
    """Test listing user sessions."""
    response = await client.get("/api/v1/sessions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(s["id"] == str(test_session.id) for s in data)


@pytest.mark.asyncio
async def test_get_session(
    client: AsyncClient, auth_headers: dict, test_session: Session
):
    """Test getting a specific session."""
    response = await client.get(
        f"/api/v1/sessions/{test_session.id}", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_session.id)
    assert data["title"] == test_session.title


@pytest.mark.asyncio
async def test_get_session_not_found(client: AsyncClient, auth_headers: dict):
    """Test getting a non-existent session."""
    fake_id = uuid4()
    response = await client.get(f"/api/v1/sessions/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_session(
    client: AsyncClient, auth_headers: dict, test_session: Session
):
    """Test updating a session."""
    response = await client.patch(
        f"/api/v1/sessions/{test_session.id}",
        json={"title": "Updated Title", "description": "Updated description"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_session(
    client: AsyncClient, auth_headers: dict, test_session: Session
):
    """Test deleting a session."""
    response = await client.delete(
        f"/api/v1/sessions/{test_session.id}", headers=auth_headers
    )
    assert response.status_code == 204

    # Verify it's deleted
    response = await client.get(
        f"/api/v1/sessions/{test_session.id}", headers=auth_headers
    )
    assert response.status_code == 404
