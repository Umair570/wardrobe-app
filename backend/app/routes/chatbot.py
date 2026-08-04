"""FastAPI route for the wardrobe chatbot.

Phase 10: Groq Stylist Service integration. Uses structured JSON schema responses.
Items are fetched via the Semantic RAG Retrieval pipeline (Qdrant vector search).
"""

from typing import Any, Literal, Optional

from fastapi import APIRouter, HTTPException, Query, status, Depends
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user
from app.core.security import UserContext
from app.services.retrieval.retrieval import retrieve_wardrobe_for_query
from app.services.stylist.stylist_service import generate_outfit_recommendation
from app.services.stylist.schemas import WardrobeItem, OutfitRecommendation

router = APIRouter(prefix="/chat", tags=["chatbot"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1_000)
    # Legacy: frontend can still pass items directly; if provided they skip Qdrant retrieval.
    wardrobe_items: list[dict[str, Any]] | None = None
    # Phase 9 optional overrides – let the frontend pass explicit filters
    season:   Optional[str] = Field(default=None, description="Force season filter on Qdrant search")
    category: Optional[str] = Field(default=None, description="Force category filter on Qdrant search")
    top_k:    int           = Field(default=8, ge=1, le=20, description="Max Qdrant results")


class ChatResponse(BaseModel):
    reply: str
    outfit: OutfitRecommendation
    # Phase 8/9: expose retrieval metadata so frontend / devs can see what Qdrant returned
    retrieval_source: Literal["qdrant_vector", "mongodb_fallback", "client_provided"] = "mongodb_fallback"
    items_retrieved: int = 0


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: UserContext = Depends(get_current_user),
) -> ChatResponse:
    """
    Return wardrobe-aware outfit suggestion with structured item list.

    Item retrieval flow:
      1. If client provided wardrobe_items → use them directly (legacy path).
      2. Otherwise → Qdrant vector search filtered by user_id (Phase 8/9).
      3. If Qdrant returns 0 results → MongoDB fallback.
      4. StylistService receives the item list and calls Groq LLM with structured output schema (Phase 10).
    """
    # ------------------------------------------------------------------
    # Resolve wardrobe items
    # ------------------------------------------------------------------
    retrieval_source = "mongodb_fallback"

    if request.wardrobe_items:
        # Client-provided: parse into WardrobeItem models
        items = []
        for item in request.wardrobe_items:
            # handle legacy _id vs id
            item_id = item.get("id") or item.get("_id") or "unknown"
            items.append(WardrobeItem(
                id=str(item_id),
                category=item.get("category"),
                type=item.get("type"),
                color=item.get("color"),
                style=item.get("style"),
                season=item.get("season"),
                pattern=item.get("pattern"),
                tags=item.get("tags", [])
            ))
        retrieval_source = "client_provided"
    else:
        # Phase 8/9: RAG retrieval via Qdrant
        items = await retrieve_wardrobe_for_query(
            user_id=current_user.id,
            query=request.message,
            top_k=request.top_k,
            season_override=request.season,
            category_override=request.category,
        )
        # Detect which path was taken (Qdrant vs MongoDB fallback)
        from app.services.vector.qdrant_service import qdrant_service
        retrieval_source = "qdrant_vector" if qdrant_service.available else "mongodb_fallback"

    # ------------------------------------------------------------------
    # Call StylistService (Phase 10)
    # ------------------------------------------------------------------
    try:
        result = await generate_outfit_recommendation(
            query=request.message,
            retrieved_items=items
        )
        
        return ChatResponse(
            reply=result.message,
            outfit=result.outfit,
            retrieval_source=retrieval_source,
            items_retrieved=len(items),
        )
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error