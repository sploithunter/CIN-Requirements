"""
Tests for document and section endpoints.
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4

from app.models.user import User
from app.models.project import Project, ProjectMember, ProjectRole
from app.models.document import Document, DocumentType, DocumentStatus
from app.models.section import Section, SectionStatus


@pytest.fixture
async def test_project(db_session, test_user: User) -> Project:
    """Create a test project with the test user as owner."""
    project = Project(
        name="Document Test Project",
        description="A test project for document tests",
    )
    db_session.add(project)
    await db_session.flush()

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


@pytest.fixture
async def test_document(db_session, test_project: Project, test_user: User) -> Document:
    """Create a test document."""
    document = Document(
        project_id=test_project.id,
        document_type=DocumentType.REQUIREMENTS,
        title="Test Requirements Document",
        description="A test document",
        content={"type": "doc", "content": []},
        created_by_id=test_user.id,
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)

    return document


@pytest.fixture
async def test_section(db_session, test_document: Document) -> Section:
    """Create a test section."""
    section = Section(
        document_id=test_document.id,
        section_number="1",
        title="Introduction",
        order=0,
    )
    db_session.add(section)
    await db_session.commit()
    await db_session.refresh(section)

    return section


# ============================================================================
# Document CRUD Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_document(
    client: AsyncClient, auth_headers: dict, test_project: Project
):
    """Test creating a new document."""
    response = await client.post(
        "/api/v1/documents",
        json={
            "project_id": str(test_project.id),
            "document_type": "requirements",
            "title": "New Requirements Doc",
            "description": "Testing document creation",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Requirements Doc"
    assert data["document_type"] == "requirements"
    assert data["status"] == "draft"
    assert data["current_version"] == 1


@pytest.mark.asyncio
async def test_create_document_all_types(
    client: AsyncClient, auth_headers: dict, test_project: Project
):
    """Test creating documents of all types."""
    doc_types = ["requirements", "functional", "specification", "rom", "custom"]

    for doc_type in doc_types:
        response = await client.post(
            "/api/v1/documents",
            json={
                "project_id": str(test_project.id),
                "document_type": doc_type,
                "title": f"Test {doc_type.title()} Document",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["document_type"] == doc_type


@pytest.mark.asyncio
async def test_list_project_documents(
    client: AsyncClient, auth_headers: dict, test_project: Project, test_document: Document
):
    """Test listing documents in a project."""
    response = await client.get(
        f"/api/v1/documents/project/{test_project.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(d["id"] == str(test_document.id) for d in data)


@pytest.mark.asyncio
async def test_get_document(
    client: AsyncClient, auth_headers: dict, test_document: Document
):
    """Test getting a document with content."""
    response = await client.get(
        f"/api/v1/documents/{test_document.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_document.id)
    assert data["title"] == "Test Requirements Document"
    assert "content" in data


@pytest.mark.asyncio
async def test_update_document(
    client: AsyncClient, auth_headers: dict, test_document: Document
):
    """Test updating a document."""
    response = await client.patch(
        f"/api/v1/documents/{test_document.id}",
        json={
            "title": "Updated Title",
            "status": "in_review",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["status"] == "in_review"


@pytest.mark.asyncio
async def test_delete_document(
    client: AsyncClient, auth_headers: dict, test_document: Document
):
    """Test deleting a document."""
    response = await client.delete(
        f"/api/v1/documents/{test_document.id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # Verify deleted
    response = await client.get(
        f"/api/v1/documents/{test_document.id}",
        headers=auth_headers,
    )
    assert response.status_code == 404


# ============================================================================
# Document Version Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_document_version(
    client: AsyncClient, auth_headers: dict, test_document: Document
):
    """Test creating a version snapshot."""
    response = await client.post(
        f"/api/v1/documents/{test_document.id}/versions",
        json={"change_summary": "Initial version"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["version_number"] == 1
    assert data["change_summary"] == "Initial version"


@pytest.mark.asyncio
async def test_list_document_versions(
    client: AsyncClient, auth_headers: dict, test_document: Document
):
    """Test listing document versions."""
    # Create a version first
    await client.post(
        f"/api/v1/documents/{test_document.id}/versions",
        json={"change_summary": "Test version"},
        headers=auth_headers,
    )

    response = await client.get(
        f"/api/v1/documents/{test_document.id}/versions",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


# ============================================================================
# Section Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_section(
    client: AsyncClient, auth_headers: dict, test_document: Document
):
    """Test creating a section."""
    response = await client.post(
        f"/api/v1/documents/{test_document.id}/sections",
        json={
            "document_id": str(test_document.id),
            "section_number": "2",
            "title": "User Requirements",
            "order": 1,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["section_number"] == "2"
    assert data["title"] == "User Requirements"
    assert data["status"] == "empty"


@pytest.mark.asyncio
async def test_list_sections(
    client: AsyncClient, auth_headers: dict, test_document: Document, test_section: Section
):
    """Test listing sections in a document."""
    response = await client.get(
        f"/api/v1/documents/{test_document.id}/sections",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(s["id"] == str(test_section.id) for s in data)


@pytest.mark.asyncio
async def test_get_section(
    client: AsyncClient, auth_headers: dict, test_document: Document, test_section: Section
):
    """Test getting a section with bindings."""
    response = await client.get(
        f"/api/v1/documents/{test_document.id}/sections/{test_section.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_section.id)
    assert data["title"] == "Introduction"
    assert "bindings" in data


@pytest.mark.asyncio
async def test_update_section(
    client: AsyncClient, auth_headers: dict, test_document: Document, test_section: Section
):
    """Test updating a section."""
    response = await client.patch(
        f"/api/v1/documents/{test_document.id}/sections/{test_section.id}",
        json={
            "status": "draft",
            "content_preview": "This is the introduction section...",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "draft"
    assert data["content_preview"] == "This is the introduction section..."


@pytest.mark.asyncio
async def test_delete_section(
    client: AsyncClient, auth_headers: dict, test_document: Document, test_section: Section
):
    """Test deleting a section."""
    response = await client.delete(
        f"/api/v1/documents/{test_document.id}/sections/{test_section.id}",
        headers=auth_headers,
    )
    assert response.status_code == 204


# ============================================================================
# Section Binding Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_section_binding(
    client: AsyncClient, auth_headers: dict, test_document: Document, test_section: Section
):
    """Test creating a section binding."""
    response = await client.post(
        f"/api/v1/documents/{test_document.id}/sections/{test_section.id}/bindings",
        json={
            "section_id": str(test_section.id),
            "binding_type": "discussion",
            "note": "Discussing introduction requirements",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["binding_type"] == "discussion"
    assert data["is_active"] is True
    assert data["note"] == "Discussing introduction requirements"


@pytest.mark.asyncio
async def test_get_active_bindings(
    client: AsyncClient, auth_headers: dict, test_document: Document, test_section: Section
):
    """Test getting active bindings for a document."""
    # Create a binding first
    await client.post(
        f"/api/v1/documents/{test_document.id}/sections/{test_section.id}/bindings",
        json={
            "section_id": str(test_section.id),
            "binding_type": "editing",
        },
        headers=auth_headers,
    )

    response = await client.get(
        f"/api/v1/documents/{test_document.id}/active-bindings",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert all(b["is_active"] for b in data)


@pytest.mark.asyncio
async def test_deactivate_binding(
    client: AsyncClient, auth_headers: dict, test_document: Document, test_section: Section
):
    """Test deactivating a section binding."""
    # Create a binding first
    create_response = await client.post(
        f"/api/v1/documents/{test_document.id}/sections/{test_section.id}/bindings",
        json={
            "section_id": str(test_section.id),
            "binding_type": "discussion",
        },
        headers=auth_headers,
    )
    binding_id = create_response.json()["id"]

    # Deactivate it
    response = await client.patch(
        f"/api/v1/documents/{test_document.id}/bindings/{binding_id}",
        json={"is_active": False},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False
    assert data["deactivated_at"] is not None


# ============================================================================
# Document Import Tests
# ============================================================================


@pytest.mark.asyncio
async def test_import_document_preview(
    client: AsyncClient, auth_headers: dict, test_project: Project
):
    """Test previewing a document import."""
    # Read a test docx file
    test_file_path = "/Users/jason/Documents/Conversational_Requirements_Platform_Requirements_v1.2.docx"

    import os
    if not os.path.exists(test_file_path):
        pytest.skip("Test document not available")

    with open(test_file_path, "rb") as f:
        response = await client.post(
            f"/api/v1/documents/import/{test_project.id}/preview",
            headers=auth_headers,
            files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )

    assert response.status_code == 200
    data = response.json()
    assert "metadata" in data
    assert "sections" in data
    assert len(data["sections"]) > 0


@pytest.mark.asyncio
async def test_import_document(
    client: AsyncClient, auth_headers: dict, test_project: Project
):
    """Test importing a document."""
    test_file_path = "/Users/jason/Documents/Conversational_Requirements_Platform_Requirements_v1.2.docx"

    import os
    if not os.path.exists(test_file_path):
        pytest.skip("Test document not available")

    with open(test_file_path, "rb") as f:
        response = await client.post(
            f"/api/v1/documents/import/{test_project.id}",
            headers=auth_headers,
            files={"file": ("requirements.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            data={"document_type": "requirements", "title": "Imported Requirements"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Imported Requirements"
    assert data["document_type"] == "requirements"
    assert data["status"] == "draft"

    # Verify sections were created
    sections_response = await client.get(
        f"/api/v1/documents/{data['id']}/sections",
        headers=auth_headers,
    )
    assert sections_response.status_code == 200
    sections = sections_response.json()
    assert len(sections) > 0
