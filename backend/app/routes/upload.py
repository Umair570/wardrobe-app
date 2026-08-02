import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.concurrency import run_in_threadpool
from datetime import datetime

from app.database.mongodb import wardrobe_collection, settings
from app.database.models import WardrobeItemOut
from app.ml_loader import process_wardrobe_upload

router = APIRouter(prefix="/upload", tags=["upload"])

ALLOWED_TYPES = {"image/jpeg", "image/png"}

# Map Umair's error codes to appropriate HTTP status codes
ERROR_CODE_STATUS = {
    "NOT_FOUND": 404,
    "BLURRY_IMAGE": 422,
    "SEG_ERROR": 500,
    "NO_CLOTHING": 422,
    "CLASS_ERROR": 500,
}

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

@router.post("/", response_model=list[WardrobeItemOut])
async def upload_item(file: UploadFile = File(...)):
    source_path = await save_upload(file, settings.upload_dir)

    result = await run_in_threadpool(process_wardrobe_upload, source_path)

    if not result["success"]:
        status_code = ERROR_CODE_STATUS.get(result.get("code"), 500)
        raise HTTPException(status_code=status_code, detail=result["error"])

    created_items = []
    for item in result["items"]:
        doc = {
            "source_image": source_path,
            "segmentation_path": item["segmentation_path"],
            "area_ratio": item["area_ratio"],
            "category": item["category"],
            "type": item["type"],
            "style": item["style"],
            "season": item["season"],
            "pattern": item["pattern"],
            "color": item["color"],
            "tags": item["tags"],
            "confidence_scores": item["confidence_scores"],
            "uploaded_at": datetime.utcnow(),
        }
        db_result = await wardrobe_collection.insert_one(doc)
        created_items.append(WardrobeItemOut(id=str(db_result.inserted_id), **doc))

    return created_items