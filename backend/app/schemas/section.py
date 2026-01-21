from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.section import SectionStatus
from app.models.section_binding import BindingType


class SectionBase(BaseModel):
    section_number: str
    title: str


class SectionCreate(SectionBase):
    document_id: UUID
    parent_id: UUID | None = None
    order: int = 0
    prosemirror_node_id: str | None = None


class SectionUpdate(BaseModel):
    section_number: str | None = None
    title: str | None = None
    status: SectionStatus | None = None
    order: int | None = None
    prosemirror_node_id: str | None = None
    content_preview: str | None = None
    ai_generated: bool | None = None
    ai_confidence: float | None = None
    open_questions: list | None = None


class SectionRead(SectionBase):
    id: UUID
    document_id: UUID
    parent_id: UUID | None
    order: int
    status: SectionStatus
    prosemirror_node_id: str | None
    content_preview: str | None
    ai_generated: bool
    ai_confidence: float | None
    open_questions: list | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SectionTree(SectionRead):
    """Section with nested children for tree view."""
    children: list["SectionTree"] = []


# Section Binding schemas
class SectionBindingBase(BaseModel):
    section_id: UUID
    binding_type: BindingType


class SectionBindingCreate(SectionBindingBase):
    message_id: UUID | None = None
    note: str | None = None


class SectionBindingUpdate(BaseModel):
    is_active: bool | None = None
    note: str | None = None


class SectionBindingRead(SectionBindingBase):
    id: UUID
    message_id: UUID | None
    created_by_id: UUID | None
    is_ai_generated: bool
    is_active: bool
    note: str | None
    created_at: datetime
    deactivated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class SectionWithBindings(SectionRead):
    """Section with its active bindings."""
    bindings: list[SectionBindingRead] = []


# For activating a section context in chat
class ActivateSectionRequest(BaseModel):
    section_id: UUID
    binding_type: BindingType = BindingType.DISCUSSION


class ActiveSectionContext(BaseModel):
    """Current section context for the chat."""
    section: SectionRead
    binding: SectionBindingRead
