"""
Semantic retrieval over the user's wardrobe.

    query text
        │
        ▼
    FashionCLIP text encoder  (same embedding space as the stored garment images)
        │
        ▼
    Qdrant search
        ├─ HARD FILTER: user_id == caller
        ├─ OPTIONAL:    category | season | style | color
        └─ SEMANTIC:    cosine distance vs. the query vector
        │
        ▼
    List[WardrobeItem]

Fallback chain:
    Qdrant unavailable / 0 results → MongoDB full fetch
    MongoDB unavailable            → empty list

The stylist agent calls `search_wardrobe`, which wraps these helpers and lets the
LLM decide what to search for and how often. `retrieve_wardrobe_for_query` is the
single-shot entry point kept for non-agent callers.
"""

import logging
from typing import Optional

from app.database.mongodb import wardrobe_collection
from app.services.embedding.model_registry import embedding_service
from app.services.stylist.schemas import WardrobeItem
from app.services.vector.qdrant_service import qdrant_service

logger = logging.getLogger(__name__)


async def fetch_wardrobe_items(user_id: str) -> list[WardrobeItem]:
    """Fetch all items for the user directly from MongoDB."""
    items: list[WardrobeItem] = []
    query = {"$or": [{"user_id": user_id}, {"user_id": {"$exists": False}}]} if user_id else {}

    async for doc in wardrobe_collection.find(query):
        garment = doc.get("garment") or {}
        items.append(
            WardrobeItem(
                id=str(doc["_id"]),
                category=str(doc.get("category") or garment.get("category") or "unknown"),
                type=str(doc.get("type") or garment.get("type") or "unknown"),
                color=str(doc.get("color") or garment.get("color") or "unknown"),
                style=doc.get("style") or garment.get("style"),
                season=doc.get("season") or garment.get("season"),
                pattern=doc.get("pattern") or garment.get("pattern"),
                tags=[str(t) for t in (doc.get("tags") or garment.get("tags") or [])],
            )
        )
    return items


async def retrieve_wardrobe_for_query(
    user_id: str,
    query: str,
    top_k: int = 8,
    season_override: Optional[str] = None,
    category_override: Optional[str] = None,
) -> list[WardrobeItem]:
    """
    Embed `query` with the active model and run a filtered vector search.

    Falls back to a full MongoDB fetch when Qdrant is unavailable or returns
    nothing, so an un-indexed wardrobe still produces recommendations.
    """
    logger.info("[retrieval] user=%s query=%r top_k=%d", user_id, query[:60], top_k)

    query_vector: Optional[list[float]] = None
    if embedding_service.is_available():
        try:
            query_vector, latency_ms = embedding_service.timed_embed_text(query)
            logger.debug("[retrieval] Embedded in %.1f ms (dim=%d)", latency_ms, len(query_vector))
        except Exception as e:
            logger.warning("[retrieval] Embedding failed (%s); using filter-only search.", e)
    else:
        logger.warning("[retrieval] Embedding model unavailable; using filter-only Qdrant scroll.")

    qdrant_results: list[dict] = []
    if qdrant_service.available:
        qdrant_results = await qdrant_service.search_items(
            user_id=user_id,
            query_vector=query_vector,      # None → scroll, no semantic ranking
            category_filter=category_override,
            season_filter=season_override,
            limit=top_k,
        )
        logger.info("[retrieval] Qdrant returned %d item(s).", len(qdrant_results))
    else:
        logger.warning("[retrieval] Qdrant unavailable; skipping vector search.")

    if qdrant_results:
        return _qdrant_results_to_wardrobe_items(qdrant_results)

    logger.info("[retrieval] Falling back to MongoDB fetch for user=%s.", user_id)
    return await fetch_wardrobe_items(user_id)


def _qdrant_results_to_wardrobe_items(results: list[dict]) -> list[WardrobeItem]:
    """
    Convert Qdrant payload dicts into WardrobeItem instances.

    Payload shape: {id, mongo_id, user_id, category, type, color, style, season,
    pattern, tags, score?}. `mongo_id` is what the rest of the system uses as the
    item identifier — the Qdrant point id is a UUID derived from it.
    """
    items = []
    for r in results:
        tags = r.get("tags", [])
        if not isinstance(tags, list):
            tags = []

        items.append(
            WardrobeItem(
                id=r.get("mongo_id") or str(r.get("id", "unknown")),
                category=r.get("category") or "unknown",
                type=r.get("type") or "unknown",
                color=r.get("color") or "unknown",
                style=r.get("style"),
                season=r.get("season"),
                pattern=r.get("pattern"),
                tags=tags,
            )
        )
    return items
