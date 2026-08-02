"""Visualization service for the wardrobe 2D overlay MVP (WMVP-20).

Responsibilities:
  1. Fetch selected wardrobe items from MongoDB by ID.
  2. Map each item's ML category to a layout slot (top / bottom / shoes / outerwear).
  3. Validate that at most one item per slot is selected.
  4. Build a standardized overlay response the frontend can render directly.

The frontend's only job is: for each item in the response, render the PNG at
(position.x%, position.y%) with (position.width% x position.height%) dimensions
and the given z_index.  No additional layout logic is needed client-side.
"""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status


# ── Category → layout slot mapping ────────────────────────────────────────────
# Keys are the values Umair's ML pipeline saves to MongoDB's `category` field
# (i.e. the *broad* category from CATEGORY_MAP in ml/classification/model.py,
#  NOT the raw granular label strings).
# None means the category is not visualizable in the 2D overlay (bags, accessories).

LAYOUT_CATEGORY_MAP: dict[str, str | None] = {
    # Tops
    "shirt": "top",
    "sweater": "top",
    "suit": "top",
    # Bottoms
    "pants": "bottom",
    "shorts": "bottom",
    "skirt": "bottom",
    "dress": "bottom",
    # Footwear
    "shoes": "shoes",
    # Outerwear (can layer over a top)
    "jacket": "outerwear",
    # Non-visualizable
    "bag": None,
    "accessory": None,
}

# ── Layout positions per slot (percentage of container dimensions) ─────────────
# Coordinates align with the vector mannequin silhouette:
# x / y = center of the slot (percent), width / height = slot size (percent).

LAYOUT_POSITIONS: dict[str, dict[str, float]] = {
    "top":       {"x": 50, "y": 30, "width": 72, "height": 28},
    "bottom":    {"x": 50, "y": 58, "width": 56, "height": 36},
    "shoes":     {"x": 50, "y": 88, "width": 38, "height": 10},
    "outerwear": {"x": 50, "y": 31, "width": 78, "height": 30},
}


# z-index: outerwear sits on top of everything, shoes at the bottom
Z_INDEX: dict[str, int] = {
    "outerwear": 4,
    "top":       3,
    "bottom":    2,
    "shoes":     1,
}


class VisualizationService:
    """Builds 2D overlay response from selected wardrobe item IDs."""

    async def build_response(self, item_ids: list[str]) -> dict[str, Any]:
        """Full pipeline: fetch -> validate -> build layout -> return response."""
        docs = await self._get_selected_items(item_ids)
        slot_map = self._assign_slots(docs)
        return {
            "mode": "overlay",
            "items": [self._build_item_payload(slot, doc) for slot, doc in slot_map.items()],
        }

    # ── Private helpers ────────────────────────────────────────────────────────

    async def _get_selected_items(self, item_ids: list[str]) -> list[dict]:
        """Fetch wardrobe docs from MongoDB for the given IDs."""
        try:
            from app.database.mongodb import wardrobe_collection  # type: ignore[import]
        except ImportError:
            from backend.app.database.mongodb import wardrobe_collection  # type: ignore[import]

        object_ids: list[ObjectId] = []
        for raw_id in item_ids:
            try:
                object_ids.append(ObjectId(raw_id))
            except InvalidId:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"'{raw_id}' is not a valid item ID.",
                )

        docs: list[dict] = []
        async for doc in wardrobe_collection.find({"_id": {"$in": object_ids}}):
            docs.append(doc)

        found_ids = {str(doc["_id"]) for doc in docs}
        missing = [rid for rid in item_ids if rid not in found_ids]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Items not found: {', '.join(missing)}",
            )

        return docs

    def _assign_slots(self, docs: list[dict]) -> dict[str, dict]:
        """Map each doc to a layout slot, enforcing max 1 per slot."""
        slot_map: dict[str, dict] = {}
        for doc in docs:
            category = str(doc.get("category", "")).lower()
            slot = LAYOUT_CATEGORY_MAP.get(category)

            if slot is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"Category '{category}' (item {doc['_id']}) cannot be "
                        "visualized in the 2D overlay."
                    ),
                )

            if slot in slot_map:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Only one item of type '{slot}' can be selected for visualization.",
                )

            slot_map[slot] = doc

        return slot_map

    def _build_item_payload(self, slot: str, doc: dict) -> dict[str, Any]:
        """Convert a MongoDB doc + slot into the frontend overlay payload."""
        seg_path: str = doc.get("segmentation_path", "")
        # Normalise filesystem path → browser-accessible URL.
        # StaticFiles may be mounted at /uploads OR the ML pipeline writes to
        # ml/outputs/. Either way, strip leading drive/directory up to the
        # known sub-path roots and prepend a single '/'.
        normalised = seg_path.replace("\\", "/")
        for marker in ("uploads/", "ml/outputs/", "ml/"):
            idx = normalised.lower().find(marker)
            if idx != -1:
                image_url = "/" + normalised[idx:]
                break
        else:
            # Fallback: ensure at least a leading slash
            image_url = normalised if normalised.startswith("/") else "/" + normalised

        return {
            "id": str(doc["_id"]),
            "category": slot,
            "type": str(doc.get("type", "unknown")),
            "image_url": image_url,
            "position": LAYOUT_POSITIONS[slot],
            "z_index": Z_INDEX[slot],
        }

