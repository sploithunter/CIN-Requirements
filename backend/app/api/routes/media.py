from uuid import UUID

from fastapi import APIRouter, HTTPException, UploadFile, File, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, get_session_with_access
from app.models.media import Media, MediaType
from app.services.storage_service import StorageService

router = APIRouter()

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/wav", "audio/webm", "audio/ogg"}
ALLOWED_DOCUMENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def get_media_type(content_type: str) -> MediaType:
    if content_type in ALLOWED_IMAGE_TYPES:
        return MediaType.IMAGE
    elif content_type in ALLOWED_AUDIO_TYPES:
        return MediaType.AUDIO
    elif content_type in ALLOWED_DOCUMENT_TYPES:
        return MediaType.DOCUMENT
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {content_type}",
        )


@router.post("/{session_id}/upload")
async def upload_file(
    session_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    file: UploadFile = File(...),
):
    await get_session_with_access(session_id, current_user, db)
    storage_service = StorageService()

    # Validate content type
    if not file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content type is required",
        )

    media_type = get_media_type(file.content_type)

    # Read file content
    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed ({MAX_FILE_SIZE // 1024 // 1024}MB)",
        )

    # Upload to storage
    storage_key, storage_url = await storage_service.upload_file(
        content=content,
        filename=file.filename or "unnamed",
        content_type=file.content_type,
        session_id=session_id,
    )

    # Create media record
    media = Media(
        session_id=session_id,
        filename=storage_key.split("/")[-1],
        original_filename=file.filename or "unnamed",
        content_type=file.content_type,
        media_type=media_type,
        size_bytes=file_size,
        storage_key=storage_key,
        storage_url=storage_url,
    )
    db.add(media)
    await db.commit()
    await db.refresh(media)

    return {
        "id": str(media.id),
        "filename": media.original_filename,
        "content_type": media.content_type,
        "size_bytes": media.size_bytes,
        "url": media.storage_url,
    }


@router.get("/{session_id}/files")
async def list_files(
    session_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    await get_session_with_access(session_id, current_user, db)

    result = await db.execute(
        select(Media)
        .where(Media.session_id == session_id)
        .order_by(Media.created_at.desc())
    )
    files = result.scalars().all()

    return [
        {
            "id": str(f.id),
            "filename": f.original_filename,
            "content_type": f.content_type,
            "media_type": f.media_type,
            "size_bytes": f.size_bytes,
            "url": f.storage_url,
            "created_at": f.created_at.isoformat(),
        }
        for f in files
    ]


@router.delete("/{session_id}/files/{media_id}")
async def delete_file(
    session_id: UUID,
    media_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    await get_session_with_access(session_id, current_user, db)
    storage_service = StorageService()

    result = await db.execute(
        select(Media).where(Media.id == media_id, Media.session_id == session_id)
    )
    media = result.scalar_one_or_none()

    if media is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    # Delete from storage
    await storage_service.delete_file(media.storage_key)

    # Delete record
    await db.delete(media)
    await db.commit()

    return {"status": "deleted"}


@router.get("/{session_id}/files/{media_id}/url")
async def get_file_url(
    session_id: UUID,
    media_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    await get_session_with_access(session_id, current_user, db)
    storage_service = StorageService()

    result = await db.execute(
        select(Media).where(Media.id == media_id, Media.session_id == session_id)
    )
    media = result.scalar_one_or_none()

    if media is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    # Generate presigned URL
    presigned_url = await storage_service.get_presigned_url(
        storage_key=media.storage_key,
        expires_in=3600,
    )

    return {"url": presigned_url}
