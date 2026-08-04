"""Visualization service for the wardrobe 2D overlay & IDM-VTON try-on (WMVP-20).

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

import os
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
    "underwear": "top",
    "swimwear": "top",
    # Bottoms
    "pants": "bottom",
    "shorts": "bottom",
    "skirt": "bottom",
    "sleepwear": "bottom", # Mostly pajama bottoms
    # Full body
    "dress": "dress",
    "traditional": "dress",
    "one-piece": "dress",
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
    "dress":     {"x": 50, "y": 50, "width": 70, "height": 55},
    "shoes":     {"x": 50, "y": 88, "width": 38, "height": 10},
    "outerwear": {"x": 50, "y": 31, "width": 78, "height": 30},
}


# z-index: outerwear sits on top of everything, shoes at the bottom
Z_INDEX: dict[str, int] = {
    "outerwear": 4,
    "top":       3,
    "dress":     3,
    "bottom":    2,
    "shoes":     1,
}


class VisualizationService:
    """Builds 2D overlay or IDM-VTON image try-on response from selected item IDs."""

    async def build_response(
        self,
        item_ids: list[str],
        mode: str = "overlay",
        user_body_photo_url: str | None = None,
    ) -> dict[str, Any]:
        """Full pipeline: fetch -> validate -> build layout or generate AI image -> return response.

        NOTE: `user_body_photo_url` is required for `mode="ai"`. Real image-to-image
        try-on needs (a) the user's body photo and (b) the actual garment cutout
        images (segmentation_path on each doc) — not just a text description built
        from color/type. Wire this through to image_generation_service.generate_image
        once that function accepts image inputs. Uses IDM-VTON via HuggingFace Spaces.
        """
        docs = await self._get_selected_items(item_ids)
        slot_map = self._assign_slots(docs)
        items_payload = [self._build_item_payload(slot, doc) for slot, doc in slot_map.items()]

        if mode == "ai":
            if not user_body_photo_url:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="AI try-on mode requires a user body photo.",
                )

            from app.services.visualization import get_vton_model
            from app.services.visualization.schemas import VirtualTryOnRequest

            person_image_url = user_body_photo_url
            
            # Extract garment URLs by category slot
            top_garment_url = next((self._to_absolute_url(item["image_url"]) for item in items_payload if item["category"] in ["top", "outerwear"]), None)
            bottom_garment_url = next((self._to_absolute_url(item["image_url"]) for item in items_payload if item["category"] == "bottom"), None)
            dress_garment_url = next((self._to_absolute_url(item["image_url"]) for item in items_payload if item["category"] == "dress"), None)

            vton_req = VirtualTryOnRequest(
                person_image_url=person_image_url,
                top_garment_url=top_garment_url,
                bottom_garment_url=bottom_garment_url,
                dress_garment_url=dress_garment_url
            )
            
            vton_model = get_vton_model()
            vton_res = await vton_model.generate(vton_req)
            
            if not vton_res.success:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"AI image generation failed: {vton_res.error_message}",
                )

            return {
                "mode": "ai",
                "ai_image_url": self._to_absolute_url(vton_res.ai_image_url),
                "items": items_payload,
            }

        return {
            "mode": "overlay",
            "items": items_payload,
        }

    # ── Private helpers ────────────────────────────────────────────────────────

    def _to_absolute_url(self, url) -> str:
        """image_generation_service fetches garment images itself over HTTP, so
        it needs a real, absolute URL -- not the relative '/ml/outputs/...'
        paths items carry. Same for the ai_image_url we hand back to the
        frontend if we save inferences locally vs supabase.
        """
        if not url:
            return url or ""
        # Coerce to plain str — handles supabase-py PublicUrlResponse objects
        url_str = str(url).strip()
        # Ensure we do not prepend the domain wrapper to pure binary memory payloads
        if url_str.startswith("http://") or url_str.startswith("https://") or url_str.startswith("data:"):
            return url_str
        base = os.getenv("BACKEND_BASE_URL", "http://localhost:8000").rstrip("/")
        return f"{base}{url_str if url_str.startswith('/') else '/' + url_str}"

    async def _to_base64(self, photo_ref: str) -> str:
        """Convert whatever the frontend sent for the body photo into raw
        base64 (no 'data:image/...' prefix), which is what
        image_generation_service.generate_image()'s person_image_b64 expects.

        Handles:
          - data: URIs (e.g. from a <canvas>/FileReader upload) -> decode inline
          - http(s) URLs (e.g. a photo already saved server-side) -> fetch + encode
          - blob: URLs -> these are browser-local object URLs and are NOT
            reachable from the server at all. If you're seeing this error,
            the frontend needs to either upload the photo to the backend
            first (getting back a real URL) or send it as a data: URI
            instead of a blob: URL.
        """
        if photo_ref.startswith("data:"):
            try:
                return photo_ref.split(",", 1)[1]
            except IndexError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Malformed data URI for the body photo.",
                )

        if photo_ref.startswith("blob:"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "The body photo is a browser-local blob: URL, which the "
                    "server can't fetch. Upload the photo to the backend first "
                    "(or send it as a data: URI) instead of a blob: URL."
                ),
            )

        url = self._to_absolute_url(photo_ref)
        try:
            import httpx

            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url)
            res.raise_for_status()
        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Could not fetch body photo from '{url}': {err}",
            )

        import base64 as _base64

        return _base64.b64encode(res.content).decode("utf-8")

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
            garment = doc.get("garment") or {}
            category_raw = doc.get("category") or garment.get("category") or ""
            category = str(category_raw).lower()
            slot = LAYOUT_CATEGORY_MAP.get(category)

            if slot is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"Category '{category_raw}' (item {doc['_id']}) cannot be "
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
        source = doc.get("source") or {}
        image_url = doc.get("image_url") or source.get("image_url")
        
        if image_url:
            # Always coerce to plain str — stored value might be a
            # supabase-py PublicUrlResponse object if saved before this fix.
            image_url = str(image_url).strip()
            
        if not image_url:
            segmentation = doc.get("segmentation") or {}
            seg_path: str = doc.get("segmentation_path") or segmentation.get("cutout_url") or doc.get("source_image", "")
            # Normalise filesystem path → browser-accessible URL.
            normalised = str(seg_path).replace("\\", "/")
            for marker in ("uploads/", "ml/outputs/", "ml/"):
                idx = normalised.lower().find(marker)
                if idx != -1:
                    image_url = "/" + normalised[idx:]
                    break
            else:
                image_url = normalised if normalised.startswith("/") else "/" + normalised

        garment = doc.get("garment") or {}
        type_raw = doc.get("type") or garment.get("type") or "unknown"
        color_raw = doc.get("color") or garment.get("color") or ""
        
        return {
            "id": str(doc["_id"]),
            "category": slot,
            "type": str(type_raw),
            "color": str(color_raw),
            "image_url": image_url,
            "position": LAYOUT_POSITIONS[slot],
            "z_index": Z_INDEX[slot],
        }