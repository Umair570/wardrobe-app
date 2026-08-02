"""FastAPI route for the wardrobe chatbot MVP."""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

try:
    from app.services.chatbot_service import (
        ChatbotConfigurationError,
        ChatbotProviderError,
        ChatbotService,
        parse_wardrobe_items,
    )
except ImportError:
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
    user_id: str = Field(default="default_user", max_length=128)


class RecommendedItemOut(BaseModel):
    id: str
    label: str
    category: str
    slot: str
    color: str
    type: str


class ChatResponse(BaseModel):
    reply: str
    recommended_items: list[RecommendedItemOut] = Field(default_factory=list)


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Return wardrobe-aware outfit suggestion with structured item list."""
    try:
        result = await ChatbotService().reply(
            message=request.message,
            items=parse_wardrobe_items(request.wardrobe_items),
            user_id=request.user_id,
        )
        return ChatResponse(
            reply=result.reply,
            recommended_items=[
                RecommendedItemOut(
                    id=item.id,
                    label=item.label,
                    category=item.category,
                    slot=item.slot,
                    color=item.color,
                    type=item.type,
                )
                for item in result.recommended_items
            ],
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    except ChatbotConfigurationError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
    except ChatbotProviderError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error
