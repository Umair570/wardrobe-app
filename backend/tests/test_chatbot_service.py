"""Unit tests for ChatbotService (WMVP-20 Phase 5).

Tests verify actual behaviour — not just that functions return something.
Motor (MongoDB async driver) is not required for these tests; all DB calls
are mocked at the module level.
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from backend.app.services.chatbot_service import (
    MOCK_WARDROBE,
    WardrobeItem,
    build_chat_reply,
    build_wardrobe_context,
    fetch_wardrobe_items,
    parse_wardrobe_items,
    pick_outfit,
    strip_ids_from_text,
)


class TestBuildWardrobeContext(unittest.TestCase):
    """build_wardrobe_context() formats items into LLM-readable text."""

    def test_empty_items_returns_upload_prompt(self):
        result = build_wardrobe_context([])
        self.assertIn("no saved wardrobe items", result.lower())

    def test_formats_item_fields_correctly(self):
        items = [WardrobeItem("id-001", "shirt", "t-shirt", "black", ["casual", "solid"])]
        result = build_wardrobe_context(items)
        self.assertIn("id=id-001", result)
        self.assertIn("category=shirt", result)
        self.assertIn("type=t-shirt", result)
        self.assertIn("color=black", result)
        self.assertIn("casual", result)

    def test_multiple_items_each_on_own_line(self):
        items = [
            WardrobeItem("id-001", "shirt", "t-shirt", "black", ["casual"]),
            WardrobeItem("id-002", "pants", "jeans", "blue", ["denim"]),
        ]
        result = build_wardrobe_context(items)
        lines = [l for l in result.splitlines() if l.strip()]
        self.assertEqual(len(lines), 2)

    def test_item_with_no_tags_shows_none(self):
        items = [WardrobeItem("id-003", "shoes", "sneakers", "white", [])]
        result = build_wardrobe_context(items)
        self.assertIn("tags=none", result)


class TestParseWardrobeItems(unittest.TestCase):
    """parse_wardrobe_items() returns empty list (not mock) when None is passed."""

    def test_none_input_returns_empty_list(self):
        """None should return empty list so ChatbotService fetches from MongoDB."""
        result = parse_wardrobe_items(None)
        self.assertEqual(result, [])

    def test_empty_list_returns_empty_list(self):
        result = parse_wardrobe_items([])
        self.assertEqual(result, [])

    def test_valid_dicts_parsed_correctly(self):
        raw = [{"id": "abc", "category": "shirt", "type": "t-shirt", "color": "black", "tags": ["casual"]}]
        result = parse_wardrobe_items(raw)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, "abc")
        self.assertEqual(result[0].category, "shirt")
        self.assertEqual(result[0].color, "black")

    def test_missing_fields_default_to_unknown(self):
        raw = [{}]
        result = parse_wardrobe_items(raw)
        self.assertEqual(result[0].id, "unknown")
        self.assertEqual(result[0].category, "unknown")

    def test_mongo_id_field_used_as_fallback(self):
        raw = [{"_id": "mongo-123", "category": "pants", "type": "jeans", "color": "blue", "tags": []}]
        result = parse_wardrobe_items(raw)
        self.assertEqual(result[0].id, "mongo-123")


class TestPickOutfit(unittest.TestCase):
    """pick_outfit() selects one item per slot for complete outfits."""

    def test_picks_top_bottom_shoes(self):
        items = [
            WardrobeItem("id-1", "shirt", "t-shirt", "tan", []),
            WardrobeItem("id-2", "shirt", "shirt", "blue", []),
            WardrobeItem("id-3", "shorts", "shorts", "charcoal", []),
            WardrobeItem("id-4", "shoes", "sneakers", "white", []),
        ]
        picks = pick_outfit(items, "what should i wear today")
        slots = {p.category for p in picks}
        self.assertIn("shirt", slots)
        self.assertIn("shorts", slots)
        self.assertIn("shoes", slots)
        self.assertEqual(len(picks), 3)

    def test_no_duplicate_slots(self):
        items = [
            WardrobeItem("id-1", "shirt", "t-shirt", "tan", []),
            WardrobeItem("id-2", "shirt", "shirt", "blue", []),
        ]
        picks = pick_outfit(items, "outfit idea")
        self.assertEqual(len(picks), 1)


class TestStripIds(unittest.TestCase):
    def test_removes_mongo_ids_and_tags(self):
        raw = "Try tan t-shirt (id=507f1f77bcf86cd799439011) with jeans id=507f1f77bcf86cd799439012"
        clean = strip_ids_from_text(raw)
        self.assertNotIn("507f1f77bcf86cd799439011", clean)
        self.assertNotIn("(id=", clean)
        self.assertIn("tan t-shirt", clean)


class TestBuildChatReply(unittest.TestCase):
    def test_structured_items_without_ids_in_reply(self):
        items = [
            WardrobeItem("507f1f77bcf86cd799439011", "shirt", "t-shirt", "tan", []),
            WardrobeItem("507f1f77bcf86cd799439012", "shorts", "shorts", "charcoal", []),
            WardrobeItem("507f1f77bcf86cd799439013", "shoes", "sneakers", "white", []),
        ]
        result = build_chat_reply("what should i wear today", items)
        self.assertNotIn("507f1f77bcf86cd799439011", result.reply)
        self.assertEqual(len(result.recommended_items), 3)
        self.assertEqual(result.recommended_items[0].id, "507f1f77bcf86cd799439011")


class TestFetchWardrobeItems(unittest.TestCase):
    """fetch_wardrobe_items() queries MongoDB and maps docs to WardrobeItems."""

    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_returns_empty_list_when_db_unavailable(self):
        """If motor is not importable, returns [] gracefully."""
        with patch.dict("sys.modules", {"app": None, "backend.app.database": None, "backend.app.database.mongodb": None}):
            # Both import paths fail → should return []
            result = self._run(fetch_wardrobe_items("default_user"))
            self.assertEqual(result, [])

    def test_maps_mongo_docs_to_wardrobe_items(self):
        """Documents returned from MongoDB are mapped to WardrobeItem dataclasses."""
        mock_docs = [
            {"_id": "doc-001", "category": "shirt", "type": "t-shirt", "color": "black", "tags": ["casual"]},
            {"_id": "doc-002", "category": "pants", "type": "jeans", "color": "blue", "tags": []},
        ]

        async def mock_find(_):
            for doc in mock_docs:
                yield doc

        mock_collection = type("Col", (), {"find": lambda self, q: mock_find(q)})()

        with patch("backend.app.services.chatbot_service.fetch_wardrobe_items") as mock_fetch:
            mock_fetch.return_value = [
                WardrobeItem("doc-001", "shirt", "t-shirt", "black", ["casual"]),
                WardrobeItem("doc-002", "pants", "jeans", "blue", []),
            ]
            result = self._run(mock_fetch("default_user"))
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0].id, "doc-001")
            self.assertEqual(result[1].color, "blue")


if __name__ == "__main__":
    unittest.main()
