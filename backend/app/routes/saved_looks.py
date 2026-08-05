"""
Saved Looks API Router.

Endpoints:
  GET    /saved-looks/          – list the user's saved looks
  POST   /saved-looks/          – save a new look (outfit)
  DELETE /saved-looks/{look_id} – remove a saved look

Uses the dedicated `saved_looks` collection — does NOT touch wardrobe_items,
outfits, or any existing collection.
"""

import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user
from app.core.security import UserContext
from app.database.mongodb import saved_looks_collection, activity_collection

router = APIRouter(prefix="/saved-looks", tags=["saved-looks"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class SaveLookRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    tag: str = Field(default="CASUAL", max_length=30)
    item_ids: List[str] = Field(default_factory=list, max_length=6)
    favorited: bool = False


class SavedLookOut(BaseModel):
    id: str
    name: str
    tag: str
    item_ids: List[str] = []
    images: List[str] = []
    favorited: bool = False
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# GET /saved-looks/ – list all saved looks for the current user
# ---------------------------------------------------------------------------

@router.get("/", response_model=List[SavedLookOut])
async def list_saved_looks(current_user: UserContext = Depends(get_current_user)):
    cursor = saved_looks_collection.find(
        {"user_id": current_user.id}
    ).sort("created_at", -1)
    docs = await cursor.to_list(length=100)

    return [
        SavedLookOut(
            id=str(doc["_id"]),
            name=doc.get("name", "Untitled Look"),
            tag=doc.get("tag", "CASUAL"),
            item_ids=doc.get("item_ids", []),
            images=doc.get("images", []),
            favorited=doc.get("favorited", False),
            created_at=doc.get("created_at"),
        )
        for doc in docs
    ]


# ---------------------------------------------------------------------------
# POST /saved-looks/ – save a new look
# ---------------------------------------------------------------------------

@router.post("/", response_model=SavedLookOut, status_code=201)
async def save_look(
    body: SaveLookRequest,
    current_user: UserContext = Depends(get_current_user),
):
    now = datetime.utcnow()
    doc = {
        "user_id": current_user.id,
        "name": body.name,
        "tag": body.tag.upper(),
        "item_ids": body.item_ids,
        "images": [],
        "favorited": body.favorited,
        "created_at": now,
        "updated_at": now,
    }
    result = await saved_looks_collection.insert_one(doc)
    look_id = str(result.inserted_id)

    # Log activity
    await activity_collection.insert_one({
        "user_id": current_user.id,
        "kind": "favorite",
        "label": f"Saved look **{body.name}**",
        "created_at": now,
    })

    return SavedLookOut(
        id=look_id,
        name=body.name,
        tag=body.tag.upper(),
        item_ids=body.item_ids,
        images=[],
        favorited=body.favorited,
        created_at=now,
    )


# ---------------------------------------------------------------------------
# PATCH /saved-looks/{look_id}/favorite – toggle favorite
# ---------------------------------------------------------------------------

@router.patch("/{look_id}/favorite")
async def toggle_favorite(
    look_id: str,
    current_user: UserContext = Depends(get_current_user),
):
    from bson import ObjectId
    from bson.errors import InvalidId

    try:
        oid = ObjectId(look_id)
    except (InvalidId, Exception):
        raise HTTPException(status_code=400, detail="Invalid look ID")

    doc = await saved_looks_collection.find_one({"_id": oid, "user_id": current_user.id})
    if not doc:
        raise HTTPException(status_code=404, detail="Look not found")

    new_val = not doc.get("favorited", False)
    await saved_looks_collection.update_one(
        {"_id": oid},
        {"$set": {"favorited": new_val, "updated_at": datetime.utcnow()}},
    )
    return {"ok": True, "favorited": new_val}


# ---------------------------------------------------------------------------
# DELETE /saved-looks/{look_id}
# ---------------------------------------------------------------------------

@router.delete("/{look_id}")
async def delete_saved_look(
    look_id: str,
    current_user: UserContext = Depends(get_current_user),
):
    from bson import ObjectId
    from bson.errors import InvalidId

    try:
        oid = ObjectId(look_id)
    except (InvalidId, Exception):
        raise HTTPException(status_code=400, detail="Invalid look ID")

    result = await saved_looks_collection.delete_one({"_id": oid, "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Look not found")

    return {"ok": True}
