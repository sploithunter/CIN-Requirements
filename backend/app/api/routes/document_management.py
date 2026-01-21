from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.api.routes.projects import get_project_with_access
from app.models.project import ProjectRole
from app.models.document import Document, DocumentStatus
from app.models.document_version import DocumentVersion
from app.models.section import Section, SectionStatus
from app.models.section_binding import SectionBinding, BindingType
from app.schemas.document import (
    DocumentCreate,
    DocumentRead,
    DocumentUpdate,
    DocumentList,
    DocumentWithContent,
    DocumentVersionCreate,
    DocumentVersionRead,
    DocumentVersionWithContent,
)
from app.schemas.section import (
    SectionCreate,
    SectionRead,
    SectionUpdate,
    SectionTree,
    SectionWithBindings,
    SectionBindingCreate,
    SectionBindingRead,
    SectionBindingUpdate,
    ActivateSectionRequest,
    ActiveSectionContext,
)

router = APIRouter()


# ============================================================================
# Document CRUD
# ============================================================================


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def create_document(
    document_in: DocumentCreate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Create a new document in a project. Requires owner or gatherer role."""
    await get_project_with_access(
        document_in.project_id,
        current_user,
        db,
        required_roles=[ProjectRole.OWNER, ProjectRole.GATHERER],
    )

    document = Document(
        project_id=document_in.project_id,
        document_type=document_in.document_type,
        title=document_in.title,
        description=document_in.description,
        derived_from_id=document_in.derived_from_id,
        content=document_in.content,
        created_by_id=current_user.id,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    return document


@router.get("/project/{project_id}", response_model=list[DocumentList])
async def list_project_documents(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """List all documents in a project."""
    await get_project_with_access(project_id, current_user, db)

    result = await db.execute(
        select(Document)
        .where(Document.project_id == project_id)
        .order_by(Document.updated_at.desc())
    )
    documents = result.scalars().all()

    return documents


@router.get("/{document_id}", response_model=DocumentWithContent)
async def get_document(
    document_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Get a document with its content."""
    document = await get_document_with_access(document_id, current_user, db)
    return document


@router.patch("/{document_id}", response_model=DocumentRead)
async def update_document(
    document_id: UUID,
    document_in: DocumentUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Update a document. Requires owner or gatherer role."""
    document = await get_document_with_access(
        document_id,
        current_user,
        db,
        required_roles=[ProjectRole.OWNER, ProjectRole.GATHERER],
    )

    update_data = document_in.model_dump(exclude_unset=True)

    # Track who edited
    if update_data:
        document.last_edited_by_id = current_user.id

    for field, value in update_data.items():
        setattr(document, field, value)

    await db.commit()
    await db.refresh(document)

    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Delete a document. Requires owner role."""
    document = await get_document_with_access(
        document_id,
        current_user,
        db,
        required_roles=[ProjectRole.OWNER],
    )

    await db.delete(document)
    await db.commit()


# ============================================================================
# Document Versions
# ============================================================================


@router.post("/{document_id}/versions", response_model=DocumentVersionRead, status_code=status.HTTP_201_CREATED)
async def create_document_version(
    document_id: UUID,
    version_in: DocumentVersionCreate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Create a new version snapshot of a document."""
    document = await get_document_with_access(
        document_id,
        current_user,
        db,
        required_roles=[ProjectRole.OWNER, ProjectRole.GATHERER],
    )

    # Create version with current content
    version = DocumentVersion(
        document_id=document_id,
        version_number=document.current_version,
        content=document.content or {},
        change_summary=version_in.change_summary,
        created_by_id=current_user.id,
    )
    db.add(version)

    # Increment document version
    document.current_version += 1

    await db.commit()
    await db.refresh(version)

    return version


@router.get("/{document_id}/versions", response_model=list[DocumentVersionRead])
async def list_document_versions(
    document_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """List all versions of a document."""
    await get_document_with_access(document_id, current_user, db)

    result = await db.execute(
        select(DocumentVersion)
        .where(DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.version_number.desc())
    )
    versions = result.scalars().all()

    return versions


@router.get("/{document_id}/versions/{version_number}", response_model=DocumentVersionWithContent)
async def get_document_version(
    document_id: UUID,
    version_number: int,
    current_user: CurrentUser,
    db: DbSession,
):
    """Get a specific version of a document with content."""
    await get_document_with_access(document_id, current_user, db)

    result = await db.execute(
        select(DocumentVersion).where(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version_number == version_number,
        )
    )
    version = result.scalar_one_or_none()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found",
        )

    return version


@router.post("/{document_id}/versions/{version_number}/restore", response_model=DocumentRead)
async def restore_document_version(
    document_id: UUID,
    version_number: int,
    current_user: CurrentUser,
    db: DbSession,
):
    """Restore a document to a previous version."""
    document = await get_document_with_access(
        document_id,
        current_user,
        db,
        required_roles=[ProjectRole.OWNER, ProjectRole.GATHERER],
    )

    result = await db.execute(
        select(DocumentVersion).where(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version_number == version_number,
        )
    )
    version = result.scalar_one_or_none()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found",
        )

    # Save current state as a new version first
    current_version = DocumentVersion(
        document_id=document_id,
        version_number=document.current_version,
        content=document.content or {},
        change_summary=f"Auto-saved before restoring to v{version_number}",
        created_by_id=current_user.id,
    )
    db.add(current_version)

    # Restore content
    document.content = version.content
    document.current_version += 1
    document.last_edited_by_id = current_user.id

    await db.commit()
    await db.refresh(document)

    return document


# ============================================================================
# Sections
# ============================================================================


@router.post("/{document_id}/sections", response_model=SectionRead, status_code=status.HTTP_201_CREATED)
async def create_section(
    document_id: UUID,
    section_in: SectionCreate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Create a new section in a document."""
    await get_document_with_access(
        document_id,
        current_user,
        db,
        required_roles=[ProjectRole.OWNER, ProjectRole.GATHERER],
    )

    section = Section(
        document_id=document_id,
        section_number=section_in.section_number,
        title=section_in.title,
        parent_id=section_in.parent_id,
        order=section_in.order,
        prosemirror_node_id=section_in.prosemirror_node_id,
    )
    db.add(section)
    await db.commit()
    await db.refresh(section)

    return section


@router.get("/{document_id}/sections", response_model=list[SectionRead])
async def list_sections(
    document_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """List all sections in a document (flat list)."""
    await get_document_with_access(document_id, current_user, db)

    result = await db.execute(
        select(Section)
        .where(Section.document_id == document_id)
        .order_by(Section.section_number)
    )
    sections = result.scalars().all()

    return sections


@router.get("/{document_id}/sections/tree", response_model=list[SectionTree])
async def get_section_tree(
    document_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Get sections as a hierarchical tree."""
    await get_document_with_access(document_id, current_user, db)

    result = await db.execute(
        select(Section)
        .where(Section.document_id == document_id)
        .order_by(Section.order)
    )
    sections = result.scalars().all()

    # Build tree structure
    sections_by_id = {s.id: s for s in sections}
    root_sections = []

    for section in sections:
        section_tree = SectionTree(
            id=section.id,
            document_id=section.document_id,
            section_number=section.section_number,
            title=section.title,
            parent_id=section.parent_id,
            order=section.order,
            status=section.status,
            prosemirror_node_id=section.prosemirror_node_id,
            content_preview=section.content_preview,
            ai_generated=section.ai_generated,
            ai_confidence=section.ai_confidence,
            open_questions=section.open_questions,
            created_at=section.created_at,
            updated_at=section.updated_at,
            children=[],
        )

        if section.parent_id is None:
            root_sections.append(section_tree)

    # Build nested structure (simplified - for deeper nesting, use recursion)
    return root_sections


@router.get("/{document_id}/sections/{section_id}", response_model=SectionWithBindings)
async def get_section(
    document_id: UUID,
    section_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Get a section with its active bindings."""
    await get_document_with_access(document_id, current_user, db)

    result = await db.execute(
        select(Section)
        .where(Section.id == section_id, Section.document_id == document_id)
        .options(selectinload(Section.bindings))
    )
    section = result.scalar_one_or_none()

    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found",
        )

    # Filter to active bindings
    active_bindings = [
        SectionBindingRead(
            id=b.id,
            section_id=b.section_id,
            message_id=b.message_id,
            binding_type=b.binding_type,
            created_by_id=b.created_by_id,
            is_ai_generated=b.is_ai_generated,
            is_active=b.is_active,
            note=b.note,
            created_at=b.created_at,
            deactivated_at=b.deactivated_at,
        )
        for b in section.bindings
        if b.is_active
    ]

    return SectionWithBindings(
        id=section.id,
        document_id=section.document_id,
        section_number=section.section_number,
        title=section.title,
        parent_id=section.parent_id,
        order=section.order,
        status=section.status,
        prosemirror_node_id=section.prosemirror_node_id,
        content_preview=section.content_preview,
        ai_generated=section.ai_generated,
        ai_confidence=section.ai_confidence,
        open_questions=section.open_questions,
        created_at=section.created_at,
        updated_at=section.updated_at,
        bindings=active_bindings,
    )


@router.patch("/{document_id}/sections/{section_id}", response_model=SectionRead)
async def update_section(
    document_id: UUID,
    section_id: UUID,
    section_in: SectionUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Update a section."""
    await get_document_with_access(
        document_id,
        current_user,
        db,
        required_roles=[ProjectRole.OWNER, ProjectRole.GATHERER],
    )

    result = await db.execute(
        select(Section).where(Section.id == section_id, Section.document_id == document_id)
    )
    section = result.scalar_one_or_none()

    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found",
        )

    update_data = section_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(section, field, value)

    await db.commit()
    await db.refresh(section)

    return section


@router.delete("/{document_id}/sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_section(
    document_id: UUID,
    section_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Delete a section."""
    await get_document_with_access(
        document_id,
        current_user,
        db,
        required_roles=[ProjectRole.OWNER, ProjectRole.GATHERER],
    )

    result = await db.execute(
        select(Section).where(Section.id == section_id, Section.document_id == document_id)
    )
    section = result.scalar_one_or_none()

    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found",
        )

    await db.delete(section)
    await db.commit()


# ============================================================================
# Section Bindings (for chat-document linking)
# ============================================================================


@router.post("/{document_id}/sections/{section_id}/bindings", response_model=SectionBindingRead, status_code=status.HTTP_201_CREATED)
async def create_section_binding(
    document_id: UUID,
    section_id: UUID,
    binding_in: SectionBindingCreate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Create a binding between a section and a message."""
    await get_document_with_access(document_id, current_user, db)

    # Verify section exists
    result = await db.execute(
        select(Section).where(Section.id == section_id, Section.document_id == document_id)
    )
    section = result.scalar_one_or_none()

    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found",
        )

    binding = SectionBinding(
        section_id=section_id,
        message_id=binding_in.message_id,
        binding_type=binding_in.binding_type,
        created_by_id=current_user.id,
        note=binding_in.note,
    )
    db.add(binding)
    await db.commit()
    await db.refresh(binding)

    return SectionBindingRead(
        id=binding.id,
        section_id=binding.section_id,
        message_id=binding.message_id,
        binding_type=binding.binding_type,
        created_by_id=binding.created_by_id,
        is_ai_generated=binding.is_ai_generated,
        is_active=binding.is_active,
        note=binding.note,
        created_at=binding.created_at,
        deactivated_at=binding.deactivated_at,
    )


@router.patch("/{document_id}/bindings/{binding_id}", response_model=SectionBindingRead)
async def update_section_binding(
    document_id: UUID,
    binding_id: UUID,
    binding_in: SectionBindingUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Update a section binding (e.g., deactivate it)."""
    await get_document_with_access(document_id, current_user, db)

    result = await db.execute(
        select(SectionBinding)
        .join(Section, Section.id == SectionBinding.section_id)
        .where(SectionBinding.id == binding_id, Section.document_id == document_id)
    )
    binding = result.scalar_one_or_none()

    if not binding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Binding not found",
        )

    update_data = binding_in.model_dump(exclude_unset=True)

    # Track deactivation time
    if "is_active" in update_data and not update_data["is_active"]:
        binding.deactivated_at = datetime.utcnow()

    for field, value in update_data.items():
        setattr(binding, field, value)

    await db.commit()
    await db.refresh(binding)

    return SectionBindingRead(
        id=binding.id,
        section_id=binding.section_id,
        message_id=binding.message_id,
        binding_type=binding.binding_type,
        created_by_id=binding.created_by_id,
        is_ai_generated=binding.is_ai_generated,
        is_active=binding.is_active,
        note=binding.note,
        created_at=binding.created_at,
        deactivated_at=binding.deactivated_at,
    )


@router.get("/{document_id}/active-bindings", response_model=list[SectionBindingRead])
async def get_active_bindings(
    document_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Get all active bindings for a document."""
    await get_document_with_access(document_id, current_user, db)

    result = await db.execute(
        select(SectionBinding)
        .join(Section, Section.id == SectionBinding.section_id)
        .where(Section.document_id == document_id, SectionBinding.is_active == True)
    )
    bindings = result.scalars().all()

    return [
        SectionBindingRead(
            id=b.id,
            section_id=b.section_id,
            message_id=b.message_id,
            binding_type=b.binding_type,
            created_by_id=b.created_by_id,
            is_ai_generated=b.is_ai_generated,
            is_active=b.is_active,
            note=b.note,
            created_at=b.created_at,
            deactivated_at=b.deactivated_at,
        )
        for b in bindings
    ]


# ============================================================================
# Helper Functions
# ============================================================================


async def get_document_with_access(
    document_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    required_roles: list[ProjectRole] | None = None,
) -> Document:
    """Get a document and verify user has access to its project."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Verify project access
    await get_project_with_access(
        document.project_id,
        current_user,
        db,
        required_roles=required_roles,
    )

    return document
