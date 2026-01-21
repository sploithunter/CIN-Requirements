from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4
import enum

from sqlalchemy import String, DateTime, Text, ForeignKey, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.message import Message
    from app.models.media import Media


class SessionStatus(str, enum.Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(255), default="Untitled Session")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(
            SessionStatus,
            values_callable=lambda x: [e.value for e in x],
            name="sessionstatus",
        ),
        default=SessionStatus.DRAFT,
    )

    # Owner
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))

    # Real-time collaboration
    liveblocks_room_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # AI context
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    context_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Document content (Yjs state stored separately, this is for backup/export)
    document_content: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Metadata
    token_usage: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="sessions")
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="session", cascade="all, delete-orphan"
    )
    media: Mapped[list["Media"]] = relationship(
        "Media", back_populates="session", cascade="all, delete-orphan"
    )
