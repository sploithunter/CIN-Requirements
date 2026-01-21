from uuid import UUID

import httpx
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, get_session_with_access
from app.core.config import get_settings
from app.models.session import Session
from app.schemas.session import (
    SessionCreate,
    SessionRead,
    SessionUpdate,
    SessionList,
    LiveblocksTokenResponse,
)

router = APIRouter()
settings = get_settings()


@router.post("", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    current_user: CurrentUser,
    db: DbSession,
):
    session = Session(
        title=session_data.title,
        description=session_data.description,
        owner_id=current_user.id,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    # Create Liveblocks room
    session.liveblocks_room_id = f"session-{session.id}"
    await db.commit()
    await db.refresh(session)

    return session


@router.get("", response_model=list[SessionList])
async def list_sessions(
    current_user: CurrentUser,
    db: DbSession,
    skip: int = 0,
    limit: int = 50,
):
    result = await db.execute(
        select(Session)
        .where(Session.owner_id == current_user.id)
        .order_by(Session.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{session_id}", response_model=SessionRead)
async def get_session(
    session_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    session = await get_session_with_access(session_id, current_user, db)
    return session


@router.patch("/{session_id}", response_model=SessionRead)
async def update_session(
    session_id: UUID,
    session_data: SessionUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    session = await get_session_with_access(session_id, current_user, db)

    update_data = session_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(session, field, value)

    await db.commit()
    await db.refresh(session)
    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    session = await get_session_with_access(session_id, current_user, db)
    await db.delete(session)
    await db.commit()


@router.post("/{session_id}/liveblocks-token", response_model=LiveblocksTokenResponse)
async def get_liveblocks_token(
    session_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    session = await get_session_with_access(session_id, current_user, db)

    if not session.liveblocks_room_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session does not have a Liveblocks room",
        )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.liveblocks.io/v2/identify-user",
            headers={
                "Authorization": f"Bearer {settings.liveblocks_secret_key}",
                "Content-Type": "application/json",
            },
            json={
                "userId": str(current_user.id),
                "groupIds": [session.liveblocks_room_id],
                "userInfo": {
                    "name": current_user.name,
                    "email": current_user.email,
                    "avatar": current_user.avatar_url,
                },
            },
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get Liveblocks token",
            )

        return LiveblocksTokenResponse(token=response.json()["token"])
