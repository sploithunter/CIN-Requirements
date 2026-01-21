from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4
import enum

from sqlalchemy import String, DateTime, BigInteger, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.session import Session


class MediaType(str, enum.Enum):
    IMAGE = "image"
    AUDIO = "audio"
    DOCUMENT = "document"
    VIDEO = "video"


class Media(Base):
    __tablename__ = "media"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(ForeignKey("sessions.id"))

    filename: Mapped[str] = mapped_column(String(255))
    original_filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    media_type: Mapped[MediaType] = mapped_column(
        Enum(
            MediaType,
            values_callable=lambda x: [e.value for e in x],
            name="mediatype",
        )
    )
    size_bytes: Mapped[int] = mapped_column(BigInteger)

    # Storage location (S3/R2)
    storage_key: Mapped[str] = mapped_column(String(500))
    storage_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # For images - extracted text from vision
    extracted_text: Mapped[str | None] = mapped_column(String, nullable=True)

    # For audio - transcript
    transcript: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="media")
