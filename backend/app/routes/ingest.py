"""
Phase 5 – Ingestion API Router.

POST /api/v1/ingest
  - Accepts a multipart image upload.
  - Stores original to Supabase (wardrobe-originals bucket).
  - Creates a job document in MongoDB with status "queued".
  - Dispatches process_ingestion as a FastAPI BackgroundTask.
  - Returns 202 Accepted with the job_id immediately.

GET /api/v1/ingest/{job_id}
  - Returns current job status and item IDs when done.
"""

import os
import uuid
import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.security import UserContext
from app.auth.dependencies import get_current_user
from app.database.mongodb import ingestion_jobs_collection
from app.database.models import IngestionJobStatus
from app.services.storage.supabase import supabase_storage
from app.tasks.ingestion import process_ingestion

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingest"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE_MB = 20


# ---------------------------------------------------------------------------
# POST /ingest – kick off ingestion
# ---------------------------------------------------------------------------

@router.post("/", response_model=IngestionJobStatus, status_code=202)
async def ingest_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: UserContext = Depends(get_current_user),
):
    """
    Upload an image containing one or more garments.
    Returns a job_id you can poll with GET /ingest/{job_id}.
    """
    # ------------------------------------------------------------------
    # 1. Basic validation
    # ------------------------------------------------------------------
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file.content_type}'. Accepted: JPEG, PNG, WEBP.",
        )

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB). Maximum allowed is {MAX_SIZE_MB} MB.",
        )

    # ------------------------------------------------------------------
    # 2. Save to local temp dir for processing
    # ------------------------------------------------------------------
    upload_id = uuid.uuid4().hex
    ext = (file.filename or "upload").rsplit(".", 1)[-1].lower()
    ext = ext if ext in ("jpg", "jpeg", "png", "webp") else "jpg"
    local_filename = f"{upload_id}.{ext}"
    local_path = os.path.join(settings.upload_dir, local_filename)

    os.makedirs(settings.upload_dir, exist_ok=True)
    with open(local_path, "wb") as f:
        f.write(contents)

    # ------------------------------------------------------------------
    # 3. Upload original to Supabase (wardrobe-originals bucket)
    # ------------------------------------------------------------------
    original_url = ""
    original_storage_path = f"{current_user.id}/{upload_id}.{ext}"

    try:
        original_url = await supabase_storage.upload_original(
            file_path=local_path,
            user_id=current_user.id,
            upload_id=upload_id,
        )
    except Exception as e:
        logger.warning("[ingest] Supabase upload skipped (%s). Continuing.", e)
        original_url = f"{settings.backend_base_url}/uploads/{local_filename}"

    # ------------------------------------------------------------------
    # 4. Create job document in MongoDB
    # ------------------------------------------------------------------
    job_id = uuid.uuid4().hex
    job_doc = {
        "job_id":               job_id,
        "user_id":              current_user.id,
        "status":               "queued",
        "original_url":         original_url,
        "original_storage_path": original_storage_path,
        "items_found":          0,
        "item_ids":             [],
        "created_at":           datetime.utcnow(),
        "updated_at":           datetime.utcnow(),
    }
    await ingestion_jobs_collection.insert_one(job_doc)

    # ------------------------------------------------------------------
    # 5. Dispatch background task (Phase 21/22: swap for Celery .delay())
    # ------------------------------------------------------------------
    background_tasks.add_task(
        process_ingestion,
        job_id=job_id,
        user_id=current_user.id,
        original_local_path=local_path,
        original_url=original_url,
        original_storage_path=original_storage_path,
        upload_id=upload_id,
    )

    logger.info("[ingest] Job %s queued for user %s", job_id, current_user.id)

    return IngestionJobStatus(
        job_id=job_id,
        status="queued",
        user_id=current_user.id,
        original_path=original_storage_path,
        items_found=0,
        created_at=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# GET /ingest/{job_id} – poll status
# ---------------------------------------------------------------------------

@router.get("/{job_id}", response_model=dict)
async def get_ingest_status(
    job_id: str,
    current_user: UserContext = Depends(get_current_user),
):
    """
    Poll the status of an ingestion job.
    Returns status (queued / processing / done / failed) and item_ids when done.
    """
    doc = await ingestion_jobs_collection.find_one(
        {"job_id": job_id, "user_id": current_user.id},
        {"_id": 0},  # exclude MongoDB _id from response
    )
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found or does not belong to your account.",
        )

    return {
        "job_id":      doc.get("job_id"),
        "status":      doc.get("status"),
        "items_found": doc.get("items_found", 0),
        "item_ids":    doc.get("item_ids", []),
        "error":       doc.get("error"),
        "created_at":  doc.get("created_at"),
        "updated_at":  doc.get("updated_at"),
    }
