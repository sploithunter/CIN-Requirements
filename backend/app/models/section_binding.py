from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4
import enum

from sqlalchemy import DateTime, Text, ForeignKey, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.section import Section
    from app.models.message import Message
    from app.models.user import User


class BindingType(str, enum.Enum):
    DISCUSSION = "discussion"      # Chat is discussing this section
    EDITING = "editing"            # AI is actively editing this section
    REFERENCE = "reference"        # Message references this section
    QUESTION = "question"          # Question about this section
    APPROVAL = "approval"          # Approval/sign-off on this section


class SectionBinding(Base):
    """Links chat messages to document sections for context highlighting."""
    __tablename__ = "section_bindings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # What's being bound
    section_id: Mapped[UUID] = mapped_column(ForeignKey("sections.id"))
    message_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("messages.id"), nullable=True
    )

    # Binding metadata
    binding_type: Mapped[BindingType] = mapped_column(
        Enum(
            BindingType,
            values_callable=lambda x: [e.value for e in x],
            name="bindingtype",
        )
    )

    # Who created this binding (user or AI)
    created_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)

    # Active binding = currently highlighted in UI
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Optional note about the binding
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    section: Mapped["Section"] = relationship("Section", back_populates="bindings")
    message: Mapped["Message | None"] = relationship(
        "Message", back_populates="section_bindings"
    )
    created_by: Mapped["User | None"] = relationship("User")
