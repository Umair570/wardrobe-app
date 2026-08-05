from app.services.stylist.schemas import WardrobeItem

def get_slot(item: WardrobeItem) -> str:
    """Outfit Engine categorization logic."""
    cat = (item.category or "").lower()
    typ = (item.type or "").lower()
    
    if "jacket" in typ or "coat" in typ or "blazer" in typ or "hoodie" in typ or cat == "outerwear":
        return "outerwear"
    if "shoe" in typ or "boot" in typ or "sneaker" in typ or "heel" in typ or cat == "shoes":
        return "shoes"
    if "pant" in typ or "trouser" in typ or "short" in typ or "skirt" in typ or "jean" in typ or cat == "lower_body" or cat == "bottom":
        return "bottom"
    return "top"  # Default fallback for shirts, sweaters, t-shirts, etc.

def build_system_prompt(items: list[WardrobeItem], weather_context: str | None = None) -> str:
    """
    Constructs the system prompt for the Groq Stylist.
    Phase 11: Outfit Engine Validation Layer groups items by slot.
    """
    if not items:
        context_str = "The user has no items in their wardrobe."
    else:
        # Build flattened readable list of all wardrobe items. Trust the LLM to identify the garments natively.
        categories = {"outerwear": [], "top": [], "bottom": [], "shoes": []}
        for i in items:
            slot = get_slot(i)
            desc = f"ID: {i.id}"
            if i.type or i.category or i.color:
                desc += f" ({i.color} {i.type} / {i.category})"
            categories[slot].append(" - " + desc)
            
        lines = ["\n--- AVAILABLE ITEMS BY CATEGORY ---"]
        for slot, slot_items in categories.items():
            lines.append(f"\n[{slot.upper()}]")
            if not slot_items:
                lines.append(" - No items available")
            else:
                lines.extend(slot_items)
            
        context_str = "\n".join(lines)

    if weather_context:
        context_str = f"ENVIRONMENTAL CONSTRAINTS:\n{weather_context}\n\n" + context_str

    return f"""You are a professional fashion stylist AI.
Your goal is to recommend an outfit based on the user's query and their available wardrobe items.

AVAILABLE WARDROBE ITEMS:
{context_str}

CONSTRAINTS & RULES:
1. You MUST ONLY recommend items that exist in the AVAILABLE WARDROBE ITEMS list above.
2. You MUST critically evaluate if the returned items are reasonably appropriate for the user's request. If the available items (e.g., heavy hoodies/flannels) are DANGEROUSLY inappropriate for the requested scenario (e.g., a summer beach party at 95F, or shorts in a blizzard), YOU MUST NOT force an outfit. However, for mild mismatches (e.g. wearing a hoodie in 65F drizzle), you SHOULD recommend the best available items from their wardrobe rather than rejecting their entire closet. Always try to build an outfit if it's safe and reasonable.
3. DO NOT hallucinate or invent item IDs. If a suitable item is not available, leave that field as exactly null (without quotes, as a literal JSON null).
4. CRITICAL: If you mention recommending an item in your text `message` (e.g. "I recommend the charcoal chinos"), you MUST place that item's exact ID into the corresponding JSON field (e.g. `bottom_id`). NEVER mention an item in the text but fail to include its ID in the JSON block below.
5. You must output exactly in JSON format, matching this schema:

{{
  "message": "A confident, friendly explanation of why you chose this outfit.",
  "outfit": {{
    "top_id": "string (or literal null) - Exact ID from [TOP]",
    "bottom_id": "string (or literal null) - Exact ID from [BOTTOM]",
    "outerwear_id": "string (or literal null) - Exact ID from [OUTERWEAR]",
    "shoes_id": "string (or literal null) - Exact ID from [SHOES]"
  }}
}}

5. IF the retrieved wardrobe options are completely contextually irrelevant to the user's styling request, DO NOT blindly force an outfit. Politely decline generation in the `message` string, and set all `outfit` IDs to literal null (without quotes).
"""
