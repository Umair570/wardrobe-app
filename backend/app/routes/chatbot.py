"""FastAPI route for the wardrobe chatbot.

Phase 10: Groq Stylist Service integration. Uses structured JSON schema responses.
Items are fetched via the Semantic RAG Retrieval pipeline (Qdrant vector search).
"""

import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from fastapi import APIRouter, HTTPException, Query, status, Depends
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user
from app.core.security import UserContext
from app.database.mongodb import chat_sessions_collection, chat_messages_collection
from app.services.retrieval.retrieval import retrieve_wardrobe_for_query
from app.services.stylist.stylist_service import generate_outfit_recommendation
from app.services.stylist.schemas import WardrobeItem, OutfitRecommendation

router = APIRouter(prefix="/chat", tags=["chatbot"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1_000)
    session_id: Optional[str] = Field(default=None, description="Current chat session ID")
    # Native frontend geographical location parameters via Navigation API
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    # Legacy: frontend can still pass items directly; if provided they skip Qdrant retrieval.
    wardrobe_items: list[dict[str, Any]] | None = None
    # Phase 9 optional overrides – let the frontend pass explicit filters
    season:   Optional[str] = Field(default=None, description="Force season filter on Qdrant search")
    category: Optional[str] = Field(default=None, description="Force category filter on Qdrant search")
    top_k:    int           = Field(default=8, ge=1, le=20, description="Max Qdrant results")


class ChatResponse(BaseModel):
    reply: str
    outfit: OutfitRecommendation
    session_id: str
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
    # Weather & Context Layer (Phase 5)
    # ------------------------------------------------------------------
    try:
        from app.services.weather.weather_service import fetch_weather_context
        weather_context = await fetch_weather_context(
            query=request.message,
            browser_lat=request.latitude,
            browser_lon=request.longitude
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Weather context failed to initialize: %s", e)
        weather_context = None

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
        # Phase 8/9/5: RAG retrieval via Qdrant with Weather
        items = await retrieve_wardrobe_for_query(
            user_id=current_user.id,
            query=request.message,
            top_k=request.top_k,
            season_override=request.season,
            category_override=request.category,
            weather_context=weather_context,
        )
        # Detect which path was taken (Qdrant vs MongoDB fallback)
        from app.services.vector.qdrant_service import qdrant_service
        retrieval_source = "qdrant_vector" if qdrant_service.available else "mongodb_fallback"

    # ------------------------------------------------------------------
    # Resolving Chat Session
    # ------------------------------------------------------------------
    session_id = request.session_id
    if not session_id:
        session_id = str(uuid.uuid4())
        await chat_sessions_collection.insert_one({
            "session_id": session_id,
            "user_id": current_user.id,
            "title": request.message[:40] + ("..." if len(request.message) > 40 else ""),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
    else:
        await chat_sessions_collection.update_one(
            {"session_id": session_id, "user_id": current_user.id},
            {"$set": {"updated_at": datetime.utcnow()}}
        )

    # ------------------------------------------------------------------
    # Record User Query
    # ------------------------------------------------------------------
    await chat_messages_collection.insert_one({
        "message_id": str(uuid.uuid4()),
        "session_id": session_id,
        "role": "user",
        "content": request.message,
        "timestamp": datetime.utcnow(),
    })

    # ------------------------------------------------------------------
    # Retrieve Chat History (Phase 11)
    # ------------------------------------------------------------------
    chat_history = []
    if session_id:
        cursor = chat_messages_collection.find({"session_id": session_id}).sort("timestamp", 1)
        async for doc in cursor:
            # We don't want to include the message we just inserted, as it's the `query` itself.
            if doc["content"] != request.message:
                chat_history.append({"role": doc["role"], "content": doc["content"]})

    # Limit history to last 10 messages to avoid blowing up context
    chat_history = chat_history[-10:]

    # ------------------------------------------------------------------
    # Call StylistService (Phase 10 & 5 & 11)
    # ------------------------------------------------------------------
    try:
        result = await generate_outfit_recommendation(
            query=request.message,
            retrieved_items=items,
            weather_context=weather_context,
            chat_history=chat_history
        )
        
        # ------------------------------------------------------------------
        # Record Assistant Completion
        # ------------------------------------------------------------------
        await chat_messages_collection.insert_one({
            "message_id": str(uuid.uuid4()),
            "session_id": session_id,
            "role": "assistant",
            "content": result.message,
            "timestamp": datetime.utcnow(),
            "outfit": result.outfit.model_dump() if hasattr(result.outfit, "model_dump") else result.outfit.dict(),
        })

        return ChatResponse(
            reply=result.message,
            outfit=result.outfit,
            session_id=session_id,
            retrieval_source=retrieval_source,
            items_retrieved=len(items),
        )
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error


@router.get("/sessions")
async def get_sessions(current_user: UserContext = Depends(get_current_user)):
    """Fetch all chat sessions for the current user."""
    cursor = chat_sessions_collection.find({"user_id": current_user.id}).sort("updated_at", -1)
    sessions = await cursor.to_list(length=50)
    return [
        {
            "session_id": s["session_id"],
            "title": s.get("title", "New Chat"),
            "updated_at": s.get("updated_at")
        }
        for s in sessions
    ]


@router.get("/sessions/{session_id}")
async def get_session_history(
    session_id: str,
    current_user: UserContext = Depends(get_current_user)
):
    """Fetch history for a specific chat session."""
    session = await chat_sessions_collection.find_one({"session_id": session_id, "user_id": current_user.id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    cursor = chat_messages_collection.find({"session_id": session_id}).sort("timestamp", 1)
    messages = await cursor.to_list(length=100)
    
    formatted_messages = []
    for m in messages:
        formatted_messages.append({
            "id": m.get("message_id"),
            "role": m.get("role"),
            "content": m.get("content"),
            "outfit": m.get("outfit"),
        })

    return {"session_id": session_id, "messages": formatted_messages}