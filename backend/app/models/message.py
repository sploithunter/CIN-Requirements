from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4
import enum

from sqlalchemy import DateTime, Text, ForeignKey, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.session import Session


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, enum.Enum):
    TEXT = "text"
    QUESTIONNAIRE = "questionnaire"
    REQUIREMENT = "requirement"
    VOICE_TRANSCRIPT = "voice_transcript"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(ForeignKey("sessions.id"))

    role: Mapped[MessageRole] = mapped_column(
        Enum(
            MessageRole,
            values_callable=lambda x: [e.value for e in x],
            name="messagerole",
        )
    )
    message_type: Mapped[MessageType] = mapped_column(
        Enum(
            MessageType,
            values_callable=lambda x: [e.value for e in x],
            name="messagetype",
        ),
        default=MessageType.TEXT,
    )
    content: Mapped[str] = mapped_column(Text)

    # For questionnaires and structured responses
    extra_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Token tracking
    input_tokens: Mapped[int] = mapped_column(default=0)
    output_tokens: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="messages")
