"""
Supabase Storage Service — Phase 4 upgrade.

Supports all four user-isolated buckets defined in the roadmap:
  - wardrobe-originals/{user_id}/{upload_id}.jpg
  - wardrobe-cutouts/{user_id}/{item_id}.png
  - body-photos/{user_id}/body.jpg
  - visualizations/{user_id}/{job_id}.png

Backward-compatible: upload_user_file() still works exactly as before.
New methods use the canonical path helpers from constants/storage_paths.py.
"""

import os
import uuid
import logging
from typing import Optional
from supabase import create_client, Client
from app.core.config import settings
from app.constants.storage_paths import (
    ALL_BUCKETS,
    BUCKET_ORIGINALS,
    BUCKET_CUTOUTS,
    BUCKET_BODY_PHOTOS,
    BUCKET_VISUALIZATIONS,
    original_path,
    cutout_path,
    mask_path,
    body_photo_path,
    visualization_path,
)

logger = logging.getLogger(__name__)


class SupabaseStorageService:
    """
    Thin wrapper around the Supabase Storage SDK.
    All public methods return the public URL of the uploaded object.
    """

    def __init__(self):
        self.url = settings.supabase_url
        self.key = settings.supabase_service_role_key or settings.supabase_anon_key
        self.client: Optional[Client] = None

        if self.url and self.key:
            try:
                self.client = create_client(self.url, self.key)
                self._ensure_all_buckets()
            except Exception as e:
                logger.warning("[SupabaseStorageService] Failed to init client: %s", e)

    @property
    def bucket_body(self) -> str:
        return BUCKET_BODY_PHOTOS

    # ------------------------------------------------------------------
    # Bucket management
    # ------------------------------------------------------------------

    def _ensure_all_buckets(self) -> None:
        """Create all four canonical buckets if they don't exist yet."""
        for bucket in ALL_BUCKETS:
            self.ensure_bucket(bucket)

    def ensure_bucket(self, bucket: str) -> None:
        if not self.client:
            return
        try:
            self.client.storage.create_bucket(bucket, options={"public": True})
            logger.info("[SupabaseStorageService] Created bucket '%s'", bucket)
        except Exception as e:
            msg = str(e).lower()
            # Already exists → not an error
            if "already exists" in msg or "conflict" in msg or "duplicate" in msg:
                pass
            else:
                logger.warning("[SupabaseStorageService] Bucket check '%s': %s", bucket, e)

    # ------------------------------------------------------------------
    # Internal upload helper
    # ------------------------------------------------------------------

    def _upload(self, bucket: str, storage_path: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """
        Upload raw bytes to a bucket at storage_path and return the public URL.
        Raises RuntimeError on failure.
        """
        if not self.client:
            fallback = f"{settings.backend_base_url}/fallback/{bucket}/{storage_path}"
            logger.warning("[SupabaseStorageService] Client not configured. Returning fallback URL.")
            return fallback

        try:
            self.client.storage.from_(bucket).upload(
                storage_path,
                data,
                file_options={"content-type": content_type},
            )
        except Exception as e:
            msg = str(e).lower()
            if "already exists" in msg or "duplicate" in msg:
                # File already uploaded — update instead of failing
                try:
                    self.client.storage.from_(bucket).update(
                        storage_path,
                        data,
                        file_options={"content-type": content_type},
                    )
                except Exception as ue:
                    raise RuntimeError(f"Supabase storage upload/update error: {ue}") from ue
            else:
                raise RuntimeError(f"Supabase storage upload error: {e}") from e

        public_url = str(
            self.client.storage.from_(bucket).get_public_url(storage_path)
        ).strip()
        logger.info("[SupabaseStorageService] ✓ %s/%s → %s", bucket, storage_path, public_url)
        return public_url

    def _read_file(self, file_path: str) -> bytes:
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(file_path, "rb") as f:
            return f.read()

    # ------------------------------------------------------------------
    # Phase 4 – canonical upload methods
    # ------------------------------------------------------------------

    async def upload_original(
        self,
        file_path: str,
        user_id: str,
        upload_id: Optional[str] = None,
    ) -> str:
        """
        Store the raw uploaded image.
        Path: wardrobe-originals/{user_id}/{upload_id}.{ext}
        """
        uid = upload_id or uuid.uuid4().hex
        ext = os.path.splitext(file_path)[-1].lstrip(".") or "jpg"
        path = original_path(user_id, uid, ext)
        data = self._read_file(file_path)
        content_type = "image/jpeg" if ext in ("jpg", "jpeg") else "image/png"
        return self._upload(BUCKET_ORIGINALS, path, data, content_type)

    async def upload_cutout(
        self,
        file_path: str,
        user_id: str,
        item_id: str,
    ) -> str:
        """
        Store a segmented garment cutout (transparent PNG).
        Path: wardrobe-cutouts/{user_id}/{item_id}.png
        """
        path = cutout_path(user_id, item_id)
        data = self._read_file(file_path)
        return self._upload(BUCKET_CUTOUTS, path, data, "image/png")

    async def upload_mask(
        self,
        file_path: str,
        user_id: str,
        item_id: str,
    ) -> str:
        """
        Store a binary segmentation mask.
        Path: wardrobe-cutouts/{user_id}/{item_id}_mask.png
        """
        path = mask_path(user_id, item_id)
        data = self._read_file(file_path)
        return self._upload(BUCKET_CUTOUTS, path, data, "image/png")

    async def upload_body_photo(
        self,
        file_path: str,
        user_id: str,
    ) -> str:
        """
        Store the user's body reference photo.
        Path: body-photos/{user_id}/body.jpg
        """
        path = body_photo_path(user_id)
        data = self._read_file(file_path)
        return self._upload(BUCKET_BODY_PHOTOS, path, data, "image/jpeg")

    async def upload_visualization(
        self,
        file_path: str,
        user_id: str,
        job_id: str,
    ) -> str:
        """
        Store a virtual try-on visualization result.
        Path: visualizations/{user_id}/{job_id}.png
        """
        path = visualization_path(user_id, job_id)
        data = self._read_file(file_path)
        return self._upload(BUCKET_VISUALIZATIONS, path, data, "image/png")

    # ------------------------------------------------------------------
    # Backward-compatible generic uploader (used by old upload.py)
    # ------------------------------------------------------------------

    async def upload_user_file(
        self,
        file_path: str,
        user_id: str,
        bucket: str = None,
        filename_override: Optional[str] = None,
    ) -> str:
        """
        Generic uploader kept for backward-compatibility.
        Defaults to wardrobe-originals bucket.
        New code should use the specific upload_* methods above.
        """
        bucket = bucket or BUCKET_ORIGINALS
        self.ensure_bucket(bucket)
        fname = filename_override or os.path.basename(file_path)
        storage_path = f"{user_id}/{uuid.uuid4().hex[:8]}_{fname}"
        data = self._read_file(file_path)
        ext = os.path.splitext(fname)[-1].lstrip(".") or "jpg"
        content_type = "image/jpeg" if ext in ("jpg", "jpeg") else "image/png"
        return self._upload(bucket, storage_path, data, content_type)

    # ------------------------------------------------------------------
    # Deletion helper
    # ------------------------------------------------------------------

    def delete_file(self, bucket: str, storage_path: str) -> None:
        if not self.client:
            return
        try:
            self.client.storage.from_(bucket).remove([storage_path])
            logger.info("[SupabaseStorageService] Deleted %s/%s", bucket, storage_path)
        except Exception as e:
            logger.warning("[SupabaseStorageService] Delete error %s/%s: %s", bucket, storage_path, e)

    async def upload_file_bytes(
        self,
        bucket: str,
        path: str,
        data: bytes,
        content_type: str = "image/jpeg",
    ) -> str:
        """
        Upload raw bytes directly (no local file required).
        Returns the public URL.
        """
        return self._upload(bucket, path, data, content_type)


supabase_storage = SupabaseStorageService()
