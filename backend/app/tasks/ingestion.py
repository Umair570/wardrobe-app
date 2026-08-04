"""
Phase 5 – Multi-Garment Ingestion Task.

This module contains the async function `process_ingestion` that runs
as a FastAPI BackgroundTask (interim).

Phase 21/22: This will be migrated to a Celery task dispatched via RabbitMQ.
The task signature will remain identical so the route code needs zero changes.

Pipeline steps (matching the roadmap flow):
  1. Image validation  (blur / format / dimensions)
  2. Garment segmentation  (SAM-2 via ml pipeline)
  3. Attribute classification  (color / style / season / material)
  4. Store cutouts to Supabase  (wardrobe-cutouts bucket)
  5. Generate CLIP/Fashion embeddings
  6. Upsert vectors + payload into Qdrant
  7. Write full metadata document to MongoDB
  8. Update job status to "done" (or "failed")
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from app.database.mongodb import wardrobe_collection, ingestion_jobs_collection
from app.database.models import WardrobeItemCreate, GarmentSource, GarmentAttributes, GarmentSegmentation, GarmentEmbedding, GarmentConfidence
from app.services.storage.supabase import supabase_storage
from app.services.vector.qdrant_service import qdrant_service
from app.services.embedding.model_registry import embedding_service
from app.constants.storage_paths import BUCKET_CUTOUTS

logger = logging.getLogger(__name__)


async def _update_job(job_id: str, update: dict) -> None:
    """Helper: patch a job document in MongoDB."""
    await ingestion_jobs_collection.update_one(
        {"job_id": job_id},
        {"$set": {**update, "updated_at": datetime.utcnow()}},
    )


async def process_ingestion(
    job_id: str,
    user_id: str,
    original_local_path: str,
    original_url: str,
    original_storage_path: str,
    upload_id: str,
) -> None:
    """
    Full multi-garment ingestion pipeline executed as a background task.

    Args:
        job_id:               UUID string identifying this job (stored in MongoDB).
        user_id:              Authenticated user's Supabase UID.
        original_local_path:  Temp file path on disk (will be cleaned up here).
        original_url:         Public Supabase URL of the already-uploaded original.
        original_storage_path: Supabase storage path for the original image.
        upload_id:            Unique ID used to name the original file in storage.
    """
    logger.info(
        "[ingest][%s] ====== PIPELINE START for user=%s upload=%s ======",
        job_id, user_id, upload_id
    )
    await _update_job(job_id, {"status": "processing"})

    try:
        # ----------------------------------------------------------------
        # Step 1: Image Validation (blur / format / dimensions)
        # ----------------------------------------------------------------
        validation_result = await _validate_image(original_local_path)
        if not validation_result["valid"]:
            logger.warning("[ingest][%s] Validation failed: %s", job_id, validation_result["reason"])
            await _update_job(job_id, {"status": "failed", "error": validation_result["reason"]})
            return

        # ----------------------------------------------------------------
        # Step 2: Garment Detection & SAM-2 Segmentation
        # ----------------------------------------------------------------
        segments = await _run_segmentation(original_local_path)
        logger.info("[ingest][%s] Found %d segment(s)", job_id, len(segments))
        await _update_job(job_id, {"items_found": len(segments)})

        # ----------------------------------------------------------------
        # Steps 3-7: Per-garment processing loop
        # ----------------------------------------------------------------
        inserted_ids = []
        for seg in segments:
            item_id = uuid.uuid4().hex

            # Step 3: Attribute classification
            attributes = await _classify_garment(seg)

            # Step 4: Upload cutout to Supabase
            cutout_url: Optional[str] = None
            mask_url: Optional[str] = None

            if seg.get("cutout_path"):
                try:
                    cutout_url = await supabase_storage.upload_cutout(
                        file_path=seg["cutout_path"],
                        user_id=user_id,
                        item_id=item_id,
                    )
                except Exception as e:
                    logger.warning("[ingest][%s] Cutout upload failed: %s", job_id, e)

            if seg.get("mask_path"):
                try:
                    mask_url = await supabase_storage.upload_mask(
                        file_path=seg["mask_path"],
                        user_id=user_id,
                        item_id=item_id,
                    )
                except Exception as e:
                    logger.warning("[ingest][%s] Mask upload failed: %s", job_id, e)

            # Step 5 & 6: Generate embedding + upsert into Qdrant
            # Priority: ML pipeline embedding → embedding_service fallback
            embedding_vector = seg.get("embedding")   # may be None if ML stub
            embedding_model  = seg.get("embedding_model", "fashion-clip-v1")

            logger.info(
                "[ingest][%s] Step 5: embedding check — pre-existing vector: %s, service available: %s",
                job_id, (embedding_vector is not None), embedding_service.is_available()
            )

            if not embedding_vector and embedding_service.is_available():
                import os
                # Resolve the best local file to embed from
                cutout_path = seg.get("cutout_path")
                logger.info(
                    "[ingest][%s] Resolving embed source — cutout_path=%s, original=%s",
                    job_id, cutout_path, original_local_path
                )
                candidates = [cutout_path, original_local_path]
                embed_source = None

                for cand in candidates:
                    if not cand:
                        continue
                    # Try the path as-is (absolute paths from ML pipeline)
                    if os.path.isfile(cand):
                        embed_source = cand
                        logger.info("[ingest][%s] Embed source resolved: %s", job_id, embed_source)
                        break
                    # Try relative to repo root
                    repo_root = os.path.abspath(
                        os.path.join(os.path.dirname(__file__), "..", "..", "..")
                    )
                    alt_path = os.path.join(repo_root, cand)
                    if os.path.isfile(alt_path):
                        embed_source = alt_path
                        logger.info(
                            "[ingest][%s] Embed source resolved (repo-relative): %s",
                            job_id, embed_source
                        )
                        break

                if embed_source:
                    try:
                        from PIL import Image as PILImage
                        logger.info("[ingest][%s] Opening image for embedding: %s", job_id, embed_source)
                        img = PILImage.open(embed_source).convert("RGB")
                        logger.info("[ingest][%s] Image opened — calling embed_image...", job_id)
                        embedding_vector = embedding_service.embed_image(img)
                        embedding_model  = embedding_service.active_key
                        logger.info(
                            "[ingest][%s] ✅ Embedding generated via %s (dim=%d)",
                            job_id, embedding_model, len(embedding_vector),
                        )
                    except Exception as e:
                        logger.warning(
                            "[ingest][%s] ❌ Embedding failed: %s",
                            job_id, e, exc_info=True
                        )
                else:
                    logger.warning(
                        "[ingest][%s] ❌ No valid image file found to embed. "
                        "Checked candidates: %s",
                        job_id, candidates
                    )
            elif not embedding_service.is_available():
                logger.warning(
                    "[ingest][%s] Embedding service not available — "
                    "check that transformers/torch are installed and EMBEDDING_MODEL is set in .env.",
                    job_id
                )

            embedding_dim = len(embedding_vector) if embedding_vector else 512
            logger.info(
                "[ingest][%s] Final embedding: vector=%s, dim=%d, model=%s",
                job_id,
                "PRESENT" if embedding_vector else "MISSING",
                embedding_dim, embedding_model
            )

            # Upsert into Qdrant — always attempt if vector exists
            if embedding_vector:
                logger.info("[ingest][%s] Step 6: Upserting to Qdrant for item %s...", job_id, item_id)
                upsert_ok = await qdrant_service.upsert_item_vector(
                    item_id=item_id,
                    vector=embedding_vector,
                    user_id=user_id,
                    payload={
                        "category": attributes.get("category"),
                        "type":     attributes.get("type"),
                        "color":    attributes.get("color"),
                        "style":    attributes.get("style"),
                        "season":   attributes.get("season"),
                        "pattern":  attributes.get("pattern"),
                        "tags":     attributes.get("tags", []),
                    },
                )
                if upsert_ok:
                    logger.info(
                        "[ingest][%s] ✅ Qdrant upsert SUCCEEDED for item %s",
                        job_id, item_id
                    )
                else:
                    logger.error(
                        "[ingest][%s] ❌ Qdrant upsert FAILED for item %s — "
                        "check QDRANT_URL and QDRANT_API_KEY in .env",
                        job_id, item_id
                    )
            else:
                logger.warning(
                    "[ingest][%s] ⚠️ No embedding vector — item %s saved to MongoDB only, NOT in Qdrant.",
                    job_id, item_id,
                )

            # Step 7: Write metadata to MongoDB (Phase 3 schema)
            now = datetime.utcnow()
            doc = WardrobeItemCreate(
                user_id=user_id,
                source=GarmentSource(
                    image_url=original_url,
                    storage_path=original_storage_path,
                ),
                garment=GarmentAttributes(
                    category=attributes.get("category"),
                    type=attributes.get("type"),
                    color=attributes.get("color"),
                    style=attributes.get("style"),
                    season=attributes.get("season"),
                    pattern=attributes.get("pattern"),
                    material=attributes.get("material"),
                    tags=attributes.get("tags", []),
                ),
                segmentation=GarmentSegmentation(
                    mask_url=mask_url,
                    cutout_url=cutout_url,
                    bbox=seg.get("bbox"),
                ),
                embedding=GarmentEmbedding(
                    model=embedding_model,
                    dimension=embedding_dim,
                    vector_id=item_id,
                ),
                confidence=GarmentConfidence(
                    segmentation_score=seg.get("segmentation_score"),
                    classification_score=attributes.get("classification_score"),
                ),
                created_at=now,
                updated_at=now,
            )

            result = await wardrobe_collection.insert_one(
                doc.model_dump(exclude_none=True)
            )
            inserted_ids.append(str(result.inserted_id))
            logger.info("[ingest][%s] Item %s saved to MongoDB", job_id, item_id)

            # --- Clean up local cutouts and masks ---
            import os
            for path_key in ["cutout_path", "mask_path"]:
                p = seg.get(path_key)
                if p and os.path.isfile(p):
                    try:
                        os.remove(p)
                        logger.info("[ingest][%s] Cleaned up local file %s", job_id, p)
                    except OSError:
                        pass


        # ----------------------------------------------------------------
        # Step 8: Mark job done
        # ----------------------------------------------------------------
        await _update_job(job_id, {
            "status": "done",
            "items_found": len(inserted_ids),
            "item_ids": inserted_ids,
        })
        logger.info("[ingest][%s] Pipeline complete. %d item(s) ingested.", job_id, len(inserted_ids))

    except Exception as exc:
        logger.error("[ingest][%s] Pipeline crashed: %s", job_id, exc, exc_info=True)
        await _update_job(job_id, {"status": "failed", "error": str(exc)})

    finally:
        # Always clean up the temp file
        import os
        try:
            if original_local_path and os.path.isfile(original_local_path):
                os.remove(original_local_path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Internal pipeline helpers
# (These call into the existing ML loader or return stubs when ML is unavailable)
# ---------------------------------------------------------------------------

async def _validate_image(file_path: str) -> dict:
    """
    Step 1: Validate image quality (blur, format, dimensions).
    Returns {"valid": True} or {"valid": False, "reason": "..."}.
    """
    try:
        from PIL import Image
        import os

        # Format & existence check
        if not os.path.isfile(file_path):
            return {"valid": False, "reason": "File not found"}

        with Image.open(file_path) as img:
            width, height = img.size

        # Minimum dimension check (100x100)
        if width < 100 or height < 100:
            return {"valid": False, "reason": f"Image too small: {width}x{height}"}

        # Maximum file size check: 20 MB
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if size_mb > 20:
            return {"valid": False, "reason": f"File too large: {size_mb:.1f} MB (max 20 MB)"}

        return {"valid": True}

    except Exception as e:
        return {"valid": False, "reason": f"Validation error: {e}"}


async def _run_segmentation(file_path: str) -> list:
    """
    Step 2: Run SAM-2 garment segmentation via the existing ML pipeline.
    Falls back to a single-item stub so the pipeline never hard-fails.

    Each returned dict has:
      - cutout_path: Optional[str]  – local path to transparent PNG cutout
      - mask_path:   Optional[str]  – local path to binary mask PNG
      - bbox:        Optional[list] – [x1, y1, x2, y2]
      - embedding:   Optional[list] – CLIP float vector
      - segmentation_score: Optional[float]
    """
    try:
        from fastapi.concurrency import run_in_threadpool
        from app.ml_loader import process_wardrobe_upload

        result = await run_in_threadpool(process_wardrobe_upload, file_path)
        if result.get("success"):
            # Normalise ML output into our expected dict shape
            return [
                {
                    "cutout_path":        item.get("segmentation_path"),
                    "mask_path":          item.get("mask_path"),
                    "bbox":               item.get("bbox"),
                    "embedding":          item.get("embedding"),
                    "embedding_model":    item.get("embedding_model", "fashion-clip-v1"),
                    "segmentation_score": item.get("confidence_scores", {}).get("segmentation"),
                    # Classification attributes forwarded directly
                    **{k: item.get(k) for k in ("category", "type", "color", "style", "season", "pattern", "material", "tags")},
                }
                for item in result.get("items", [])
            ]
    except Exception as e:
        logger.warning("[ingest] ML segmentation unavailable (%s). Using stub.", e)

    # Stub: single un-segmented item
    return [{"cutout_path": None, "mask_path": None, "bbox": None, "embedding": None, "segmentation_score": None}]


async def _classify_garment(seg: dict) -> dict:
    """
    Step 3: Extract garment attributes.
    Attributes may already be present from the ML pipeline output.
    Falls back to empty strings.
    """
    return {
        "category":            seg.get("category"),
        "type":                seg.get("type"),
        "color":               seg.get("color"),
        "style":               seg.get("style"),
        "season":              seg.get("season"),
        "pattern":             seg.get("pattern"),
        "material":            seg.get("material"),
        "tags":                seg.get("tags", []),
        "classification_score": seg.get("classification_score"),
    }
