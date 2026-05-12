from fastapi import APIRouter

from src.models.chat import ChatRequest, ChatResponse
from src.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])
chat_service = ChatService()


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    history = [m.model_dump() for m in request.history]
    response_text = chat_service.generate_response(
        request.message,
        collection=request.collection,
        history=history,
    )
    return ChatResponse(response=response_text)
