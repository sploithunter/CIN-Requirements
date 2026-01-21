from uuid import UUID
from io import BytesIO

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser, DbSession, get_session_with_access
from app.services.document_generator import DocumentGenerator

router = APIRouter()


@router.post("/{session_id}/generate/requirements")
async def generate_requirements_document(
    session_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    format: str = "docx",
):
    session = await get_session_with_access(session_id, current_user, db)
    doc_generator = DocumentGenerator()

    if format not in ["docx", "markdown"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format must be 'docx' or 'markdown'",
        )

    # Generate document
    document_bytes = await doc_generator.generate_requirements_document(
        session=session,
        format=format,
    )

    if format == "docx":
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"{session.title.replace(' ', '_')}_requirements.docx"
    else:
        media_type = "text/markdown"
        filename = f"{session.title.replace(' ', '_')}_requirements.md"

    return StreamingResponse(
        BytesIO(document_bytes),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/{session_id}/generate/summary")
async def generate_session_summary(
    session_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    session = await get_session_with_access(session_id, current_user, db)
    doc_generator = DocumentGenerator()

    summary = await doc_generator.generate_session_summary(session=session)

    return {"summary": summary}


@router.post("/{session_id}/export")
async def export_session(
    session_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    include_messages: bool = True,
    include_media: bool = False,
):
    session = await get_session_with_access(session_id, current_user, db)
    doc_generator = DocumentGenerator()

    export_data = await doc_generator.export_session(
        session=session,
        include_messages=include_messages,
        include_media=include_media,
    )

    return export_data
