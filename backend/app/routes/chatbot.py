"""FastAPI route for the wardrobe chatbot.

The stylist is a tool-calling agent: the LLM decides when to check the weather
and what to search for, retrieval runs through FashionCLIP + Qdrant, and the
answer comes back as three outfit options the user can pick between and send
straight to the visualization endpoint.
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user
from app.core.security import UserContext
from app.database.mongodb import chat_messages_collection, chat_sessions_collection
from app.services.agent.agent_service import run_stylist_agent
from app.services.agent.tools import ToolContext
from app.services.stylist.schemas import OutfitOption, OutfitRecommendation

router = APIRouter(prefix="/chat", tags=["chatbot"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1_000)
    session_id: Optional[str] = Field(default=None, description="Current chat session ID")
    # Browser geolocation, forwarded so the weather tool can resolve "here".
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    # Legacy: the frontend may still pass items directly. They seed the agent's
    # known-item set so IDs validate, but the agent still searches for itself.
    wardrobe_items: list[dict[str, Any]] | None = None


class WeatherSummary(BaseModel):
    location: str
    condition: str
    temperature_c: float
    feels_like_c: float
    temperature_band: str
    require: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    outfits: list[OutfitOption] = Field(default_factory=list)
    # Back-compat with the single-outfit frontend: mirrors outfits[0].
    outfit: OutfitRecommendation = Field(default_factory=OutfitRecommendation)
    session_id: str
    weather: Optional[WeatherSummary] = None
    items_retrieved: int = 0
    tools_used: list[str] = Field(default_factory=list)


def _weather_summary(report) -> Optional[WeatherSummary]:
    if report is None:
        return None
    return WeatherSummary(
        location=report.location,
        condition=report.condition,
        temperature_c=report.temperature_c,
        feels_like_c=report.feels_like_c,
        temperature_band=report.dress_code.temperature_band,
        require=report.dress_code.require,
        avoid=report.dress_code.avoid,
    )


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: UserContext = Depends(get_current_user),
) -> ChatResponse:
    """Run the stylist agent and return up to three outfit options."""

    # ------------------------------------------------------------------
    # Session bookkeeping
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
            {"$set": {"updated_at": datetime.utcnow()}},
        )

    # ------------------------------------------------------------------
    # Prior turns, fetched BEFORE recording the new message so the current
    # query is not duplicated into its own history.
    # ------------------------------------------------------------------
    history_docs = (
        await chat_messages_collection.find({"session_id": session_id})
        .sort("timestamp", 1)
        .to_list(length=100)
    )
    chat_history = [
        {"role": doc.get("role"), "content": doc.get("content")}
        for doc in history_docs
        if doc.get("role") in ("user", "assistant") and doc.get("content")
    ][-10:]

    await chat_messages_collection.insert_one({
        "message_id": str(uuid.uuid4()),
        "session_id": session_id,
        "role": "user",
        "content": request.message,
        "timestamp": datetime.utcnow(),
    })

    # ------------------------------------------------------------------
    # Run the agent
    # ------------------------------------------------------------------
    ctx = ToolContext(
        user_id=current_user.id,
        browser_lat=request.latitude,
        browser_lon=request.longitude,
    )

    if request.wardrobe_items:
        ctx.remember([
            {
                "id": str(item.get("id") or item.get("_id") or ""),
                "category": item.get("category"),
                "type": item.get("type"),
                "color": item.get("color"),
                "style": item.get("style"),
                "season": item.get("season"),
                "pattern": item.get("pattern"),
            }
            for item in request.wardrobe_items
        ])

    try:
        result = await run_stylist_agent(
            query=request.message,
            ctx=ctx,
            chat_history=chat_history,
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error

    response = result.response

    await chat_messages_collection.insert_one({
        "message_id": str(uuid.uuid4()),
        "session_id": session_id,
        "role": "assistant",
        "content": response.message,
        "timestamp": datetime.utcnow(),
        "outfits": [o.model_dump() for o in response.outfits],
    })

    return ChatResponse(
        reply=response.message,
        outfits=response.outfits,
        outfit=response.primary,
        session_id=session_id,
        weather=_weather_summary(ctx.weather_report),
        items_retrieved=result.items_seen,
        tools_used=result.tool_calls_made,
    )


@router.get("/sessions")
async def get_sessions(current_user: UserContext = Depends(get_current_user)):
    """Fetch all chat sessions for the current user."""
    cursor = chat_sessions_collection.find({"user_id": current_user.id}).sort("updated_at", -1)
    sessions = await cursor.to_list(length=50)
    return [
        {
            "session_id": s["session_id"],
            "title": s.get("title", "New Chat"),
            "updated_at": s.get("updated_at"),
        }
        for s in sessions
    ]


@router.get("/sessions/{session_id}")
async def get_session_history(
    session_id: str,
    current_user: UserContext = Depends(get_current_user),
):
    """Fetch history for a specific chat session."""
    session = await chat_sessions_collection.find_one(
        {"session_id": session_id, "user_id": current_user.id}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    cursor = chat_messages_collection.find({"session_id": session_id}).sort("timestamp", 1)
    messages = await cursor.to_list(length=100)

    return {
        "session_id": session_id,
        "messages": [
            {
                "id": m.get("message_id"),
                "role": m.get("role"),
                "content": m.get("content"),
                # Newer turns store `outfits`; older ones stored a single `outfit`.
                "outfits": m.get("outfits") or ([m["outfit"]] if m.get("outfit") else []),
            }
            for m in messages
        ],
    }

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: UserContext = Depends(get_current_user),
):
    """Delete a specific chat session and all its messages."""
    session = await chat_sessions_collection.find_one(
        {"session_id": session_id, "user_id": current_user.id}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await chat_sessions_collection.delete_one({"session_id": session_id, "user_id": current_user.id})
    await chat_messages_collection.delete_many({"session_id": session_id})

    return {"ok": True}
