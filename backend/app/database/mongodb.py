"""
MongoDB client and collection references.

Phase 3 update:
  - Adds an async `init_db_indexes()` function that creates compound indexes
    on the wardrobe_items collection for fast user-scoped queries.
  - Called from main.py startup event.
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

logger = logging.getLogger(__name__)

client = AsyncIOMotorClient(settings.mongodb_uri)
db = client[settings.mongodb_db_name]

# ---------------------------------------------------------------------------
# Collections (Phase 3 schema)
# ---------------------------------------------------------------------------
wardrobe_collection    = db["wardrobe_items"]
outfits_collection     = db["outfits"]
chat_sessions_collection = db["chat_sessions"]
chat_messages_collection = db["chat_messages"]
users_collection       = db["users"]
ingestion_jobs_collection = db["ingestion_jobs"]   # Phase 5: track async jobs
saved_looks_collection   = db["saved_looks"]        # Frontend saved outfits
activity_collection      = db["activity_events"]     # User activity feed


# ---------------------------------------------------------------------------
# Index initialization (idempotent – safe to call on every startup)
# ---------------------------------------------------------------------------

async def init_db_indexes() -> None:
    """
    Create all compound indexes needed for efficient user-scoped queries.
    Motor's create_index is idempotent – it is a no-op when the index already exists.
    """
    try:
        # --- wardrobe_items ---
        # Primary: filter by user, then sort/filter by category / season
        await wardrobe_collection.create_index(
            [("user_id", 1), ("garment.category", 1)],
            name="user_category_idx",
        )
        await wardrobe_collection.create_index(
            [("user_id", 1), ("garment.season", 1)],
            name="user_season_idx",
        )
        await wardrobe_collection.create_index(
            [("user_id", 1), ("created_at", -1)],
            name="user_created_at_idx",
        )

        # --- ingestion_jobs ---
        await ingestion_jobs_collection.create_index(
            [("user_id", 1), ("status", 1)],
            name="job_user_status_idx",
        )
        await ingestion_jobs_collection.create_index(
            [("job_id", 1)],
            unique=True,
            name="job_id_unique_idx",
        )

        # --- outfits ---
        await outfits_collection.create_index(
            [("user_id", 1), ("created_at", -1)],
            name="outfit_user_idx",
        )

        # --- chat_sessions ---
        await chat_sessions_collection.create_index(
            [("user_id", 1), ("created_at", -1)],
            name="session_user_idx",
        )

        # --- chat_messages ---
        await chat_messages_collection.create_index(
            [("session_id", 1), ("timestamp", 1)],
            name="message_session_idx",
        )

        # --- saved_looks ---
        await saved_looks_collection.create_index(
            [("user_id", 1), ("created_at", -1)],
            name="saved_looks_user_idx",
        )

        # --- activity_events ---
        await activity_collection.create_index(
            [("user_id", 1), ("created_at", -1)],
            name="activity_user_idx",
        )

        logger.info("[mongodb] All indexes initialized successfully.")

    except Exception as exc:
        logger.error("[mongodb] Index initialization failed: %s", exc)