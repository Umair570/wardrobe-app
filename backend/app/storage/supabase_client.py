"""
Supabase storage client wrapper.
Handles uploading wardrobe item images and returning public URLs.
"""

import os
import uuid
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not (SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY):
    raise RuntimeError(
        "Supabase credentials not set. Define SUPABASE_URL and either SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY in .env."
    )

# Prefer service role key for admin actions like bucket creation
API_KEY = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY
client = create_client(SUPABASE_URL, API_KEY)

DEFAULT_BUCKET = os.getenv("SUPABASE_BUCKET", "wardrobe-images")

def _ensure_bucket(bucket: str) -> None:
    """Create the bucket if it does not already exist.
    Uses the service role key if available; if creation fails due to permissions,
    we assume the bucket already exists or the anon key lacks rights, and we simply log.
    """
    try:
        client.storage.create_bucket(bucket, public=True)
        print(f"[supabase] Created bucket '{bucket}'")
    except Exception as e:
        # If bucket already exists, the API returns a Conflict error (code 409)
        # or a permission error when using anon key. Log and continue.
        msg = str(e).lower()
        if "already exists" in msg or "conflict" in msg:
            # Bucket already exists – nothing to do
            pass
        elif "unauthorized" in msg or "forbidden" in msg:
            # Likely using anon key without write permission; proceed assuming bucket exists.
            print(f"[supabase] Warning: unable to create bucket '{bucket}' (unauthorized). Assuming it exists.")
        else:
            print(f"[supabase] Unexpected error creating bucket '{bucket}': {e}")

async def upload_file(file_path: str, bucket: str = DEFAULT_BUCKET) -> str:
    """Upload a local file to Supabase storage and return a public URL.
    The function ensures the bucket exists (idempotently) and then uploads.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Ensure bucket exists before upload
    _ensure_bucket(bucket)

    filename = os.path.basename(file_path)
    storage_path = f"{uuid.uuid4().hex}_{filename}"
    # Read file bytes
    with open(file_path, "rb") as f:
        data = f.read()

    # Upload – supabase-py v2 raises on error, no need to inspect .error
    try:
        client.storage.from_(bucket).upload(
            storage_path,
            data,
        )
    except Exception as e:
        raise RuntimeError(f"Supabase upload error: {e}") from e

    # Get public URL — supabase-py v2 may return PublicUrlResponse, not str
    public_url = str(client.storage.from_(bucket).get_public_url(storage_path)).strip()
    print(f"[supabase] Uploaded → {public_url}")
    return public_url
