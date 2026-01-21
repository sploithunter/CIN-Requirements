from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Text, ForeignKey, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.user import User


class DocumentVersion(Base):
    """Snapshot of a document at a point in time."""
    __tablename__ = "document_versions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id"))

    # Version info
    version_number: Mapped[int] = mapped_column(Integer)

    # Full content snapshot (TipTap JSON)
    content: Mapped[dict] = mapped_column(JSON)

    # What changed
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Who made the version
    created_by_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Optional: diff from previous version
    diff_from_previous: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="versions")
    created_by: Mapped["User"] = relationship("User")
