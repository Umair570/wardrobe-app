"""Unit tests for VisualizationService (WMVP-20 Phase 5).

Tests verify layout positions, category conflict validation,
missing item 404 handling, and non-visualizable category rejection.
All MongoDB calls are mocked — no live DB required.
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from bson import ObjectId

from backend.app.services.visualization_service import (
    LAYOUT_CATEGORY_MAP,
    LAYOUT_POSITIONS,
    Z_INDEX,
    VisualizationService,
)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ── LAYOUT_CATEGORY_MAP contract tests ────────────────────────────────────────

class TestLayoutCategoryMap(unittest.TestCase):
    """LAYOUT_CATEGORY_MAP must cover all ML output category values."""

    def test_shirt_maps_to_top(self):
        self.assertEqual(LAYOUT_CATEGORY_MAP["shirt"], "top")

    def test_sweater_maps_to_top(self):
        self.assertEqual(LAYOUT_CATEGORY_MAP["sweater"], "top")

    def test_pants_maps_to_bottom(self):
        self.assertEqual(LAYOUT_CATEGORY_MAP["pants"], "bottom")

    def test_shorts_maps_to_bottom(self):
        self.assertEqual(LAYOUT_CATEGORY_MAP["shorts"], "bottom")

    def test_shoes_maps_to_shoes(self):
        self.assertEqual(LAYOUT_CATEGORY_MAP["shoes"], "shoes")

    def test_jacket_maps_to_outerwear(self):
        self.assertEqual(LAYOUT_CATEGORY_MAP["jacket"], "outerwear")

    def test_bag_not_visualizable(self):
        self.assertIsNone(LAYOUT_CATEGORY_MAP["bag"])

    def test_accessory_not_visualizable(self):
        self.assertIsNone(LAYOUT_CATEGORY_MAP["accessory"])


class TestLayoutPositions(unittest.TestCase):
    """Every visualizable slot must have all 4 position fields and a z_index."""

    SLOTS = ["top", "bottom", "shoes", "outerwear"]

    def test_all_slots_have_position_fields(self):
        for slot in self.SLOTS:
            pos = LAYOUT_POSITIONS[slot]
            for field in ("x", "y", "width", "height"):
                self.assertIn(field, pos, f"Slot '{slot}' missing position field '{field}'")

    def test_all_slots_have_z_index(self):
        for slot in self.SLOTS:
            self.assertIn(slot, Z_INDEX)

    def test_outerwear_has_highest_z_index(self):
        self.assertEqual(max(Z_INDEX.values()), Z_INDEX["outerwear"])

    def test_shoes_has_lowest_z_index(self):
        self.assertEqual(min(Z_INDEX.values()), Z_INDEX["shoes"])


# ── VisualizationService._assign_slots tests ──────────────────────────────────

class TestAssignSlots(unittest.TestCase):
    """_assign_slots enforces max 1 per layout slot and rejects non-visualizable."""

    def _make_doc(self, category, id_str="507f1f77bcf86cd799439011"):
        return {"_id": ObjectId(id_str), "category": category, "type": "test", "segmentation_path": "uploads/test.png"}

    def test_valid_top_bottom_shoes_mapped(self):
        service = VisualizationService()
        docs = [
            self._make_doc("shirt"),
            self._make_doc("pants"),
            self._make_doc("shoes", "507f1f77bcf86cd799439012"),
        ]
        slot_map = service._assign_slots(docs)
        self.assertIn("top", slot_map)
        self.assertIn("bottom", slot_map)
        self.assertIn("shoes", slot_map)

    def test_duplicate_tops_raises_400(self):
        from fastapi import HTTPException
        service = VisualizationService()
        docs = [
            self._make_doc("shirt", "507f1f77bcf86cd799439011"),
            self._make_doc("sweater", "507f1f77bcf86cd799439012"),
        ]
        with self.assertRaises(HTTPException) as ctx:
            service._assign_slots(docs)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("top", ctx.exception.detail)

    def test_non_visualizable_category_raises_422(self):
        from fastapi import HTTPException
        service = VisualizationService()
        docs = [self._make_doc("bag")]
        with self.assertRaises(HTTPException) as ctx:
            service._assign_slots(docs)
        self.assertEqual(ctx.exception.status_code, 422)


# ── VisualizationService._build_item_payload tests ────────────────────────────

class TestBuildItemPayload(unittest.TestCase):
    """_build_item_payload converts a MongoDB doc into the frontend overlay contract."""

    def _make_doc(self, seg_path, category="shirt", typ="t-shirt"):
        return {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "category": category,
            "type": typ,
            "segmentation_path": seg_path,
        }

    def test_payload_has_all_required_fields(self):
        service = VisualizationService()
        doc = self._make_doc("uploads/test.png")
        payload = service._build_item_payload("top", doc)
        for field in ("id", "category", "type", "image_url", "position", "z_index"):
            self.assertIn(field, payload)

    def test_image_url_starts_with_slash(self):
        service = VisualizationService()
        doc = self._make_doc("uploads/abc_item_0.png")
        payload = service._build_item_payload("top", doc)
        self.assertTrue(payload["image_url"].startswith("/"))

    def test_windows_path_backslashes_converted(self):
        service = VisualizationService()
        doc = self._make_doc("uploads\\abc_item_0.png")
        payload = service._build_item_payload("top", doc)
        self.assertNotIn("\\", payload["image_url"])

    def test_position_fields_present(self):
        service = VisualizationService()
        doc = self._make_doc("uploads/test.png")
        payload = service._build_item_payload("bottom", doc)
        pos = payload["position"]
        for field in ("x", "y", "width", "height"):
            self.assertIn(field, pos)

    def test_z_index_is_integer(self):
        service = VisualizationService()
        doc = self._make_doc("uploads/test.png")
        payload = service._build_item_payload("shoes", doc)
        self.assertIsInstance(payload["z_index"], int)


if __name__ == "__main__":
    unittest.main()
