"""
Phase 7 – Qdrant Vector Service (canonical location: services/vector/).

Key Phase 7 improvements over the old retrieval/qdrant.py:
  1. Vector points store the exact MongoDB _id reference in their payload.
  2. Payload indexes on user_id/category/season/style/color for O(1) filtering.
  3. Collection initialization delegates to collections.py (handles dim + indexes).
  4. Embedding dimension is read from the active embedding model in the registry.
  5. upsert_item_vector() accepts full Phase 3 payload schema (all garment fields).
  6. delete_item_vector() for item removal support.
  7. get_item_vector() to retrieve a specific point by ID.

Canonical import:
    from app.services.vector.qdrant_service import qdrant_service
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from functools import partial

from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qmodels
    QDRANT_AVAILABLE = True
except Exception as e:
    QDRANT_AVAILABLE = False
    logger.warning("[QdrantService] qdrant-client import failed: %s. Vector operations disabled.", e)
    print(f"CRITICAL DEBUG: qdrant_client import failed with error: {repr(e)}")


class QdrantService:
    """
    Manages all interactions with the Qdrant vector database.

    Design decisions (Phase 7):
    - Point ID = MongoDB wardrobe_item string ObjectId (stored in payload as mongo_id too).
      This creates a direct link between Qdrant points and MongoDB documents.
    - Hard user_id filter on EVERY search — user isolation is enforced at DB level.
    - All garment payload fields are indexed for fast hybrid (filter + vector) search.
    """

    def __init__(self):
        self.client: Optional[Any] = None
        self.collection_name = settings.qdrant_collection

        if not QDRANT_AVAILABLE:
            return

        if not settings.qdrant_url:
            logger.warning("[QdrantService] QDRANT_URL not set. Vector operations disabled.")
        self._connect()

    def _connect(self) -> None:
        print(f"DEBUG [QdrantService] _connect called. QDRANT_AVAILABLE={QDRANT_AVAILABLE}, url={repr(settings.qdrant_url)}")
        if not QDRANT_AVAILABLE or not settings.qdrant_url:
            print("DEBUG [QdrantService] Early return from _connect!")
            return
        try:
            print("DEBUG [QdrantService] Attempting to initialize QdrantClient...")
            self.client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key or None,
                timeout=15,
            )
            from app.services.vector.collections import ensure_collection
            ensure_collection(self.client, self.collection_name)
            logger.info("[QdrantService] Connected to Qdrant at %s", settings.qdrant_url)
            print("DEBUG [QdrantService] Successfully connected!")
        except Exception as e:
            logger.error("[QdrantService] Connection attempt failed: %s", e)
            print(f"DEBUG [QdrantService] Connection Exception: {e}")
            self.client = None

    @property
    def available(self) -> bool:
        if self.client is None:
            print(f"DEBUG [QdrantService] available property: client is None. qdrant_url={repr(settings.qdrant_url)}")
            if settings.qdrant_url:
                self._connect()
        return self.client is not None

    async def _run_blocking(self, func, *args, **kwargs):
        """Helper to run synchronous Qdrant calls in an executor."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(func, *args, **kwargs))

    # ------------------------------------------------------------------
    # Upsert (insert or update) a single wardrobe item vector
    # ------------------------------------------------------------------

    async def upsert_item_vector(
        self,
        item_id: str,           # MongoDB ObjectId string → used as Qdrant point ID
        vector: List[float],
        user_id: str,
        payload: Dict[str, Any],
    ) -> bool:
        """
        Insert or update a wardrobe item's vector in Qdrant.
        """
        if not self.available:
            logger.warning("[QdrantService] Qdrant client unavailable. Check QDRANT_URL/API_KEY. Skipping item %s.", item_id)
            return False

        if not vector or len(vector) == 0:
            logger.warning("[QdrantService] Empty vector for item %s — skipping upsert.", item_id)
            return False

        # Ensure vector is a standard Python list of native floats
        try:
            clean_vector = [float(v) for v in vector]
        except Exception as e:
            logger.error("[QdrantService] Invalid vector format for item %s: %s", item_id, e)
            return False

        full_payload: Dict[str, Any] = {
            "user_id":  user_id,
            "mongo_id": item_id,
            **payload,
        }

        if "tags" in full_payload and not isinstance(full_payload["tags"], list):
            full_payload["tags"] = []

        try:
            logger.info("[QdrantService] Upserting point %s (mongo_id=%s) for user %s into '%s'...", _to_qdrant_id(item_id), item_id, user_id, self.collection_name)
            await self._run_blocking(
                self.client.upsert,
                collection_name=self.collection_name,
                points=[
                    qmodels.PointStruct(
                        id=_to_qdrant_id(item_id),
                        vector=clean_vector,
                        payload=full_payload,
                    )
                ],
            )
            logger.info("[QdrantService] ✅ Successfully upserted point %s for user %s", item_id, user_id)
            return True
        except Exception as e:
            logger.error("[QdrantService] ❌ Upsert failed for item %s: %s", item_id, str(e), exc_info=True)
            return False

    # ------------------------------------------------------------------
    # Batch upsert
    # ------------------------------------------------------------------

    async def upsert_batch(self, points: List[Dict[str, Any]]) -> int:
        """Upsert multiple points in a single request."""
        if not self.available or not points:
            return 0

        qdrant_points = []
        for p in points:
            full_payload = {
                "user_id":  p["user_id"],
                "mongo_id": p["item_id"],
                **p.get("payload", {}),
            }
            qdrant_points.append(
                qmodels.PointStruct(
                    id=_to_qdrant_id(p["item_id"]),
                    vector=p["vector"],
                    payload=full_payload,
                )
            )

        try:
            logger.info("[QdrantService] Batch upserting %d points", len(qdrant_points))
            await self._run_blocking(
                self.client.upsert,
                collection_name=self.collection_name,
                points=qdrant_points,
            )
            return len(qdrant_points)
        except Exception as e:
            logger.error("[QdrantService] Batch upsert failed: %s", e)
            return 0

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def search_items(
        self,
        user_id: str,
        query_vector: Optional[List[float]] = None,
        category_filter: Optional[str] = None,
        season_filter: Optional[str] = None,
        style_filter: Optional[str] = None,
        color_filter: Optional[str] = None,
        limit: int = 8,
    ) -> List[Dict[str, Any]]:
        """Search wardrobe items for a specific user."""
        if not self.available:
            return []

        must_filters = [
            qmodels.FieldCondition(
                key="user_id",
                match=qmodels.MatchValue(value=user_id),
            )
        ]

        for field, value in [
            ("category", category_filter),
            ("season",   season_filter),
            ("style",    style_filter),
            ("color",    color_filter),
        ]:
            if value:
                must_filters.append(
                    qmodels.FieldCondition(
                        key=field,
                        match=qmodels.MatchValue(value=value),
                    )
                )

        query_filter = qmodels.Filter(must=must_filters)

        try:
            if query_vector:
                results = await self._run_blocking(
                    self.client.search,
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=query_filter,
                    limit=limit,
                    with_payload=True,
                )
                return [
                    {"id": r.id, "score": round(r.score, 4), **r.payload}
                    for r in results
                ]
            else:
                scroll_res, _ = await self._run_blocking(
                    self.client.scroll,
                    collection_name=self.collection_name,
                    scroll_filter=query_filter,
                    limit=limit,
                    with_payload=True,
                )
                return [{"id": r.id, **r.payload} for r in scroll_res]

        except Exception as e:
            logger.error("[QdrantService] Search failed: %s", e)
            return []

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete_item_vector(self, item_id: str) -> bool:
        """Remove a vector point by its MongoDB item ID."""
        if not self.available:
            return False
        try:
            await self._run_blocking(
                self.client.delete,
                collection_name=self.collection_name,
                points_selector=qmodels.PointIdsList(
                    points=[_to_qdrant_id(item_id)]
                ),
            )
            logger.info("[QdrantService] Deleted point %s", item_id)
            return True
        except Exception as e:
            logger.error("[QdrantService] Delete failed for %s: %s", item_id, e)
            return False

    # ------------------------------------------------------------------
    # Get single point
    # ------------------------------------------------------------------

    async def get_item_vector(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single vector point by its MongoDB item ID."""
        if not self.available:
            return None
        try:
            results = await self._run_blocking(
                self.client.retrieve,
                collection_name=self.collection_name,
                ids=[_to_qdrant_id(item_id)],
                with_payload=True,
                with_vectors=False,
            )
            if results:
                r = results[0]
                return {"id": r.id, **r.payload}
            return None
        except Exception as e:
            logger.error("[QdrantService] Get failed for %s: %s", item_id, e)
            return None

    # ------------------------------------------------------------------
    # Collection stats
    # ------------------------------------------------------------------

    def collection_info(self) -> Dict[str, Any]:
        """Return basic collection statistics (Sync wrapper)."""
        if not self.available:
            return {"available": False}
        try:
            info = self.client.get_collection(self.collection_name)
            points = (
                getattr(info, "points_count", None)
                or getattr(info, "vectors_count", None)
                or 0
            )
            indexed = getattr(info, "indexed_vectors_count", None)
            return {
                "available":             True,
                "collection":            self.collection_name,
                "points_count":          points,
                "indexed_vectors_count": indexed,
                "status":                str(getattr(info, "status", "unknown")),
            }
        except Exception as e:
            return {"available": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Helper: convert MongoDB hex ObjectId string to a Qdrant-compatible UUID
# ---------------------------------------------------------------------------

def _to_qdrant_id(mongo_id: str) -> str:
    padded = mongo_id.ljust(32, "0")[:32]
    return f"{padded[0:8]}-{padded[8:12]}-{padded[12:16]}-{padded[16:20]}-{padded[20:32]}"


# ---------------------------------------------------------------------------
# Singleton – canonical import for the whole application
# ---------------------------------------------------------------------------

qdrant_service = QdrantService()
