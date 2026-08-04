"""
Storage bucket + path constants.

Phase 4 – Defines the four Supabase Storage buckets and the helper that
builds a user-isolated path inside any of them, matching the roadmap layout:

    wardrobe-originals/{user_id}/{upload_id}.jpg
    wardrobe-cutouts/{user_id}/{item_id}.png
    body-photos/{user_id}/body.jpg
    visualizations/{user_id}/{job_id}.png
"""

from app.core.config import settings


# ---------------------------------------------------------------------------
# Canonical bucket names (pulled from settings so they're overridable via .env)
# ---------------------------------------------------------------------------

BUCKET_ORIGINALS:     str = settings.supabase_bucket_wardrobe   # "wardrobe-originals"
BUCKET_CUTOUTS:       str = settings.supabase_bucket_cutouts    # "wardrobe-cutouts"
BUCKET_BODY_PHOTOS:   str = settings.supabase_bucket_body       # "body-photos"
BUCKET_VISUALIZATIONS: str = settings.supabase_bucket_generated  # "visualizations"

ALL_BUCKETS = [
    BUCKET_ORIGINALS,
    BUCKET_CUTOUTS,
    BUCKET_BODY_PHOTOS,
    BUCKET_VISUALIZATIONS,
]


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def original_path(user_id: str, upload_id: str, ext: str = "jpg") -> str:
    """wardrobe-originals/{user_id}/{upload_id}.jpg"""
    return f"{user_id}/{upload_id}.{ext}"


def cutout_path(user_id: str, item_id: str) -> str:
    """wardrobe-cutouts/{user_id}/{item_id}.png"""
    return f"{user_id}/{item_id}.png"


def mask_path(user_id: str, item_id: str) -> str:
    """wardrobe-cutouts/{user_id}/{item_id}_mask.png"""
    return f"{user_id}/{item_id}_mask.png"


def body_photo_path(user_id: str) -> str:
    """body-photos/{user_id}/body.jpg"""
    return f"{user_id}/body.jpg"


def visualization_path(user_id: str, job_id: str) -> str:
    """visualizations/{user_id}/{job_id}.png"""
    return f"{user_id}/{job_id}.png"
