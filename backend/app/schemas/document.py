from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentType, DocumentStatus


class DocumentBase(BaseModel):
    title: str
    description: str | None = None
    document_type: DocumentType


class DocumentCreate(DocumentBase):
    project_id: UUID
    derived_from_id: UUID | None = None
    content: dict | None = None


class DocumentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: DocumentStatus | None = None
    content: dict | None = None


class DocumentRead(DocumentBase):
    id: UUID
    project_id: UUID
    current_version: int
    status: DocumentStatus
    derived_from_id: UUID | None
    liveblocks_room_id: str | None
    created_by_id: UUID
    last_edited_by_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentWithContent(DocumentRead):
    content: dict | None


class DocumentList(BaseModel):
    id: UUID
    title: str
    document_type: DocumentType
    status: DocumentStatus
    current_version: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Document Version schemas
class DocumentVersionCreate(BaseModel):
    change_summary: str | None = None


class DocumentVersionRead(BaseModel):
    id: UUID
    document_id: UUID
    version_number: int
    change_summary: str | None
    created_by_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentVersionWithContent(DocumentVersionRead):
    content: dict
    diff_from_previous: dict | None
