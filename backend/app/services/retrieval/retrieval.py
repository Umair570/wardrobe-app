"""
Phase 8 & 9 – Semantic RAG Retrieval Pipeline.

Replaces the raw MongoDB context dump with vector pre-filtering:

    User query text
        │
        ▼
    Text Embedding (active embedding model from registry)
        │
        ▼
    Qdrant Hybrid Search
        ├─ HARD FILTER: user_id == current_user.id
        ├─ OPTIONAL:   season | category | style filters
        └─ SEMANTIC:   cosine distance vs. query vector
        │
        ▼
    Top-K Items (default: 8)
        │
        ▼
    Returns List[WardrobeItem]  ← compatible with ChatbotService
        │
        ▼
    Groq LLM (Phase 10) receives only relevant items, not full wardrobe dump

Fallback chain:
    Qdrant unavailable / 0 results → MongoDB full fetch (old behaviour)
    MongoDB unavailable → empty list → ChatbotService uses MOCK_WARDROBE
"""

import logging
import re
from typing import Optional

from app.services.stylist.schemas import WardrobeItem
from app.services.vector.qdrant_service import qdrant_service
from app.services.embedding.model_registry import embedding_service
from app.database.mongodb import wardrobe_collection

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Query parser – extract filter hints from free text
# ---------------------------------------------------------------------------

_SEASON_KEYWORDS = {
    "summer":   "summer",
    "winter":   "winter",
    "spring":   "spring",
    "autumn":   "autumn",
    "fall":     "autumn",
    "all-season": "all-season",
    "year-round": "all-season",
}

_CATEGORY_KEYWORDS = {
    "shirt":    "top",
    "t-shirt":  "top",
    "top":      "top",
    "blouse":   "top",
    "sweater":  "top",
    "pants":    "bottom",
    "trousers": "bottom",
    "jeans":    "bottom",
    "shorts":   "bottom",
    "skirt":    "bottom",
    "bottom":   "bottom",
    "shoes":    "shoes",
    "boots":    "shoes",
    "sneakers": "shoes",
    "heels":    "shoes",
    "jacket":   "outerwear",
    "coat":     "outerwear",
    "blazer":   "outerwear",
    "outerwear": "outerwear",
}

_STYLE_KEYWORDS = {
    "formal":   "formal",
    "casual":   "casual",
    "business": "formal",
    "smart":    "formal",
    "sporty":   "casual",
    "athletic": "casual",
    "elegant":  "formal",
}


def _parse_query_filters(query: str) -> dict:
    """
    Extract optional Qdrant payload filters from the user's free-text query.
    Returns a dict with keys: season, category, style (all Optional[str]).
    """
    q = query.lower()

    season   = next((v for k, v in _SEASON_KEYWORDS.items()  if k in q), None)
    category = next((v for k, v in _CATEGORY_KEYWORDS.items() if k in q), None)
    style    = next((v for k, v in _STYLE_KEYWORDS.items()   if k in q), None)

    return {"season": season, "category": category, "style": style}


async def fetch_wardrobe_items(user_id: str) -> list[WardrobeItem]:
    """Fallback: Fetch all items for the user directly from MongoDB."""
    items: list[WardrobeItem] = []
    query = {"$or": [{"user_id": user_id}, {"user_id": {"$exists": False}}]} if user_id else {}
    
    async for doc in wardrobe_collection.find(query):
        items.append(
            WardrobeItem(
                id=str(doc["_id"]),
                category=str(doc.get("category") or "unknown"),
                type=str(doc.get("type") or "unknown"),
                color=str(doc.get("color") or "unknown"),
                tags=[str(t) for t in doc.get("tags", [])],
            )
        )
    return items


# ---------------------------------------------------------------------------
# Core retrieval function (Phase 8 & 9)
# ---------------------------------------------------------------------------

async def retrieve_wardrobe_for_query(
    user_id: str,
    query: str,
    top_k: int = 8,
    season_override: Optional[str] = None,
    category_override: Optional[str] = None,
) -> list[WardrobeItem]:
    """
    Main retrieval entry point.  Called by the chatbot route in place of the
    old raw MongoDB dump.

    Steps:
      1. Parse soft filters from query text.
      2. Embed the query using the active embedding model.
      3. Run Qdrant hybrid search (hard user_id filter + optional field filters
         + cosine vector similarity).
      4. Convert Qdrant results → List[WardrobeItem].
      5. Fallback to MongoDB full-fetch if Qdrant returns 0 results.

    Args:
        user_id:           Authenticated user's Supabase UID.
        query:             User's natural-language styling request.
        top_k:             Maximum items to retrieve from Qdrant.
        season_override:   Force a specific season filter (optional).
        category_override: Force a specific category filter (optional).

    Returns:
        List of WardrobeItem instances ready for ChatbotService.
    """
    logger.info("[retrieval] Starting RAG retrieval for user=%s query='%s'", user_id, query[:60])

    # ------------------------------------------------------------------
    # Step 1: Parse soft filters from query
    # ------------------------------------------------------------------
    filters = _parse_query_filters(query)
    season   = season_override   or filters["season"]
    category = category_override or filters["category"]
    style    = filters["style"]

    logger.debug(
        "[retrieval] Parsed filters – season=%s category=%s style=%s",
        season, category, style,
    )

    # ------------------------------------------------------------------
    # Step 2: Embed the query text
    # ------------------------------------------------------------------
    query_vector: Optional[list[float]] = None

    if embedding_service.is_available():
        try:
            query_vector, latency_ms = embedding_service.timed_embed_text(query)
            logger.debug(
                "[retrieval] Text embedded in %.1f ms (dim=%d)",
                latency_ms, len(query_vector),
            )
        except Exception as e:
            logger.warning("[retrieval] Embedding failed (%s). Falling back to filter-only search.", e)
            query_vector = None
    else:
        logger.warning(
            "[retrieval] Embedding model not available "
            "(model not downloaded yet). Using filter-only Qdrant scroll."
        )

    # ------------------------------------------------------------------
    # Step 3: Qdrant hybrid search
    # ------------------------------------------------------------------
    qdrant_results: list[dict] = []

    if qdrant_service.available:
        qdrant_results = await qdrant_service.search_items(
            user_id=user_id,
            query_vector=query_vector,     # None → scroll (no semantic ranking)
            category_filter=category,
            season_filter=season,
            style_filter=style,
            limit=top_k,
        )
        logger.info(
            "[retrieval] Qdrant returned %d item(s) for user=%s",
            len(qdrant_results), user_id,
        )
    else:
        logger.warning("[retrieval] Qdrant unavailable. Skipping vector search.")

    # ------------------------------------------------------------------
    # Step 4: Convert Qdrant results → WardrobeItem
    # ------------------------------------------------------------------
    if qdrant_results:
        items = _qdrant_results_to_wardrobe_items(qdrant_results)
        logger.info("[retrieval] Returning %d item(s) from Qdrant.", len(items))
        return items

    # ------------------------------------------------------------------
    # Step 5: Fallback – Qdrant gave 0 results (no vectors indexed yet, or
    # Qdrant is down). Pull from MongoDB directly (old behaviour).
    # ------------------------------------------------------------------
    logger.info(
        "[retrieval] Qdrant returned 0 results. Falling back to MongoDB fetch for user=%s.",
        user_id,
    )
    mongo_items = await fetch_wardrobe_items(user_id)
    logger.info("[retrieval] MongoDB fallback: %d item(s) found.", len(mongo_items))
    return mongo_items


# ---------------------------------------------------------------------------
# Result conversion
# ---------------------------------------------------------------------------

def _qdrant_results_to_wardrobe_items(results: list[dict]) -> list[WardrobeItem]:
    """
    Convert Qdrant payload dicts into WardrobeItem instances.

    Qdrant payload shape (Phase 3/7 schema):
        {id, mongo_id, user_id, category, type, color, style, season, tags, score?, …}
    """
    items = []
    for r in results:
        # mongo_id is stored in payload; fall back to Qdrant point id
        item_id = r.get("mongo_id") or str(r.get("id", "unknown"))

        # Garment can be in flat payload keys (Phase 7 upsert) or nested (future)
        category = r.get("category") or "unknown"
        typ      = r.get("type")     or "unknown"
        color    = r.get("color")    or "unknown"
        tags     = r.get("tags", [])
        if not isinstance(tags, list):
            tags = []

        items.append(
            WardrobeItem(
                id=item_id,
                category=category,
                type=typ,
                color=color,
                tags=tags,
            )
        )
    return items


# ---------------------------------------------------------------------------
# Retrieval stats helper (used by the chatbot route for debug metadata)
# ---------------------------------------------------------------------------

def retrieval_stats(
    qdrant_results: list[dict],
    mongo_used: bool = False,
) -> dict:
    return {
        "source":       "mongodb_fallback" if mongo_used else "qdrant_vector",
        "items_count":  len(qdrant_results),
        "top_score":    round(qdrant_results[0]["score"], 4) if qdrant_results and "score" in qdrant_results[0] else None,
    }
