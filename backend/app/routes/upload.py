"""
Legacy upload route — Phase 3 schema upgrade.

This route (POST /upload) is kept for backward compatibility with the existing
frontend. It now writes to MongoDB using the Phase 3 nested schema (garment,
source, segmentation, embedding, confidence sub-documents) and uses the
embedding_service fallback so Qdrant is indexed even without a full ML pipeline.

New projects should use POST /ingest which is fully async (job-based).
"""

import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from datetime import datetime

from app.core.config import settings
from app.core.security import UserContext
from app.auth.dependencies import get_current_user
from app.database.mongodb import wardrobe_collection
from app.database.models import (
    WardrobeItemOut,
    GarmentSource, GarmentAttributes,
    GarmentSegmentation, GarmentEmbedding, GarmentConfidence,
)
from app.ml_loader import process_wardrobe_upload
from app.services.storage.supabase import supabase_storage
from app.services.vector.qdrant_service import qdrant_service
from app.services.embedding.model_registry import embedding_service

router = APIRouter(prefix="/upload", tags=["upload"])

ALLOWED_TYPES = {"image/jpeg", "image/png"}

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
async def upload_item(
    file: UploadFile = File(...),
    current_user: UserContext = Depends(get_current_user),
):
    # 1. Save file locally for processing
    source_path = await save_upload(file, settings.upload_dir)

    # 2. Run ML segmentation and classification
    result = await run_in_threadpool(process_wardrobe_upload, source_path)

    # 3. Upload original image to Supabase (wardrobe-originals bucket)
    upload_id = os.path.splitext(os.path.basename(source_path))[0]
    ext = os.path.splitext(source_path)[-1].lstrip(".")
    original_storage_path = f"{current_user.id}/{upload_id}.{ext}"
    image_url = None

    try:
        image_url = await supabase_storage.upload_original(
            file_path=source_path,
            user_id=current_user.id,
            upload_id=upload_id,
        )
    except Exception as e:
        print(f"[upload] Warning: Supabase storage upload failed: {e}")
        image_url = f"{settings.backend_base_url}/uploads/{os.path.basename(source_path)}"

    # 4. Clean up local uploaded file
    try:
        os.remove(source_path)
    except OSError:
        pass

    if not result.get("success"):
        status_code = ERROR_CODE_STATUS.get(result.get("code"), 500)
        raise HTTPException(status_code=status_code, detail=result.get("error", "ML pipeline error"))

    created_items = []
    for item in result.get("items", []):
        item_id = uuid.uuid4().hex
        cutout_path = item.get("segmentation_path")

        # --- Embedding: ML pipeline first, embedding_service fallback ---
        embedding_vector = item.get("embedding")
        embedding_model  = item.get("embedding_model", "fashion-clip-v1")

        if not embedding_vector and embedding_service.is_available():
            embed_source = cutout_path if cutout_path and os.path.isfile(cutout_path) else None
            if embed_source:
                try:
                    from PIL import Image as PILImage
                    img = PILImage.open(embed_source).convert("RGB")
                    embedding_vector = embedding_service.embed_image(img)
                    embedding_model  = embedding_service.active_key
                except Exception as e:
                    print(f"[upload] Embedding fallback failed: {e}")

        # --- Store the transparent garment cutout ---
        # Everything downstream wants the isolated garment, not the photo it came
        # from: the 2D overlay layers cutouts on a mannequin, and FASHN VTON is
        # given this URL as the garment to put on the user. Without it every item
        # from one upload shares the original photo and the try-on is meaningless.
        cutout_url = None
        if cutout_path and os.path.isfile(cutout_path):
            try:
                cutout_url = await supabase_storage.upload_cutout(
                    file_path=cutout_path,
                    user_id=current_user.id,
                    item_id=item_id,
                )
            except Exception as e:
                print(f"[upload] Warning: cutout upload failed for {item_id}: {e}")

        # --- Build Phase 3 schema document ---
        now = datetime.utcnow()
        doc = {
            "user_id": current_user.id,

            # Phase 3 nested structure
            "source": GarmentSource(
                image_url=image_url,
                storage_path=original_storage_path,
            ).model_dump(),
            "garment": GarmentAttributes(
                category=item.get("category"),
                type=item.get("type"),
                color=item.get("color"),
                style=item.get("style"),
                season=item.get("season"),
                pattern=item.get("pattern"),
                tags=item.get("tags", []),
            ).model_dump(),
            "segmentation": GarmentSegmentation(
                cutout_url=cutout_url,
                bbox=item.get("bbox"),
            ).model_dump(),
            "embedding": GarmentEmbedding(
                model=embedding_model,
                dimension=len(embedding_vector) if embedding_vector else 512,
                vector_id=item_id,
            ).model_dump(),
            "confidence": GarmentConfidence(
                segmentation_score=item.get("confidence_scores", {}).get("segmentation"),
                classification_score=item.get("confidence_scores", {}).get("classification"),
            ).model_dump(),

            # Legacy flat fields — kept so WardrobeItemOut still works
            "source_image":       source_path,
            "image_url":          image_url,
            "cutout_url":         cutout_url,
            "segmentation_path":  item.get("segmentation_path", ""),
            "area_ratio":         item.get("area_ratio"),
            "category":           item.get("category"),
            "type":               item.get("type"),
            "style":              item.get("style"),
            "season":             item.get("season"),
            "pattern":            item.get("pattern"),
            "color":              item.get("color"),
            "tags":               item.get("tags", []),
            "confidence_scores":  item.get("confidence_scores", {}),
            "uploaded_at":        now,
            "created_at":         now,
            "updated_at":         now,
        }

        db_result = await wardrobe_collection.insert_one(doc)
        mongo_item_id = str(db_result.inserted_id)

        # --- Upsert into Qdrant ---
        if embedding_vector:
            await qdrant_service.upsert_item_vector(
                item_id=mongo_item_id,
                vector=embedding_vector,
                user_id=current_user.id,
                payload={
                    "category": item.get("category"),
                    "type":     item.get("type"),
                    "color":    item.get("color"),
                    "style":    item.get("style"),
                    "season":   item.get("season"),
                    "pattern":  item.get("pattern"),
                    "tags":     item.get("tags", []),
                },
            )
        else:
            print(f"[upload] No embedding for item {mongo_item_id} — Qdrant skipped.")

        created_items.append(
            WardrobeItemOut(
                id=mongo_item_id,
                user_id=current_user.id,
                category=item.get("category"),
                type=item.get("type"),
                style=item.get("style"),
                season=item.get("season"),
                pattern=item.get("pattern"),
                color=item.get("color"),
                tags=item.get("tags", []),
                confidence_scores=item.get("confidence_scores", {}),
                source_image=source_path,
                image_url=image_url,
                segmentation_path=item.get("segmentation_path", ""),
                area_ratio=item.get("area_ratio"),
                uploaded_at=now,
            )
        )

    return created_items