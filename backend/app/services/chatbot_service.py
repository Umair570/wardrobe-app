"""LLM-backed wardrobe assistant service for the MVP.

The service accepts wardrobe metadata, never image bytes, and returns a concise
outfit suggestion. It supports OpenRouter now and can be extended with other
providers without changing the API route.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()


class ChatbotConfigurationError(RuntimeError):
    """Raised when a required local chatbot setting is missing."""


class ChatbotProviderError(RuntimeError):
    """Raised when the LLM provider rejects or fails a request."""


@dataclass(frozen=True)
class WardrobeItem:
    """The minimum item data the chatbot needs from Mahad's API."""

    id: str
    category: str
    type: str
    color: str
    tags: list[str]


MOCK_WARDROBE = [
    WardrobeItem("mock-blue-jeans", "pants", "jeans", "blue", ["casual", "denim"]),
    WardrobeItem("mock-black-shirt", "shirt", "t-shirt", "black", ["casual", "solid"]),
    WardrobeItem("mock-white-sneakers", "shoes", "sneakers", "white", ["casual"]),
]


def build_wardrobe_context(items: list[WardrobeItem]) -> str:
    """Convert structured item metadata into safe, compact LLM context."""
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
    return f"""You are a concise, friendly wardrobe assistant for an MVP.
Use only the wardrobe items listed below. Do not claim the user owns items not
in the list. If there is no suitable item, say that clearly and suggest an
upload. Keep the response under 120 words. Mention selected item IDs when
recommending an item so the UI can link to it.

Wardrobe:
{wardrobe_context}"""


def _fallback_reply(message: str, items: list[WardrobeItem]) -> str:
    """Return a useful local answer when the provider response is unusable."""
    if not items:
        return "Your wardrobe is empty right now. Please upload some clothing items first."

    normalized_message = message.lower()
    if "what items" in normalized_message or "what do i own" in normalized_message:
        item_list = ", ".join(
            f"{item.color} {item.type} (id={item.id})" for item in items
        )
        return f"You currently own: {item_list}."

    jeans = next((item for item in items if item.type == "jeans"), None)
    black_shirt = next(
        (item for item in items if item.category == "shirt" and item.color == "black"),
        None,
    )
    if "jeans" in normalized_message and "black shirt" in normalized_message and jeans and black_shirt:
        return (
            f"Yes. {jeans.color.title()} {jeans.type} (id={jeans.id}) pair well with a "
            f"{black_shirt.color} {black_shirt.type} (id={black_shirt.id}) for a casual outfit."
        )

    recommended = items[:3]
    suggestion = ", ".join(
        f"{item.color} {item.type} (id={item.id})" for item in recommended
    )
    return f"A simple outfit from your wardrobe is: {suggestion}."


class ChatbotService:
    """Provider adapter used by the FastAPI route."""

    def __init__(self) -> None:
        self.provider = os.getenv("LLM_PROVIDER", "openrouter").lower()
        self.model = os.getenv("LLM_MODEL", "").strip()
        self.api_key = os.getenv("OPENROUTER_API_KEY", "").strip()

    async def reply(self, message: str, items: list[WardrobeItem]) -> str:
        if not message.strip():
            raise ValueError("Message cannot be empty.")
        if not self.model:
            raise ChatbotConfigurationError("LLM_MODEL is not set in .env.")
        if self.provider != "openrouter":
            raise ChatbotConfigurationError(
                "This MVP endpoint currently supports LLM_PROVIDER=openrouter."
            )
        if not self.api_key:
            raise ChatbotConfigurationError("OPENROUTER_API_KEY is not set in .env.")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": _system_prompt(build_wardrobe_context(items))},
                {"role": "user", "content": message.strip()},
            ],
            "temperature": 0.4,
            "max_tokens": 180,
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"].strip()
        except (httpx.HTTPError, KeyError, IndexError, TypeError) as error:
            raise ChatbotProviderError("The chatbot provider could not generate a response.") from error

        if not content or content.lower().startswith("user safety:"):
            return _fallback_reply(message, items)
        return content


def parse_wardrobe_items(raw_items: list[dict[str, Any]] | None) -> list[WardrobeItem]:
    """Accept the future wardrobe API payload, falling back to MVP mock data."""
    if raw_items is None:
        return MOCK_WARDROBE

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
