"""
Profile API Router.

Endpoints:
  GET  /api/v1/profile            – fetch current user's profile metadata
  POST /api/v1/profile/body-photo – upload a body photo to the body-photos bucket
  DELETE /api/v1/profile/body-photo – remove the body photo
"""

import logging
import io
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.auth.dependencies import get_current_user
from app.core.security import UserContext
from app.services.storage.supabase import supabase_storage
from app.database.mongodb import users_collection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profile", tags=["profile"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


class ProfileOut(BaseModel):
    user_id: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    body_photo_url: Optional[str] = None
    updated_at: Optional[datetime] = None


@router.get("/", response_model=ProfileOut)
async def get_profile(current_user: UserContext = Depends(get_current_user)):
    """Fetch the current user's stored profile."""
    doc = await users_collection.find_one({"user_id": current_user.id}, {"_id": 0})
    if not doc:
        # Return a minimal profile for users who haven't set one yet
        return ProfileOut(
            user_id=current_user.id,
            email=current_user.email,
        )
    return ProfileOut(
        user_id=doc.get("user_id", current_user.id),
        email=doc.get("email", current_user.email),
        display_name=doc.get("display_name"),
        avatar_url=doc.get("avatar_url"),
        body_photo_url=doc.get("body_photo_url"),
        updated_at=doc.get("updated_at"),
    )


@router.post("/body-photo", response_model=ProfileOut)
async def upload_body_photo(
    file: UploadFile = File(...),
    save_profile: bool = True,
    current_user: UserContext = Depends(get_current_user),
):
    """
    Upload or replace the user's body photo used for virtual try-on.
    Stored in the body-photos Supabase bucket.
    """
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file.content_type}'. Use JPEG, PNG or WEBP.",
        )

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    size_mb = len(contents) / (1024 * 1024)
    if size_mb > 10:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB). Max 10 MB.",
        )

    # Upload to Supabase body-photos bucket
    ext = (file.filename or "photo").rsplit(".", 1)[-1].lower()
    ext = ext if ext in ("jpg", "jpeg", "png", "webp") else "jpg"
    
    filename = f"body.{ext}" if save_profile else f"body_temp.{ext}"
    storage_path = f"{current_user.id}/{filename}"

    try:
        body_photo_url = await supabase_storage.upload_file_bytes(
            bucket=supabase_storage.bucket_body,
            path=storage_path,
            data=contents,
            content_type=file.content_type or "image/jpeg",
        )
    except Exception as e:
        logger.error("[profile] Body photo upload failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

    now = datetime.utcnow()
    
    # Upsert user profile document only if requested
    if save_profile:
        await users_collection.update_one(
            {"user_id": current_user.id},
            {
                "$set": {
                    "user_id": current_user.id,
                    "email": current_user.email,
                    "body_photo_url": body_photo_url,
                    "updated_at": now,
                }
            },
            upsert=True,
        )
    else:
        # Just return the URL back without committing it as their active profile picture
        return ProfileOut(
            user_id=current_user.id,
            email=current_user.email,
            body_photo_url=body_photo_url,
            updated_at=now,
        )

    logger.info("[profile] Body photo uploaded for user %s: %s", current_user.id, body_photo_url)
    return ProfileOut(
        user_id=current_user.id,
        email=current_user.email,
        body_photo_url=body_photo_url,
        updated_at=now,
    )


@router.delete("/body-photo")
async def delete_body_photo(current_user: UserContext = Depends(get_current_user)):
    """Remove the user's body photo."""
    await users_collection.update_one(
        {"user_id": current_user.id},
        {"$unset": {"body_photo_url": ""}, "$set": {"updated_at": datetime.utcnow()}},
    )
    logger.info("[profile] Body photo cleared for user %s", current_user.id)
    return {"ok": True}
