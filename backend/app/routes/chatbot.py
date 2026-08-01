"""FastAPI route for the wardrobe chatbot MVP."""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.services.chatbot_service import (
    ChatbotConfigurationError,
    ChatbotProviderError,
    ChatbotService,
    parse_wardrobe_items,
)

router = APIRouter(prefix="/chat", tags=["chatbot"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1_000)
    wardrobe_items: list[dict[str, Any]] | None = None


class ChatResponse(BaseModel):
    reply: str


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Reply using supplied wardrobe items, or temporary mock data for Day 1."""
    try:
        reply = await ChatbotService().reply(
            message=request.message,
            items=parse_wardrobe_items(request.wardrobe_items),
        )
        return ChatResponse(reply=reply)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    except ChatbotConfigurationError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
    except ChatbotProviderError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error
