from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.project import ProjectRole


class ProjectBase(BaseModel):
    name: str
    description: str | None = None
    client_name: str | None = None
    target_date: datetime | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    client_name: str | None = None
    target_date: datetime | None = None


class ProjectMemberBase(BaseModel):
    user_id: UUID
    role: ProjectRole


class ProjectMemberCreate(ProjectMemberBase):
    pass


class ProjectMemberUpdate(BaseModel):
    role: ProjectRole


class ProjectMemberRead(ProjectMemberBase):
    id: UUID
    project_id: UUID
    invited_at: datetime
    accepted_at: datetime | None

    # Include user info
    user_name: str | None = None
    user_email: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ProjectRead(ProjectBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectWithMembers(ProjectRead):
    members: list[ProjectMemberRead] = []


class ProjectList(BaseModel):
    id: UUID
    name: str
    client_name: str | None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
