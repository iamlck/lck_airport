from fastapi import APIRouter
from lck_backend.api.routes.health import router as health_router
from lck_backend.api.routes.knowledge import router as knowledge_router
from lck_backend.api.routes.chat import router as chat_router
from lck_backend.api.routes.audio import router as audio_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(knowledge_router)
api_router.include_router(chat_router)
api_router.include_router(audio_router)

