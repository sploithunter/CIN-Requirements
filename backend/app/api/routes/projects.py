from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models.project import Project, ProjectMember, ProjectRole
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    ProjectList,
    ProjectWithMembers,
    ProjectMemberCreate,
    ProjectMemberRead,
    ProjectMemberUpdate,
)

router = APIRouter()


# ============================================================================
# Project CRUD
# ============================================================================


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Create a new project. The creator becomes the owner."""
    project = Project(
        name=project_in.name,
        description=project_in.description,
        client_name=project_in.client_name,
        target_date=project_in.target_date,
    )
    db.add(project)
    await db.flush()

    # Add creator as owner
    member = ProjectMember(
        project_id=project.id,
        user_id=current_user.id,
        role=ProjectRole.OWNER,
    )
    member.accepted_at = member.invited_at  # Auto-accept for creator
    db.add(member)

    await db.commit()
    await db.refresh(project)

    return project


@router.get("", response_model=list[ProjectList])
async def list_projects(
    current_user: CurrentUser,
    db: DbSession,
    skip: int = 0,
    limit: int = 50,
):
    """List all projects the user is a member of."""
    result = await db.execute(
        select(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(ProjectMember.user_id == current_user.id)
        .order_by(Project.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    projects = result.scalars().all()
    return projects


@router.get("/{project_id}", response_model=ProjectWithMembers)
async def get_project(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Get a project with its members."""
    project = await get_project_with_access(project_id, current_user, db)

    # Load members with user info
    result = await db.execute(
        select(ProjectMember)
        .where(ProjectMember.project_id == project_id)
        .options(selectinload(ProjectMember.user))
    )
    members = result.scalars().all()

    # Build response with member info
    member_reads = []
    for m in members:
        member_read = ProjectMemberRead(
            id=m.id,
            project_id=m.project_id,
            user_id=m.user_id,
            role=m.role,
            invited_at=m.invited_at,
            accepted_at=m.accepted_at,
            user_name=m.user.name if m.user else None,
            user_email=m.user.email if m.user else None,
        )
        member_reads.append(member_read)

    return ProjectWithMembers(
        id=project.id,
        name=project.name,
        description=project.description,
        client_name=project.client_name,
        target_date=project.target_date,
        created_at=project.created_at,
        updated_at=project.updated_at,
        members=member_reads,
    )


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: UUID,
    project_in: ProjectUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Update a project. Requires owner or gatherer role."""
    project = await get_project_with_access(
        project_id, current_user, db, required_roles=[ProjectRole.OWNER, ProjectRole.GATHERER]
    )

    update_data = project_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Delete a project. Requires owner role."""
    project = await get_project_with_access(
        project_id, current_user, db, required_roles=[ProjectRole.OWNER]
    )

    await db.delete(project)
    await db.commit()


# ============================================================================
# Project Members
# ============================================================================


@router.post("/{project_id}/members", response_model=ProjectMemberRead, status_code=status.HTTP_201_CREATED)
async def add_project_member(
    project_id: UUID,
    member_in: ProjectMemberCreate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Add a member to a project. Requires owner role."""
    await get_project_with_access(
        project_id, current_user, db, required_roles=[ProjectRole.OWNER]
    )

    # Check if user exists
    result = await db.execute(select(User).where(User.id == member_in.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if already a member
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == member_in.user_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this project",
        )

    member = ProjectMember(
        project_id=project_id,
        user_id=member_in.user_id,
        role=member_in.role,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)

    return ProjectMemberRead(
        id=member.id,
        project_id=member.project_id,
        user_id=member.user_id,
        role=member.role,
        invited_at=member.invited_at,
        accepted_at=member.accepted_at,
        user_name=user.name,
        user_email=user.email,
    )


@router.get("/{project_id}/members", response_model=list[ProjectMemberRead])
async def list_project_members(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """List all members of a project."""
    await get_project_with_access(project_id, current_user, db)

    result = await db.execute(
        select(ProjectMember)
        .where(ProjectMember.project_id == project_id)
        .options(selectinload(ProjectMember.user))
    )
    members = result.scalars().all()

    return [
        ProjectMemberRead(
            id=m.id,
            project_id=m.project_id,
            user_id=m.user_id,
            role=m.role,
            invited_at=m.invited_at,
            accepted_at=m.accepted_at,
            user_name=m.user.name if m.user else None,
            user_email=m.user.email if m.user else None,
        )
        for m in members
    ]


@router.patch("/{project_id}/members/{member_id}", response_model=ProjectMemberRead)
async def update_project_member(
    project_id: UUID,
    member_id: UUID,
    member_in: ProjectMemberUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Update a member's role. Requires owner role."""
    await get_project_with_access(
        project_id, current_user, db, required_roles=[ProjectRole.OWNER]
    )

    result = await db.execute(
        select(ProjectMember)
        .where(ProjectMember.id == member_id, ProjectMember.project_id == project_id)
        .options(selectinload(ProjectMember.user))
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    # Can't demote the last owner
    if member.role == ProjectRole.OWNER and member_in.role != ProjectRole.OWNER:
        result = await db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.role == ProjectRole.OWNER,
            )
        )
        owners = result.scalars().all()
        if len(owners) == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last owner",
            )

    member.role = member_in.role
    await db.commit()
    await db.refresh(member)

    return ProjectMemberRead(
        id=member.id,
        project_id=member.project_id,
        user_id=member.user_id,
        role=member.role,
        invited_at=member.invited_at,
        accepted_at=member.accepted_at,
        user_name=member.user.name if member.user else None,
        user_email=member.user.email if member.user else None,
    )


@router.delete("/{project_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_project_member(
    project_id: UUID,
    member_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Remove a member from a project. Requires owner role."""
    await get_project_with_access(
        project_id, current_user, db, required_roles=[ProjectRole.OWNER]
    )

    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.id == member_id,
            ProjectMember.project_id == project_id,
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    # Can't remove the last owner
    if member.role == ProjectRole.OWNER:
        result = await db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.role == ProjectRole.OWNER,
            )
        )
        owners = result.scalars().all()
        if len(owners) == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last owner",
            )

    await db.delete(member)
    await db.commit()


# ============================================================================
# Helper Functions
# ============================================================================


async def get_project_with_access(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    required_roles: list[ProjectRole] | None = None,
) -> Project:
    """Get a project and verify user has access with the required role."""
    # Get the project
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Check membership
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this project",
        )

    # Check role if required
    if required_roles and membership.role not in required_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This action requires one of these roles: {', '.join(r.value for r in required_roles)}",
        )

    return project
