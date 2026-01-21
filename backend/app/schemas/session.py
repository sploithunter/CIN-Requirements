from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.session import SessionStatus


class SessionBase(BaseModel):
    title: str = "Untitled Session"
    description: str | None = None


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: SessionStatus | None = None
    system_prompt: str | None = None
    document_content: dict | None = None


class SessionRead(SessionBase):
    id: UUID
    status: SessionStatus
    owner_id: UUID
    liveblocks_room_id: str | None
    system_prompt: str | None
    context_summary: str | None
    token_usage: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionList(BaseModel):
    id: UUID
    title: str
    status: SessionStatus
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LiveblocksTokenResponse(BaseModel):
    token: str
