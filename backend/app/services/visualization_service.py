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
    """Builds 2D overlay or Gemini AI image try-on response from selected item IDs."""

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
        once that function accepts image inputs; see the TODO below.
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

            try:
                from app.services.image_generation_service import generate_image  # type: ignore[import]
            except ImportError:
                from backend.app.services.image_generation_service import generate_image  # type: ignore[import]

            person_image_b64 = await self._to_base64(user_body_photo_url)
            garment_image_urls = [
                self._to_absolute_url(item["image_url"]) for item in items_payload
            ]
            descriptions = [
                f"{doc.get('color', '')} {doc.get('type', doc.get('category', 'clothing'))}".strip()
                for doc in docs
            ]
            prompt = ", ".join(descriptions)

            try:
                from starlette.concurrency import run_in_threadpool
                ai_image_url = await run_in_threadpool(
                    generate_image,
                    prompt,
                    "idm-vton",
                    person_image_b64=person_image_b64,
                    garment_image_urls=garment_image_urls,
                )
            except Exception as err:
                # Do NOT silently fall back to overlay mode here — that hides real
                # failures (bad API key, timeout, quota) behind a response that looks
                # like a normal, successful overlay. Surface the error instead.
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"AI image generation failed: {err}",
                )

            return {
                "mode": "ai",
                "ai_image_url": self._to_absolute_url(ai_image_url),
                "items": items_payload,
            }

        return {
            "mode": "overlay",
            "items": items_payload,
        }

    # ── Private helpers ────────────────────────────────────────────────────────

    def _to_absolute_url(self, url: str) -> str:
        """image_generation_service fetches garment images itself over HTTP, so
        it needs a real, absolute URL -- not the relative '/ml/outputs/...'
        paths items carry. Same for the ai_image_url we hand back to the
        frontend. Set BACKEND_BASE_URL in the environment if this isn't
        running on localhost:8000."""
        if not url:
            return url
        if url.startswith("http://") or url.startswith("https://"):
            return url
        base = os.getenv("BACKEND_BASE_URL", "http://localhost:8000").rstrip("/")
        return f"{base}{url if url.startswith('/') else '/' + url}"

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