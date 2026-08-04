"""
Phase 8/9 Tests – Semantic RAG Retrieval Pipeline.

Tests run without a live Qdrant or MongoDB connection by mocking those services.
Run with: pytest backend/tests/test_retrieval.py -v
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Test 1: Query filter parser
# ---------------------------------------------------------------------------

def test_parse_summer_formal():
    from app.services.retrieval.retrieval import _parse_query_filters
    result = _parse_query_filters("What should I wear for a formal summer dinner?")
    assert result["season"]   == "summer"
    assert result["style"]    == "formal"
    assert result["category"] is None   # no specific garment type mentioned


def test_parse_winter_outerwear():
    from app.services.retrieval.retrieval import _parse_query_filters
    result = _parse_query_filters("I need a warm jacket for winter")
    assert result["season"]   == "winter"
    assert result["category"] == "outerwear"


def test_parse_casual_shoes():
    from app.services.retrieval.retrieval import _parse_query_filters
    result = _parse_query_filters("Casual sneakers for today")
    assert result["style"]    == "casual"
    assert result["category"] == "shoes"


def test_parse_no_filters():
    from app.services.retrieval.retrieval import _parse_query_filters
    result = _parse_query_filters("What should I wear?")
    assert result["season"]   is None
    assert result["category"] is None
    assert result["style"]    is None


# ---------------------------------------------------------------------------
# Test 2: Qdrant result → WardrobeItem conversion
# ---------------------------------------------------------------------------

def test_qdrant_results_to_wardrobe_items():
    from app.services.retrieval.retrieval import _qdrant_results_to_wardrobe_items
    results = [
        {
            "id":       "abc123-uuid",
            "mongo_id": "507f1f77bcf86cd799439011",
            "user_id":  "user_1",
            "category": "top",
            "type":     "oxford shirt",
            "color":    "white",
            "tags":     ["business", "classic"],
            "score":    0.94,
        },
        {
            "id":       "def456-uuid",
            "mongo_id": "507f1f77bcf86cd799439012",
            "user_id":  "user_1",
            "category": "bottom",
            "type":     "trousers",
            "color":    "black",
            "tags":     [],
            "score":    0.91,
        },
    ]
    items = _qdrant_results_to_wardrobe_items(results)

    assert len(items) == 2
    assert items[0].id       == "507f1f77bcf86cd799439011"
    assert items[0].category == "top"
    assert items[0].color    == "white"
    assert items[1].category == "bottom"
    assert items[1].tags     == []


def test_qdrant_result_missing_mongo_id_falls_back_to_point_id():
    from app.services.retrieval.retrieval import _qdrant_results_to_wardrobe_items
    results = [{"id": "fallback-point-id", "category": "shoes", "type": "boots", "color": "brown"}]
    items = _qdrant_results_to_wardrobe_items(results)
    assert items[0].id == "fallback-point-id"


# ---------------------------------------------------------------------------
# Test 3: retrieve_wardrobe_for_query — Qdrant happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_retrieve_uses_qdrant_when_available():
    """When Qdrant returns results, they should be used (not MongoDB)."""
    from app.services.retrieval.retrieval import retrieve_wardrobe_for_query

    fake_qdrant_results = [
        {"id": "q1", "mongo_id": "aaa", "category": "top",  "type": "shirt",  "color": "white", "tags": [], "score": 0.95},
        {"id": "q2", "mongo_id": "bbb", "category": "bottom","type": "jeans",  "color": "blue",  "tags": [], "score": 0.88},
    ]

    with patch("app.services.retrieval.retrieval.qdrant_service") as mock_qdrant, \
         patch("app.services.retrieval.retrieval.embedding_service") as mock_embed:

        mock_qdrant.available = True
        mock_qdrant.search_items = AsyncMock(return_value=fake_qdrant_results)
        mock_embed.is_available.return_value = True
        mock_embed.timed_embed_text.return_value = ([0.1] * 512, 42.0)

        items = await retrieve_wardrobe_for_query(
            user_id="user_test",
            query="What should I wear for a casual summer day?",
        )

    assert len(items) == 2
    assert items[0].id       == "aaa"
    assert items[0].category == "top"


# ---------------------------------------------------------------------------
# Test 4: retrieve_wardrobe_for_query — fallback to MongoDB when Qdrant empty
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_retrieve_falls_back_to_mongodb_when_qdrant_empty():
    """When Qdrant returns 0 results, should fall back to MongoDB fetch."""
    from app.services.retrieval.retrieval import retrieve_wardrobe_for_query
    from app.services.stylist.schemas import WardrobeItem

    mongo_items = [
        WardrobeItem(id="m1", category="shoes", type="sneakers", color="white", tags=[]),
    ]

    with patch("app.services.retrieval.retrieval.qdrant_service") as mock_qdrant, \
         patch("app.services.retrieval.retrieval.embedding_service") as mock_embed, \
         patch("app.services.retrieval.retrieval.fetch_wardrobe_items", new=AsyncMock(return_value=mongo_items)):

        mock_qdrant.available = True
        mock_qdrant.search_items = AsyncMock(return_value=[])  # 0 results
        mock_embed.is_available.return_value = False

        items = await retrieve_wardrobe_for_query(
            user_id="user_test",
            query="Show me something casual",
        )

    assert len(items) == 1
    assert items[0].id == "m1"


# ---------------------------------------------------------------------------
# Test 5: retrieve_wardrobe_for_query — Qdrant fully unavailable
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_retrieve_falls_back_when_qdrant_unavailable():
    """When Qdrant is unavailable (not connected), should go straight to MongoDB."""
    from app.services.retrieval.retrieval import retrieve_wardrobe_for_query
    from app.services.stylist.schemas import WardrobeItem

    mongo_items = [
        WardrobeItem(id="mongo1", category="top", type="t-shirt", color="black", tags=["casual"]),
        WardrobeItem(id="mongo2", category="bottom", type="jeans", color="blue", tags=["casual"]),
    ]

    with patch("app.services.retrieval.retrieval.qdrant_service") as mock_qdrant, \
         patch("app.services.retrieval.retrieval.embedding_service") as mock_embed, \
         patch("app.services.retrieval.retrieval.fetch_wardrobe_items", new=AsyncMock(return_value=mongo_items)):

        mock_qdrant.available = False   # Qdrant down
        mock_embed.is_available.return_value = False

        items = await retrieve_wardrobe_for_query(
            user_id="user_test",
            query="formal dinner look",
        )

    assert len(items) == 2
    assert items[0].id == "mongo1"


# ---------------------------------------------------------------------------
# Test 6: Season and category overrides are passed to Qdrant
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_overrides_passed_to_qdrant():
    from app.services.retrieval.retrieval import retrieve_wardrobe_for_query

    with patch("app.services.retrieval.retrieval.qdrant_service") as mock_qdrant, \
         patch("app.services.retrieval.retrieval.embedding_service") as mock_embed, \
         patch("app.services.retrieval.retrieval.fetch_wardrobe_items", new=AsyncMock(return_value=[])):

        mock_qdrant.available = True
        mock_qdrant.search_items = AsyncMock(return_value=[])
        mock_embed.is_available.return_value = False

        await retrieve_wardrobe_for_query(
            user_id="user_test",
            query="something to wear",
            season_override="winter",
            category_override="outerwear",
        )

        mock_qdrant.search_items.assert_called_once()
        call_kwargs = mock_qdrant.search_items.call_args.kwargs
        assert call_kwargs["season_filter"]   == "winter"
        assert call_kwargs["category_filter"] == "outerwear"
        assert call_kwargs["user_id"]         == "user_test"
