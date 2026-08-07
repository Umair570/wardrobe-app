"""
Activity feed API Router.

Endpoints:
  GET  /activity/  – list recent activity for the current user

Uses the dedicated `activity_events` collection — does NOT touch wardrobe_items
or any existing collection. Activity is automatically logged by other routes
(upload, saved_looks, chatbot) when they insert into this collection.
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.core.security import UserContext
from app.database.mongodb import activity_collection


router = APIRouter(prefix="/activity", tags=["activity"])


class ActivityOut(BaseModel):
    id: str
    label: str
    kind: str
    timestamp: str
    created_at: Optional[datetime] = None


def _relative_time(dt: datetime) -> str:
    """Convert a datetime to a human-friendly relative time string."""
    now = datetime.utcnow()
    diff = now - dt
    seconds = diff.total_seconds()
    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        m = int(seconds // 60)
        return f"{m}m ago"
    elif seconds < 86400:
        h = int(seconds // 3600)
        return f"{h}h ago"
    elif seconds < 172800:
        return "Yesterday"
    else:
        d = int(seconds // 86400)
        return f"{d} days ago"


@router.get("/", response_model=List[ActivityOut])
async def get_activity(current_user: UserContext = Depends(get_current_user)):
    """Return the 20 most recent activity events for the current user."""
    cursor = activity_collection.find(
        {"user_id": current_user.id}
    ).sort("created_at", -1).limit(20)

    docs = await cursor.to_list(length=20)
    return [
        ActivityOut(
            id=str(doc["_id"]),
            label=doc.get("label", ""),
            kind=doc.get("kind", "add"),
            timestamp=_relative_time(doc["created_at"]) if doc.get("created_at") else "",
            created_at=doc.get("created_at"),
        )
        for doc in docs
    ]
