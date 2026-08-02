"""LLM-backed wardrobe assistant service for the MVP.

The chatbot ALWAYS calls OpenRouter when it's configured. The LLM decides
which wardrobe items to recommend and returns them as explicit ids inside a
structured JSON payload -- so `recommended_items` reflects what the model
actually chose, not a local keyword guess layered on top of it.

The keyword-based picker in this file is a genuine fallback: it only runs
when the LLM is unconfigured, the HTTP call fails outright, or the model's
response can't be parsed. Every ChatReply carries a `source` field
("llm" | "fallback") so the frontend/demo can always tell which one produced
a given answer -- no more silently swapping in the local picker's guess.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Literal

import httpx
from dotenv import load_dotenv

load_dotenv()

_OBJECT_ID_RE = re.compile(r"\b[0-9a-f]{24}\b", re.IGNORECASE)
_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)

CATEGORY_TO_SLOT: dict[str, str] = {
    "shirt": "top",
    "sweater": "top",
    "suit": "top",
    "dress": "bottom",
    "pants": "bottom",
    "shorts": "bottom",
    "skirt": "bottom",
    "shoes": "shoes",
    "jacket": "outerwear",
    "top": "top",
    "bottom": "bottom",
    "outerwear": "outerwear",
}

SLOT_LABELS = {
    "top": "Top",
    "bottom": "Bottom",
    "shoes": "Shoes",
    "outerwear": "Outerwear",
}


class ChatbotConfigurationError(RuntimeError):
    """Raised when a required local chatbot setting is missing."""


class ChatbotProviderError(RuntimeError):
    """Raised when the LLM provider rejects or fails a request."""


@dataclass(frozen=True)
class WardrobeItem:
    id: str
    category: str
    type: str
    color: str
    tags: list[str]


@dataclass(frozen=True)
class RecommendedItem:
    id: str
    label: str
    category: str
    slot: str
    color: str
    type: str


@dataclass(frozen=True)
class ChatReply:
    reply: str
    recommended_items: list[RecommendedItem]
    # "llm"       -> reply text AND item picks both came straight from OpenRouter
    # "fallback"  -> local keyword picker was used (no key/model configured,
    #                the HTTP call failed, or the model's output didn't parse)
    source: Literal["llm", "fallback"] = "fallback"


MOCK_WARDROBE = [
    WardrobeItem("mock-blue-jeans", "pants", "jeans", "blue", ["casual", "denim"]),
    WardrobeItem("mock-black-shirt", "shirt", "t-shirt", "black", ["casual", "solid"]),
    WardrobeItem("mock-white-sneakers", "shoes", "sneakers", "white", ["casual"]),
]


def item_slot(item: WardrobeItem) -> str | None:
    return CATEGORY_TO_SLOT.get(item.category.lower())


def item_label(item: WardrobeItem) -> str:
    color = item.color.strip()
    typ = item.type.strip()
    if color and color.lower() not in ("unknown", "none"):
        return f"{color.title()} {typ}"
    return typ.replace("_", " ").title()


def to_recommended(item: WardrobeItem) -> RecommendedItem:
    slot = item_slot(item) or "other"
    return RecommendedItem(
        id=item.id,
        label=item_label(item),
        category=item.category,
        slot=slot,
        color=item.color,
        type=item.type,
    )


def dedupe_by_slot(items: list[WardrobeItem]) -> list[WardrobeItem]:
    seen: set[str] = set()
    result: list[WardrobeItem] = []
    for item in items:
        slot = item_slot(item)
        if not slot or slot in seen:
            continue
        seen.add(slot)
        result.append(item)
    return result


# ---------------------------------------------------------------------------
# Local fallback picker -- ONLY used when there is no real LLM answer to show.
# ---------------------------------------------------------------------------

def pick_outfit(items: list[WardrobeItem], message: str) -> list[WardrobeItem]:
    """Pick an outfit combination via keyword scoring. Fallback path only."""
    if not items:
        return []

    msg = message.lower()
    by_slot: dict[str, list[WardrobeItem]] = {}
    for item in items:
        slot = item_slot(item)
        if slot:
            by_slot.setdefault(slot, []).append(item)

    def score_item(item: WardrobeItem) -> int:
        score = 0
        text = f"{item.category} {item.type} {item.color} {' '.join(item.tags)}".lower()
        words = re.findall(r"\w+", msg)
        for w in words:
            if len(w) > 2 and w in text:
                score += 3
        if "formal" in msg and any(t in text for t in ("formal", "suit", "shirt", "jacket")):
            score += 5
        if "casual" in msg and any(t in text for t in ("casual", "t-shirt", "shorts", "sneakers")):
            score += 5
        if "blue" in msg and "blue" in text:
            score += 5
        if "white" in msg and "white" in text:
            score += 5
        if ("crimson" in msg or "red" in msg) and ("crimson" in text or "red" in text):
            score += 5
        return score

    picks: list[WardrobeItem] = []
    slots_to_fill = ["top", "bottom", "shoes"]
    if any(k in msg for k in ("formal", "jacket", "blazer", "outerwear", "layer", "cold", "winter")):
        slots_to_fill.insert(0, "outerwear")

    msg_hash = sum(ord(c) for c in msg)

    for slot in slots_to_fill:
        pool = by_slot.get(slot, [])
        if not pool:
            continue
        scored_pool = sorted(pool, key=lambda i: (score_item(i), (hash(i.id) + msg_hash) % 100), reverse=True)
        picks.append(scored_pool[0])

    return dedupe_by_slot(picks) if picks else items[: min(3, len(items))]


def build_outfit_reply(message: str, picks: list[WardrobeItem]) -> str:
    if not picks:
        return "Your wardrobe is empty right now. Upload a top, bottom, and shoes to get outfit ideas."

    msg = message.lower()
    labels = [item_label(p) for p in picks]

    if "what items" in msg or "what do i own" in msg:
        return "You currently own: " + ", ".join(labels) + "."

    parts = ", ".join(labels[:-1]) + f", and {labels[-1]}" if len(labels) > 1 else labels[0]

    if "formal" in msg or "jacket" in msg:
        return f"For a smart, structured look, I styled your {parts}. Tap Visualize to see how the pieces layer together!"
    if "blue" in msg or "jean" in msg or "denim" in msg:
        return f"Great choice! Here is a stylish match for your denim/blue pieces: {parts}."
    if "casual" in msg or "today" in msg or "wear" in msg:
        return f"Here is a comfortable, stylish casual look from your wardrobe: {parts}."

    return f"Here's a curated outfit tailored to your request ({parts}). Tap Visualize below to test the look!"


def build_fallback_reply(message: str, items: list[WardrobeItem]) -> ChatReply:
    if not items:
        return ChatReply(
            reply="Your wardrobe is empty. Upload some clothing photos first!",
            recommended_items=[],
            source="fallback",
        )
    picks = pick_outfit(items, message)
    return ChatReply(
        reply=build_outfit_reply(message, picks),
        recommended_items=[to_recommended(p) for p in picks],
        source="fallback",
    )


# ---------------------------------------------------------------------------
# LLM path
# ---------------------------------------------------------------------------

def build_wardrobe_context(items: list[WardrobeItem]) -> str:
    if not items:
        return "The user has no saved wardrobe items. Ask them to upload clothing first."

    lines = []
    for item in items:
        tags = ", ".join(item.tags) if item.tags else "none"
        lines.append(
            f"- id={item.id}; category={item.category}; type={item.type}; "
            f"color={item.color}; tags={tags}"
        )
    return "\n".join(lines)


def _system_prompt(wardrobe_context: str) -> str:
    return f"""You are a wardrobe stylist assistant for an MVP demo.

You may ONLY recommend items from the wardrobe list below -- never invent items.

Respond with STRICT JSON and nothing else (no markdown fences, no commentary
before or after) in exactly this shape:
{{"reply": "<friendly outfit suggestion under 80 words, mention items by color/type only, never mention raw ids>", "item_ids": ["<the id field for each item you recommend, copied exactly from the wardrobe list>"]}}

Prefer a complete look: one top, one bottom, one pair of shoes, and add
outerwear if the request mentions cold weather, formality, or layering.
If nothing in the wardrobe fits the request, say so honestly in "reply" and
return an empty item_ids list.

Wardrobe:
{wardrobe_context}"""


def _extract_json(raw: str) -> dict[str, Any] | None:
    """Pull the JSON object out of the model's raw text, tolerating stray
    markdown fences or a little wrapper text some models add anyway."""
    text = _JSON_FENCE_RE.sub("", raw).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def resolve_llm_reply(items: list[WardrobeItem], parsed: dict[str, Any]) -> ChatReply | None:
    """Turn a parsed {"reply", "item_ids"} payload into a ChatReply using the
    model's actual picks. Returns None if the payload is unusable."""
    reply_text = str(parsed.get("reply", "")).strip()
    raw_ids = parsed.get("item_ids", [])
    if not reply_text or not isinstance(raw_ids, list):
        return None

    # Safety net only -- the prompt already tells the model not to include ids.
    reply_text = _OBJECT_ID_RE.sub("", reply_text)
    reply_text = re.sub(r"\s{2,}", " ", reply_text).strip(" ,.")

    by_id = {i.id: i for i in items}
    matched = [by_id[i] for i in raw_ids if isinstance(i, str) and i in by_id]
    picks = dedupe_by_slot(matched)

    return ChatReply(
        reply=reply_text or "Here's what I'd suggest from your wardrobe.",
        recommended_items=[to_recommended(p) for p in picks],
        source="llm",
    )


async def fetch_wardrobe_items(user_id: str) -> list[WardrobeItem]:
    try:
        from app.database.mongodb import wardrobe_collection  # type: ignore[import]
    except ImportError:
        try:
            from backend.app.database.mongodb import wardrobe_collection  # type: ignore[import]
        except ImportError:
            return []

    items: list[WardrobeItem] = []
    # Filter by user_id -- the schema stores it (see PRD FR-4). Fetching
    # `.find({})` would return every user's wardrobe once you have more than
    # one account.
    async for doc in wardrobe_collection.find({"user_id": user_id}):
        items.append(
            WardrobeItem(
                id=str(doc["_id"]),
                category=str(doc.get("category", "unknown")),
                type=str(doc.get("type", "unknown")),
                color=str(doc.get("color", "unknown")),
                tags=[str(t) for t in doc.get("tags", [])],
            )
        )
    return items


class ChatbotService:
    def __init__(self) -> None:
        self.provider = os.getenv("LLM_PROVIDER", "openrouter").lower()
        self.model = os.getenv("LLM_MODEL", "").strip()
        self.api_key = os.getenv("OPENROUTER_API_KEY", "").strip()

    async def reply(
        self, message: str, items: list[WardrobeItem], user_id: str = "default_user"
    ) -> ChatReply:
        if not message.strip():
            raise ValueError("Message cannot be empty.")

        if not items:
            items = await fetch_wardrobe_items(user_id)
        if not items:
            items = list(MOCK_WARDROBE)

        if not self.model or not self.api_key or self.provider != "openrouter":
            print(
                "[ChatbotService] LLM_MODEL / OPENROUTER_API_KEY not set -- "
                "using local fallback picker."
            )
            return build_fallback_reply(message, items)

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": _system_prompt(build_wardrobe_context(items))},
                {"role": "user", "content": message.strip()},
            ],
            "temperature": 0.4,
            "max_tokens": 350,
            # NOTE: not every OpenRouter model honours response_format, and a
            # model that rejects it would make every request fail closed into
            # the fallback -- defeating the point. We rely on the prompt +
            # _extract_json()'s brace-matching instead, which works across
            # providers.
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "AI Wardrobe Assistant",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
            response.raise_for_status()
            choice = response.json().get("choices", [{}])[0]
            content = (choice.get("message", {}).get("content") or "").strip()
        except Exception as error:
            print(f"[ChatbotService] OpenRouter request failed ({error}). Using local fallback picker.")
            return build_fallback_reply(message, items)

        if "<think>" in content and "</think>" in content:
            content = content.split("</think>")[-1].strip()

        parsed = _extract_json(content)
        if parsed is None:
            print(f"[ChatbotService] Could not parse LLM JSON, falling back. Raw (truncated): {content[:200]!r}")
            return build_fallback_reply(message, items)

        llm_reply = resolve_llm_reply(items, parsed)
        if llm_reply is None:
            print(f"[ChatbotService] LLM JSON missing required fields, falling back. Parsed: {parsed}")
            return build_fallback_reply(message, items)

        return llm_reply


def parse_wardrobe_items(raw_items: list[dict[str, Any]] | None) -> list[WardrobeItem]:
    if raw_items is None:
        return []

    return [
        WardrobeItem(
            id=str(item.get("id", item.get("_id", "unknown"))),
            category=str(item.get("category", "unknown")),
            type=str(item.get("type", "unknown")),
            color=str(item.get("color", "unknown")),
            tags=[str(tag) for tag in item.get("tags", [])],
        )
        for item in raw_items
    ]