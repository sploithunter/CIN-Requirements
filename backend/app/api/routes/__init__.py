from fastapi import APIRouter

from app.api.routes import auth, sessions, ai, media, documents, projects, document_management

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(media.router, prefix="/media", tags=["media"])
api_router.include_router(documents.router, prefix="/documents/export", tags=["document-export"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(document_management.router, prefix="/documents", tags=["documents"])
