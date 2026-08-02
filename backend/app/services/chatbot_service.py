"""LLM-backed wardrobe assistant service for the MVP.

Returns a human-readable reply plus structured recommended_items so the
frontend can render per-item visualize buttons without exposing raw IDs.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

_OBJECT_ID_RE = re.compile(r"\b[0-9a-f]{24}\b", re.IGNORECASE)
_ID_TAG_RE = re.compile(r"\(id=[0-9a-f]{24}\)", re.IGNORECASE)

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


def strip_ids_from_text(text: str) -> str:
    """Remove MongoDB ids and id= tags from user-facing copy."""
    cleaned = _ID_TAG_RE.sub("", text)
    cleaned = _OBJECT_ID_RE.sub("", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([,.])", r"\1", cleaned)
    cleaned = re.sub(r",\s*,", ",", cleaned)
    return cleaned.strip(" ,.")


def extract_ids_from_text(text: str) -> list[str]:
    return list(dict.fromkeys(_OBJECT_ID_RE.findall(text)))


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


def pick_outfit(items: list[WardrobeItem], message: str) -> list[WardrobeItem]:
    """Pick one item per slot for a complete outfit suggestion."""
    if not items:
        return []

    msg = message.lower()
    by_slot: dict[str, list[WardrobeItem]] = {}
    for item in items:
        slot = item_slot(item)
        if slot:
            by_slot.setdefault(slot, []).append(item)

    def first_in(slot: str) -> WardrobeItem | None:
        pool = by_slot.get(slot, [])
        if not pool:
            return None
        if slot == "bottom" and ("jean" in msg or "denim" in msg):
            return next((i for i in pool if "jean" in i.type.lower() or "denim" in " ".join(i.tags).lower()), pool[0])
        if slot == "top" and "formal" in msg:
            return next((i for i in pool if i.category in ("shirt", "suit")), pool[0])
        return pool[0]

    picks: list[WardrobeItem] = []

    if "formal" in msg or "business" in msg or "jacket" in msg or "blazer" in msg:
        outer = first_in("outerwear")
        if outer:
            picks.append(outer)

    for slot in ("top", "bottom", "shoes"):
        item = first_in(slot)
        if item:
            picks.append(item)

    return dedupe_by_slot(picks) if picks else items[: min(3, len(items))]


def build_outfit_reply(message: str, picks: list[WardrobeItem]) -> str:
    if not picks:
        return "Your wardrobe is empty right now. Upload a top, bottom, and shoes to get outfit ideas."

    msg = message.lower()
    labels = [item_label(p) for p in picks]

    if "what items" in msg or "what do i own" in msg:
        return "You currently own: " + ", ".join(labels) + "."

    if len(labels) == 1:
        return f"I'd suggest your {labels[0]}. Tap Visualize below to preview it on the body template."

    parts = ", ".join(labels[:-1]) + f", and {labels[-1]}"
    return (
        f"Here's a complete look from your wardrobe: {parts}. "
        "Visualize each piece individually, or preview the full outfit together."
    )


def resolve_recommended(items: list[WardrobeItem], llm_text: str, message: str) -> list[WardrobeItem]:
    """Prefer LLM-mentioned ids when valid; otherwise pick a balanced outfit."""
    extracted = extract_ids_from_text(llm_text)
    if extracted:
        id_set = set(extracted)
        matched = [i for i in items if i.id in id_set]
        deduped = dedupe_by_slot(matched)
        if deduped:
            return deduped
    return pick_outfit(items, message)


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
    return f"""You are a concise, friendly wardrobe assistant for an MVP demo.
Use ONLY wardrobe items from the list below. Never invent items.

When suggesting an outfit, recommend a COMPLETE look when possible:
one top, one bottom, and shoes (add outerwear for formal/cold weather).

Write naturally for the user. Mention items by color and type only.
Do NOT include MongoDB ids, hex strings, or "(id=...)" in your answer.
Keep the response under 100 words.

Output ONLY the final recommendation — no reasoning or analysis.

Wardrobe:
{wardrobe_context}"""


def build_chat_reply(message: str, items: list[WardrobeItem], llm_text: str | None = None) -> ChatReply:
    """Build structured reply with clean text and per-item recommendations."""
    if not items:
        return ChatReply(
            reply="Your wardrobe is empty. Upload some clothing photos first!",
            recommended_items=[],
        )

    if llm_text:
        clean = strip_ids_from_text(llm_text)
        picks = resolve_recommended(items, llm_text, message)
        if not clean:
            clean = build_outfit_reply(message, picks)
        return ChatReply(reply=clean, recommended_items=[to_recommended(p) for p in picks])

    picks = pick_outfit(items, message)
    return ChatReply(
        reply=build_outfit_reply(message, picks),
        recommended_items=[to_recommended(p) for p in picks],
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
    async for doc in wardrobe_collection.find({}):
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

        # Local-only path when LLM is not configured
        if not self.model or not self.api_key or self.provider != "openrouter":
            return build_chat_reply(message, items)

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": _system_prompt(build_wardrobe_context(items))},
                {"role": "user", "content": message.strip()},
            ],
            "temperature": 0.4,
            "max_tokens": 180,
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
            raw_content = choice.get("message", {}).get("content") or ""
            content = raw_content.strip()
        except Exception as error:
            print(f"[ChatbotService] OpenRouter unavailable ({error}). Using local outfit picker.")
            return build_chat_reply(message, items)

        if "<think>" in content and "</think>" in content:
            content = content.split("</think>")[-1].strip()

        if not content or content.lower().startswith("user safety:"):
            return build_chat_reply(message, items)

        return build_chat_reply(message, items, llm_text=content)


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
