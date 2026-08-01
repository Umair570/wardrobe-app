import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from datetime import datetime

from app.database.mongodb import wardrobe_collection, settings
from app.database.models import WardrobeItemOut
# WMVP-14: uncomment once Umair's classification_service is merged
# from app.services.classification_service import classify_image

router = APIRouter(prefix="/upload", tags=["upload"])

ALLOWED_TYPES = {"image/jpeg", "image/png"}

async def save_upload(file: UploadFile, upload_dir: str) -> str:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG/PNG images are supported.")

    os.makedirs(upload_dir, exist_ok=True)
    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(upload_dir, filename)

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty or unreadable.")

    with open(filepath, "wb") as f:
        f.write(contents)

    return filepath

@router.post("/", response_model=WardrobeItemOut)
async def upload_item(file: UploadFile = File(...)):
    filepath = await save_upload(file, settings.upload_dir)

    # WMVP-14: replace None/None with real classify_image(filepath) output
    category, color = None, None

    doc = {
        "image_path": filepath,
        "category": category,
        "color": color,
        "uploaded_at": datetime.utcnow(),
    }
    result = await wardrobe_collection.insert_one(doc)

    return WardrobeItemOut(
        id=str(result.inserted_id),
        image_path=doc["image_path"],
        category=doc["category"],
        color=doc["color"],
        uploaded_at=doc["uploaded_at"],
    )