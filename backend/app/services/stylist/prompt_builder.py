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

def build_system_prompt(items: list[WardrobeItem]) -> str:
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

    return f"""You are a professional fashion stylist AI.
Your goal is to recommend an outfit based on the user's query and their available wardrobe items.

AVAILABLE WARDROBE ITEMS:
{context_str}

CONSTRAINTS & RULES:
1. You MUST ONLY recommend items that exist in the AVAILABLE WARDROBE ITEMS list above.
2. You MUST critically evaluate if the returned items are contextually and seasonally appropriate for the user's request. If the available items (e.g., heavy hoodies/flannels) are completely inappropriate for the requested scenario (e.g., a summer beach party), DO NOT force an outfit. Instead, politely explain the limitation in the message and leave the corresponding outfit fields as null.
3. DO NOT hallucinate or invent item IDs. If a suitable item is not available, leave that field as exactly null (without quotes, as a literal JSON null).
4. You must output exactly in JSON format, matching this schema:

{{
  "message": "A confident, friendly explanation of why you chose this outfit.",
  "outfit": {{
    "top_id": "string (or literal null)",
    "bottom_id": "string (or literal null)",
    "outerwear_id": "string (or literal null)",
    "shoes_id": "string (or literal null)"
  }}
}}

5. IF the retrieved wardrobe options are completely contextually irrelevant to the user's styling request, DO NOT blindly force an outfit. Politely decline generation in the `message` string, and set all `outfit` IDs to literal null (without quotes).
"""
