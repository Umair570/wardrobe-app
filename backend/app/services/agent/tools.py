"""
Tool definitions for the stylist agent.

Schemas are the OpenAI/OpenRouter function-calling format. Each tool has a
matching coroutine in `TOOL_IMPLEMENTATIONS`, dispatched through
`execute_tool()` with a per-request `ToolContext` that carries the caller's
identity. The model never sees or supplies `user_id` — it is bound server-side
so a prompt-injected `user_id` cannot reach across accounts.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Slots the visualization layer can render. Kept in sync with
# services/visualization_service.py's LAYOUT_CATEGORY_MAP.
OUTFIT_SLOTS = ("top_id", "bottom_id", "outerwear_id", "shoes_id")


@dataclass
class ToolContext:
    """Per-request state bound server-side, never model-supplied."""
    user_id: str
    browser_lat: Optional[float] = None
    browser_lon: Optional[float] = None

    # Populated as the agent searches, so the final answer can be validated
    # against items that were actually retrieved rather than invented.
    seen_items: dict[str, dict] = field(default_factory=dict)
    weather_report: Any = None

    def remember(self, items: list[dict]) -> None:
        for item in items:
            if item.get("id"):
                self.seen_items[str(item["id"])] = item


# ══════════════════════════════════════════════════════════════════════════════
# Tool schemas
# ══════════════════════════════════════════════════════════════════════════════

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_wardrobe",
            "description": (
                "Semantic search over the user's own wardrobe. The query is encoded with "
                "FashionCLIP and matched against the stored garment image embeddings in "
                "Qdrant, so describe garments VISUALLY rather than abstractly: prefer "
                "'lightweight beige linen short-sleeve shirt' over 'something for brunch'. "
                "Call this several times with different garment descriptions to assemble a "
                "complete outfit (once for tops, once for bottoms, once for shoes, ...)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Visual description of the garment being looked for.",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "How many items to return (1-20). Default 8.",
                    },
                    "category": {
                        "type": "string",
                        "description": (
                            "Optional hard filter on the broad garment category. One of: "
                            "shirt, sweater, pants, shorts, skirt, dress, jacket, suit, shoes, "
                            "bag, accessory, traditional, one-piece, swimwear, sleepwear, underwear."
                        ),
                    },
                    "season": {
                        "type": "string",
                        "description": "Optional hard filter: summer, winter, spring/fall, all-season.",
                    },
                    "color": {
                        "type": "string",
                        "description": "Optional hard filter on the stored colour name, e.g. 'navy'.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_wardrobe",
            "description": (
                "List everything in the user's wardrobe, optionally filtered to one category. "
                "Use this when the user asks what they own, or when semantic search keeps "
                "coming back empty and you need to see the full inventory."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Optional broad category filter. Omit to list everything.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max items to return (1-100). Default 50.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": (
                "Fetch live weather and the derived dressing constraints for a location. "
                "Call this whenever the request depends on conditions — 'what should I wear "
                "today', 'is it cold out', any mention of a place, or any outdoor plan. "
                "Returns hard `require` and `avoid` lists that you MUST respect. "
                "IMPORTANT: if the user names ANY place ('in Lahore', 'trip to London'), you "
                "MUST pass it as `city`. Only omit `city` when no place is mentioned at all, "
                "which falls back to auto-detecting the user's location."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": (
                            "The place the user named, e.g. 'Lahore'. Required whenever the "
                            "user mentions a location. Omit ONLY if none was mentioned."
                        ),
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "present_outfits",
            "description": (
                "Deliver the final answer. Call this exactly once, as your last action, after "
                "you have searched the wardrobe. Propose THREE distinct outfit options built "
                "only from item IDs returned by search_wardrobe or list_wardrobe, so the user "
                "can pick one to visualise. If the wardrobe genuinely cannot support three, "
                "return fewer and explain why in `message`."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": (
                            "Friendly reply to the user introducing the options and explaining "
                            "how the weather or occasion shaped them."
                        ),
                    },
                    "outfits": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 3,
                        "description": "Up to three distinct outfit options, best first.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "Short label, e.g. 'Smart casual, rain-ready'.",
                                },
                                "rationale": {
                                    "type": "string",
                                    "description": (
                                        "One or two sentences on why this works, referencing the "
                                        "weather constraints when they applied."
                                    ),
                                },
                                "top_id": {"type": ["string", "null"], "description": "Exact item ID, or null."},
                                "bottom_id": {"type": ["string", "null"], "description": "Exact item ID, or null."},
                                "outerwear_id": {"type": ["string", "null"], "description": "Exact item ID, or null."},
                                "shoes_id": {"type": ["string", "null"], "description": "Exact item ID, or null."},
                            },
                            "required": ["title", "rationale"],
                        },
                    },
                },
                "required": ["message", "outfits"],
            },
        },
    },
]

TERMINAL_TOOL = "present_outfits"


# ══════════════════════════════════════════════════════════════════════════════
# Implementations
# ══════════════════════════════════════════════════════════════════════════════

def _item_to_dict(item) -> dict[str, Any]:
    """Compact projection handed to the model — small payload, no vectors."""
    return {
        "id": item.id,
        "category": item.category,
        "type": item.type,
        "color": item.color,
        "style": item.style,
        "season": item.season,
        "pattern": item.pattern,
    }


async def _search_wardrobe(ctx: ToolContext, args: dict) -> dict:
    from app.services.embedding.model_registry import embedding_service
    from app.services.vector.qdrant_service import qdrant_service
    from app.services.retrieval.retrieval import (
        _qdrant_results_to_wardrobe_items,
        fetch_wardrobe_items,
    )

    query = (args.get("query") or "").strip()
    if not query:
        return {"error": "query is required", "items": []}

    top_k = max(1, min(int(args.get("top_k") or 8), 20))

    query_vector = None
    if embedding_service.is_available():
        try:
            query_vector = embedding_service.embed_text(query)
        except Exception as e:
            logger.warning("[agent] FashionCLIP text embedding failed: %s", e)
    else:
        logger.warning("[agent] Embedding model unavailable — falling back to filter-only search.")

    results = []
    if qdrant_service.available:
        results = await qdrant_service.search_items(
            user_id=ctx.user_id,
            query_vector=query_vector,
            category_filter=args.get("category"),
            season_filter=args.get("season"),
            color_filter=args.get("color"),
            limit=top_k,
        )

    if results:
        items = [_item_to_dict(i) for i in _qdrant_results_to_wardrobe_items(results)]
        for item, raw in zip(items, results):
            if "score" in raw:
                item["match_score"] = raw["score"]
        source = "qdrant"
    else:
        # Qdrant empty or unavailable — show the model the real wardrobe rather
        # than letting it conclude the user owns nothing.
        items = [_item_to_dict(i) for i in await fetch_wardrobe_items(ctx.user_id)][:top_k]
        source = "mongodb_fallback"

    ctx.remember(items)
    logger.info("[agent] search_wardrobe(%r) → %d item(s) via %s", query[:60], len(items), source)
    return {"source": source, "count": len(items), "items": items}


async def _list_wardrobe(ctx: ToolContext, args: dict) -> dict:
    from app.services.retrieval.retrieval import fetch_wardrobe_items

    limit = max(1, min(int(args.get("limit") or 50), 100))
    category = (args.get("category") or "").strip().lower()

    all_items = [_item_to_dict(i) for i in await fetch_wardrobe_items(ctx.user_id)]
    if category:
        all_items = [i for i in all_items if (i.get("category") or "").lower() == category]

    items = all_items[:limit]
    ctx.remember(items)
    logger.info("[agent] list_wardrobe(category=%r) → %d item(s)", category or None, len(items))
    return {"count": len(items), "total_owned": len(all_items), "items": items}


async def _get_weather(ctx: ToolContext, args: dict) -> dict:
    from app.services.weather.weather_service import get_weather_report

    city = (args.get("city") or "").strip() or None
    report = await get_weather_report(
        city=city,
        browser_lat=ctx.browser_lat,
        browser_lon=ctx.browser_lon,
    )

    if report is None:
        return {
            "available": False,
            "reason": (
                "Could not determine the location or reach the weather service. "
                "Ask the user which city they are in, or proceed without weather constraints."
            ),
        }

    ctx.weather_report = report
    payload = report.to_dict()
    payload["available"] = True
    return payload


async def _present_outfits(ctx: ToolContext, args: dict) -> dict:
    """Terminal tool — validated by the agent loop, never executed for effect."""
    return {"ok": True}


TOOL_IMPLEMENTATIONS = {
    "search_wardrobe": _search_wardrobe,
    "list_wardrobe": _list_wardrobe,
    "get_weather": _get_weather,
    "present_outfits": _present_outfits,
}


async def execute_tool(ctx: ToolContext, name: str, raw_arguments: str) -> str:
    """
    Run one tool call and return its result as a JSON string for the tool message.

    Never raises: a failed tool has to come back to the model as a readable error
    so it can adapt, otherwise one bad call kills the whole conversation.
    """
    impl = TOOL_IMPLEMENTATIONS.get(name)
    if impl is None:
        return json.dumps({"error": f"Unknown tool '{name}'."})

    try:
        args = json.loads(raw_arguments) if raw_arguments else {}
        if not isinstance(args, dict):
            raise ValueError("arguments must be a JSON object")
    except (json.JSONDecodeError, ValueError) as e:
        return json.dumps({"error": f"Could not parse arguments for '{name}': {e}"})

    try:
        return json.dumps(await impl(ctx, args), default=str)
    except Exception as e:
        logger.error("[agent] Tool '%s' failed: %s", name, e, exc_info=True)
        return json.dumps({"error": f"Tool '{name}' failed: {e}"})
