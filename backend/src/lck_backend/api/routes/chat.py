from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from lck_backend.schemas.chat import ChatRequest, ChatResponse
from lck_backend.services.chat_service import chat_service

router = APIRouter(tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if request.stream:
        return StreamingResponse(
            chat_service.stream_chat(request),
            media_type="text/event-stream"
        )
    return await chat_service.process_chat(request)

