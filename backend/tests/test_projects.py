"""
Tests for project and project member endpoints.
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4

from app.models.user import User
from app.models.project import Project, ProjectMember, ProjectRole


@pytest.fixture
async def test_project(db_session, test_user: User) -> Project:
    """Create a test project with the test user as owner."""
    project = Project(
        name="Test Project",
        description="A test project for unit tests",
        client_name="Test Client",
    )
    db_session.add(project)
    await db_session.flush()

    # Add user as owner
    member = ProjectMember(
        project_id=project.id,
        user_id=test_user.id,
        role=ProjectRole.OWNER,
    )
    member.accepted_at = member.invited_at
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(project)

    return project


# ============================================================================
# Project CRUD Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient, auth_headers: dict):
    """Test creating a new project."""
    response = await client.post(
        "/api/v1/projects",
        json={
            "name": "New Project",
            "description": "A new test project",
            "client_name": "Acme Corp",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Project"
    assert data["description"] == "A new test project"
    assert data["client_name"] == "Acme Corp"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_project_unauthorized(client: AsyncClient):
    """Test that creating a project requires authentication."""
    response = await client.post(
        "/api/v1/projects",
        json={"name": "Unauthorized Project"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_projects(
    client: AsyncClient, auth_headers: dict, test_project: Project
):
    """Test listing user's projects."""
    response = await client.get("/api/v1/projects", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(p["id"] == str(test_project.id) for p in data)


@pytest.mark.asyncio
async def test_get_project(
    client: AsyncClient, auth_headers: dict, test_project: Project
):
    """Test getting a project with members."""
    response = await client.get(
        f"/api/v1/projects/{test_project.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_project.id)
    assert data["name"] == "Test Project"
    assert "members" in data
    assert len(data["members"]) == 1
    assert data["members"][0]["role"] == "owner"


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient, auth_headers: dict):
    """Test getting a non-existent project."""
    response = await client.get(
        f"/api/v1/projects/{uuid4()}",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_project(
    client: AsyncClient, auth_headers: dict, test_project: Project
):
    """Test updating a project."""
    response = await client.patch(
        f"/api/v1/projects/{test_project.id}",
        json={"name": "Updated Project Name"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Project Name"


@pytest.mark.asyncio
async def test_delete_project(
    client: AsyncClient, auth_headers: dict, test_project: Project
):
    """Test deleting a project."""
    response = await client.delete(
        f"/api/v1/projects/{test_project.id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # Verify it's deleted
    response = await client.get(
        f"/api/v1/projects/{test_project.id}",
        headers=auth_headers,
    )
    assert response.status_code == 404


# ============================================================================
# Project Member Tests
# ============================================================================


@pytest.mark.asyncio
async def test_list_project_members(
    client: AsyncClient, auth_headers: dict, test_project: Project
):
    """Test listing project members."""
    response = await client.get(
        f"/api/v1/projects/{test_project.id}/members",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["role"] == "owner"


@pytest.mark.asyncio
async def test_add_project_member(
    client: AsyncClient, auth_headers: dict, test_project: Project, db_session
):
    """Test adding a new member to a project."""
    # Create another user to add
    from app.models.user import User
    new_user = User(
        email="newmember@test.com",
        name="New Member",
    )
    db_session.add(new_user)
    await db_session.commit()
    await db_session.refresh(new_user)

    response = await client.post(
        f"/api/v1/projects/{test_project.id}/members",
        json={
            "user_id": str(new_user.id),
            "role": "client",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == str(new_user.id)
    assert data["role"] == "client"


@pytest.mark.asyncio
async def test_add_duplicate_member(
    client: AsyncClient, auth_headers: dict, test_project: Project, test_user: User
):
    """Test that adding a duplicate member fails."""
    response = await client.post(
        f"/api/v1/projects/{test_project.id}/members",
        json={
            "user_id": str(test_user.id),
            "role": "client",
        },
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "already a member" in response.json()["detail"]
