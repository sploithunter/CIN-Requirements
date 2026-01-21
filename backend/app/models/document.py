from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4
import enum

from sqlalchemy import String, DateTime, Text, ForeignKey, Enum, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User
    from app.models.section import Section
    from app.models.document_version import DocumentVersion


class DocumentType(str, enum.Enum):
    REQUIREMENTS = "requirements"           # Initial requirements gathering
    FUNCTIONAL_ANALYSIS = "functional"      # Detailed functional breakdown
    SPECIFICATION = "specification"         # Technical specification
    ROM = "rom"                             # Rough Order of Magnitude
    CUSTOM = "custom"                       # User-defined document type


class DocumentStatus(str, enum.Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    SUPERSEDED = "superseded"              # Replaced by newer version


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"))

    # Document identity
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(
            DocumentType,
            values_callable=lambda x: [e.value for e in x],
            name="documenttype",
        )
    )
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Current version tracking
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(
            DocumentStatus,
            values_callable=lambda x: [e.value for e in x],
            name="documentstatus",
        ),
        default=DocumentStatus.DRAFT,
    )

    # Lineage - which document was this derived from?
    derived_from_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("documents.id"), nullable=True
    )

    # TipTap/ProseMirror content (JSON)
    content: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Liveblocks for real-time collaboration
    liveblocks_room_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Who created/last edited
    created_by_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    last_edited_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="documents")
    sections: Mapped[list["Section"]] = relationship(
        "Section", back_populates="document", cascade="all, delete-orphan"
    )
    versions: Mapped[list["DocumentVersion"]] = relationship(
        "DocumentVersion", back_populates="document", cascade="all, delete-orphan"
    )
    derived_from: Mapped["Document | None"] = relationship(
        "Document", remote_side=[id], foreign_keys=[derived_from_id]
    )
    created_by: Mapped["User"] = relationship(
        "User", foreign_keys=[created_by_id], back_populates="created_documents"
    )
    last_edited_by: Mapped["User | None"] = relationship(
        "User", foreign_keys=[last_edited_by_id]
    )
