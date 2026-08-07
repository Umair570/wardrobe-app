"""
Tool-calling stylist agent.

Replaces the old single-shot "stuff the whole wardrobe into one prompt" call
with a real agent loop:

    user query
        │
        ▼
    LLM  ──calls──►  get_weather        (live conditions + hard dress constraints)
        │            search_wardrobe    (FashionCLIP text embed → Qdrant vector search)
        │            list_wardrobe      (full inventory)
        │◄─results───┘
        │            …iterates, refining searches per outfit slot…
        ▼
    present_outfits  →  three distinct, validated outfit options

Retrieval is therefore driven by the model's own reasoning about what it needs,
which is what makes this RAG rather than a fixed context dump. Every item ID in
the final answer is checked against what the tools actually returned, so a
hallucinated ID is dropped instead of reaching the visualiser.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Optional

import httpx

from app.core.config import settings
from app.services.agent.tools import (
    TERMINAL_TOOL,
    TOOL_SCHEMAS,
    ToolContext,
    execute_tool,
)
from app.services.stylist.schemas import OutfitOption, StylistResponse

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 8
REQUEST_TIMEOUT = 60.0
MAX_RESPONSE_TOKENS = 1500


SYSTEM_PROMPT = """\
You are an expert personal stylist with live access to the user's real wardrobe.

TOOLS AND ORDER OF WORK
1. If the request depends on conditions in any way — "what should I wear today",
   any mention of a city, any outdoor plan, anything seasonal — call `get_weather`
   FIRST, before searching. Omit the `city` argument to use the user's own location.
2. Call `search_wardrobe` SEVERAL times, once per outfit slot you need to fill
   (a top search, a bottom search, a shoes search, an outerwear search if the
   weather calls for one). One broad search is not enough to build three outfits.
   Search queries are matched against garment photos with FashionCLIP, so write
   them as VISUAL descriptions — "dark wash slim denim jeans", not "something nice".
3. If searches keep returning nothing useful, call `list_wardrobe` to see
   everything the user actually owns before concluding anything.
4. Finish by calling `present_outfits` exactly once with THREE options.

HARD RULES
- Item IDs must come verbatim from a tool result. Never invent, guess, reformat
  or abbreviate an ID. If you cannot fill a slot, set that field to null.
- Put each item in the slot it belongs to: a shirt in `top_id`, trousers or a
  skirt in `bottom_id`, a jacket or coat in `outerwear_id`, footwear in
  `shoes_id`. Never place a bag or an accessory in an outfit slot.
- The `require` and `avoid` lists from `get_weather` are requirements, not hints.
  Never recommend anything on the `avoid` list. If the wardrobe cannot satisfy a
  `require` entry, say so plainly in your message instead of pretending it can.
- Outerwear is OPTIONAL. Leave `outerwear_id` null unless the weather actually
  calls for a layer AND the wardrobe has one that fits the conditions. Never add
  a warm or heavy layer just to fill the slot — in hot weather a coat is worse
  than no coat, and a heavy jacket is not rain protection.
- The three outfits must be genuinely DIFFERENT. Each one must differ from the
  others in its top OR its bottom — three shoe swaps over an identical outfit is
  not three options. Only repeat a garment when the wardrobe leaves no choice,
  and say so in your message when that happens.
- Recommend only what exists. An empty wardrobe means saying so, not inventing
  clothes the user does not own.
- Every item you name in prose must also appear as an ID in that outfit's fields,
  and the reverse holds too: never describe a garment you did not select. If you
  left a slot null because nothing in the wardrobe suits the conditions, say that
  outright ("you have no warm-weather footwear for this") rather than writing
  about sandals the user does not own.
- When the query or weather is hot/warm (> 22°C / 72°F), you MUST leave outerwear_id set to null unless the user explicitly requested a jacket.
"""


@dataclass
class AgentResult:
    response: StylistResponse
    tool_calls_made: list[str]
    items_seen: int
    weather_used: bool
    iterations: int


# ══════════════════════════════════════════════════════════════════════════════
# LLM transport
# ══════════════════════════════════════════════════════════════════════════════

def _llm_config() -> tuple[Optional[str], str, str, dict[str, str]]:
    """Return (api_key, base_url, model, headers) for the configured provider."""
    provider = (settings.llm_provider or "groq").lower()
    api_key = settings.active_llm_api_key
    base_url = settings.active_llm_base_url
    model = settings.active_llm_model

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if provider == "openrouter":
        # OpenRouter attributes traffic with these; harmless elsewhere.
        headers["HTTP-Referer"] = settings.backend_base_url
        headers["X-Title"] = "Wardrobe Stylist AI"

    return api_key, base_url, model, headers


async def _call_llm(client: httpx.AsyncClient, messages: list[dict], *, use_tools: bool) -> dict:
    """One chat-completions round trip. Returns the assistant message dict."""
    _, base_url, model, headers = _llm_config()

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.3,
        # Bounded on purpose. Tool calls and the final three outfits are small,
        # while an unset cap makes OpenRouter reserve the model's full context
        # up front and reject the request outright on a low credit balance.
        "max_tokens": MAX_RESPONSE_TOKENS,
    }
    if use_tools:
        payload["tools"] = TOOL_SCHEMAS
        payload["tool_choice"] = "auto"

    response = await client.post(base_url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
    if response.status_code >= 400:
        # The status line alone hides why (bad key, no credits, unknown model);
        # the body says so explicitly and is what anyone debugging needs.
        raise RuntimeError(
            f"LLM provider returned {response.status_code} for model '{model}': {response.text[:500]}"
        )
    data = response.json()

    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError(f"LLM returned no choices: {json.dumps(data)[:400]}")
    return choices[0].get("message") or {}


# ══════════════════════════════════════════════════════════════════════════════
# Final-answer validation
# ══════════════════════════════════════════════════════════════════════════════

def _build_response(ctx: ToolContext, args: dict) -> StylistResponse:
    """
    Turn a `present_outfits` tool call into a validated StylistResponse.

    Any ID the model did not actually receive from a tool is dropped — a
    hallucinated ID would otherwise 404 the visualiser downstream.
    """
    from app.services.stylist.prompt_builder import FIELD_SLOTS, SLOT_FIELDS, slot_for_attributes

    message = str(args.get("message") or "Here are some options from your wardrobe.")
    raw_outfits = args.get("outfits") or []
    if isinstance(raw_outfits, dict):
        raw_outfits = [raw_outfits]

    options: list[OutfitOption] = []
    dropped: list[str] = []
    corrected: list[str] = []

    for raw in raw_outfits[:3]:
        if not isinstance(raw, dict):
            continue

        # Place each ID in the slot its own attributes say it belongs to, not the
        # slot the model claimed. Models do put a skirt in `top_id`, and the
        # visualiser would then render it across the torso.
        slots: dict[str, Optional[str]] = {slot: None for slot in SLOT_FIELDS}

        for field, slot in FIELD_SLOTS.items():
            value = raw.get(field)
            if value in (None, "", "null", "None"):
                continue

            value = str(value)
            item = ctx.seen_items.get(value)
            if item is None:
                dropped.append(f"{field}={value}")
                continue

            actual = slot_for_attributes(item.get("category"), item.get("type"))
            if actual not in slots:
                dropped.append(f"{field}={value} ({item.get('category')} is not wearable in an outfit slot)")
                continue

            if actual != slot:
                corrected.append(f"{value}: {field} → {SLOT_FIELDS[actual]}")

            if slots[actual] is None:
                slots[actual] = value
            else:
                dropped.append(f"{value} (duplicate {actual})")

        option = OutfitOption(
            title=str(raw.get("title") or "Outfit"),
            rationale=str(raw.get("rationale") or ""),
            top_id=slots["top"],
            bottom_id=slots["bottom"],
            outerwear_id=slots["outerwear"],
            shoes_id=slots["shoes"],
        )
        # Three cards showing the same garments are one option, not three.
        signature = (option.top_id, option.bottom_id, option.outerwear_id, option.shoes_id)
        if option.item_ids() and signature not in {
            (o.top_id, o.bottom_id, o.outerwear_id, o.shoes_id) for o in options
        }:
            options.append(option)

    if dropped:
        logger.warning("[agent] Dropped %d invalid item ID(s): %s", len(dropped), dropped)
    if corrected:
        logger.info("[agent] Re-slotted %d item(s): %s", len(corrected), corrected)

    if not options and ctx.seen_items:
        logger.warning("[agent] Model produced no usable outfit despite %d retrieved item(s).",
                       len(ctx.seen_items))

    return StylistResponse(message=message, outfits=options)


def _variety_shortfall(response: StylistResponse, ctx: ToolContext) -> Optional[str]:
    """
    Return a corrective instruction if the wardrobe could support more distinct
    outfits than the model actually produced, else None.

    Duplicates are already collapsed by `_build_response`, so a short list here
    means the model reused the same garments rather than that it ran out. Only
    worth asking again when there genuinely are alternatives to reach for.
    """
    from app.services.stylist.prompt_builder import slot_for_attributes

    if len(response.outfits) >= 3:
        return None

    available: dict[str, list[str]] = {}
    for item_id, item in ctx.seen_items.items():
        slot = slot_for_attributes(item.get("category"), item.get("type"))
        available.setdefault(slot, []).append(item_id)

    tops = len(available.get("top", []))
    bottoms = len(available.get("bottom", []))
    if tops < 2 and bottoms < 2:
        return None  # The wardrobe really cannot support three distinct outfits.

    used = {i for o in response.outfits for i in o.item_ids()}
    unused = [
        f"{i} ({ctx.seen_items[i].get('color')} {ctx.seen_items[i].get('type')})"
        for i in available.get("top", []) + available.get("bottom", [])
        if i not in used
    ]

    return (
        f"Only {len(response.outfits)} distinct outfit(s) came through — the rest reused the "
        f"same garments. The wardrobe has {tops} top(s) and {bottoms} bottom(s) available, so "
        "call `present_outfits` again with THREE outfits that each differ in the top or the "
        "bottom. Still respect every weather constraint; if a garment is genuinely unsuitable, "
        "leave it out and say so rather than forcing it."
        + (f" Unused options include: {', '.join(unused[:8])}." if unused else "")
    )


def _fallback_response(ctx: ToolContext, message: str) -> StylistResponse:
    """
    Deterministic outfit assembly when the model never called `present_outfits`.

    Groups whatever the tools retrieved into slots and emits up to three
    combinations, rotating the top so the options actually differ.
    """
    from app.services.stylist.prompt_builder import slot_for_attributes

    buckets: dict[str, list[str]] = {"top": [], "bottom": [], "outerwear": [], "shoes": []}
    for item_id, item in ctx.seen_items.items():
        slot = slot_for_attributes(item.get("category"), item.get("type"))
        buckets.setdefault(slot, []).append(item_id)

    if not any(buckets.values()):
        return StylistResponse(message=message, outfits=[])

    options: list[OutfitOption] = []
    for i in range(min(3, max(len(buckets["top"]), 1))):
        def pick(slot: str, index: int) -> Optional[str]:
            values = buckets.get(slot) or []
            return values[index % len(values)] if values else None

        option = OutfitOption(
            title=f"Option {i + 1}",
            rationale="Assembled directly from your wardrobe.",
            top_id=pick("top", i),
            bottom_id=pick("bottom", i),
            outerwear_id=pick("outerwear", i),
            shoes_id=pick("shoes", i),
        )
        if option.item_ids() and option not in options:
            options.append(option)

    return StylistResponse(message=message, outfits=options)


# ══════════════════════════════════════════════════════════════════════════════
# Agent loop
# ══════════════════════════════════════════════════════════════════════════════

async def run_stylist_agent(
    query: str,
    ctx: ToolContext,
    chat_history: Optional[list[dict]] = None,
) -> AgentResult:
    """Run the tool-calling loop until the model presents outfits or we run out of turns."""
    api_key, _, model, _ = _llm_config()
    if not api_key or api_key in ("YOUR_GROQ_API_KEY", ""):
        logger.error("[agent] No LLM API key configured for provider '%s'.", settings.llm_provider)
        return AgentResult(
            response=StylistResponse(
                message="The styling assistant is not configured yet — no LLM API key is set.",
                outfits=[],
            ),
            tool_calls_made=[], items_seen=0, weather_used=False, iterations=0,
        )

    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for entry in (chat_history or [])[-10:]:
        role = entry.get("role")
        content = entry.get("content")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": query})

    tool_calls_made: list[str] = []
    nudged = False
    diversified = False

    async with httpx.AsyncClient() as client:
        for iteration in range(1, MAX_ITERATIONS + 1):
            try:
                assistant = await _call_llm(client, messages, use_tools=True)
            except Exception as e:
                logger.error("[agent] LLM call failed on iteration %d: %s", iteration, e)
                return AgentResult(
                    response=_fallback_response(
                        ctx,
                        "I had trouble reaching the styling model, so here is a direct "
                        "pick from your wardrobe.",
                    ),
                    tool_calls_made=tool_calls_made,
                    items_seen=len(ctx.seen_items),
                    weather_used=ctx.weather_report is not None,
                    iterations=iteration,
                )

            tool_calls = assistant.get("tool_calls") or []

            if not tool_calls:
                # The model answered in prose. Nudge it once toward the terminal
                # tool; if it refuses again, assemble the answer ourselves.
                content = (assistant.get("content") or "").strip()
                if not nudged:
                    nudged = True
                    messages.append({"role": "assistant", "content": content})
                    messages.append({
                        "role": "user",
                        "content": (
                            "Call the `present_outfits` tool now with your three options. "
                            "Do not reply in plain text."
                        ),
                    })
                    continue

                logger.warning("[agent] Model never called %s; using fallback assembly.", TERMINAL_TOOL)
                return AgentResult(
                    response=_fallback_response(
                        ctx, content or "Here are some options from your wardrobe."
                    ),
                    tool_calls_made=tool_calls_made,
                    items_seen=len(ctx.seen_items),
                    weather_used=ctx.weather_report is not None,
                    iterations=iteration,
                )

            messages.append(assistant)

            final: Optional[StylistResponse] = None
            retry_instruction: Optional[str] = None

            for call in tool_calls:
                function = call.get("function") or {}
                name = function.get("name") or ""
                raw_args = function.get("arguments") or "{}"
                tool_calls_made.append(name)
                logger.info("[agent] iteration %d → tool %s(%s)", iteration, name, raw_args[:160])

                if name == TERMINAL_TOOL:
                    try:
                        args = json.loads(raw_args) if raw_args else {}
                    except json.JSONDecodeError as e:
                        logger.warning("[agent] Malformed %s arguments: %s", TERMINAL_TOOL, e)
                        args = {}

                    candidate = _build_response(ctx, args)
                    shortfall = None if diversified else _variety_shortfall(candidate, ctx)

                    if shortfall:
                        # Send it back once. Every tool call still needs a tool
                        # message or the next request is rejected outright.
                        diversified = True
                        retry_instruction = shortfall
                        logger.info("[agent] Asking again for variety: %d distinct outfit(s).",
                                    len(candidate.outfits))
                        messages.append({
                            "role": "tool",
                            "tool_call_id": call.get("id"),
                            "name": name,
                            "content": json.dumps({"accepted": False, "reason": shortfall}),
                        })
                    else:
                        final = candidate
                        messages.append({
                            "role": "tool",
                            "tool_call_id": call.get("id"),
                            "name": name,
                            "content": json.dumps({"accepted": True}),
                        })
                    continue

                result = await execute_tool(ctx, name, raw_args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.get("id"),
                    "name": name,
                    "content": result,
                })

            if final is not None:
                return AgentResult(
                    response=final,
                    tool_calls_made=tool_calls_made,
                    items_seen=len(ctx.seen_items),
                    weather_used=ctx.weather_report is not None,
                    iterations=iteration,
                )

            if retry_instruction:
                messages.append({"role": "user", "content": retry_instruction})

    logger.warning("[agent] Hit the %d-iteration ceiling without a final answer.", MAX_ITERATIONS)
    return AgentResult(
        response=_fallback_response(
            ctx, "Here are the closest matches I could find in your wardrobe."
        ),
        tool_calls_made=tool_calls_made,
        items_seen=len(ctx.seen_items),
        weather_used=ctx.weather_report is not None,
        iterations=MAX_ITERATIONS,
    )
