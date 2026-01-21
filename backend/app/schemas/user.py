from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    email: EmailStr
    name: str
    avatar_url: str | None = None


class UserCreate(UserBase):
    oauth_provider: str | None = None
    oauth_id: str | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    avatar_url: str | None = None


class UserRead(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserRead
