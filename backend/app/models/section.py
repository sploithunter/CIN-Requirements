from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4
import enum

from sqlalchemy import String, DateTime, Text, ForeignKey, Enum, JSON, Integer, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.section_binding import SectionBinding


class SectionStatus(str, enum.Enum):
    EMPTY = "empty"                # No content yet
    DRAFT = "draft"                # Being worked on
    NEEDS_REVIEW = "needs_review"  # Ready for client review
    APPROVED = "approved"          # Client approved
    DISPUTED = "disputed"          # Needs discussion


class Section(Base):
    __tablename__ = "sections"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id"))

    # Section identity
    section_number: Mapped[str] = mapped_column(String(50))  # "1", "1.1", "3.2.1"
    title: Mapped[str] = mapped_column(String(255))

    # Hierarchical structure
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("sections.id"), nullable=True
    )
    order: Mapped[int] = mapped_column(Integer, default=0)  # Sort order within parent

    # Status tracking
    status: Mapped[SectionStatus] = mapped_column(
        Enum(
            SectionStatus,
            values_callable=lambda x: [e.value for e in x],
            name="sectionstatus",
        ),
        default=SectionStatus.EMPTY,
    )

    # ProseMirror node reference (for binding to editor)
    # This is the node ID in the TipTap document
    prosemirror_node_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Section-specific content (extracted from document for quick access)
    content_preview: Mapped[str | None] = mapped_column(Text, nullable=True)

    # AI assistance tracking
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0.0 - 1.0

    # Questions/discussion points for this section
    open_questions: Mapped[list | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="sections")
    parent: Mapped["Section | None"] = relationship(
        "Section", remote_side=[id], back_populates="children"
    )
    children: Mapped[list["Section"]] = relationship(
        "Section", back_populates="parent"
    )
    bindings: Mapped[list["SectionBinding"]] = relationship(
        "SectionBinding", back_populates="section", cascade="all, delete-orphan"
    )
