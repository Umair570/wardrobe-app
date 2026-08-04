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
        # Group items by slot
        slots = {"top": [], "bottom": [], "outerwear": [], "shoes": []}
        for i in items:
            slot = get_slot(i)
            desc = [f"ID: {i.id}"]
            if i.type or i.category:
                desc.append(f"({i.category} / {i.type})")
            if i.color:
                desc.append(f"Color: {i.color}")
            if i.style:
                desc.append(f"Style: {i.style}")
            if i.season:
                desc.append(f"Season: {i.season}")
            slots[slot].append(" - " + ", ".join(desc))
            
        # Build readable categorized list
        lines = []
        for slot_name, slot_items in slots.items():
            if slot_items:
                lines.append(f"\n--- {slot_name.upper()} OPTIONS ---")
                lines.extend(slot_items)
        
        context_str = "\n".join(lines)

    return f"""You are a professional fashion stylist AI.
Your goal is to recommend an outfit based on the user's query and their available wardrobe items.

AVAILABLE WARDROBE ITEMS:
{context_str}

CONSTRAINTS & RULES:
1. You MUST ONLY recommend items that exist in the AVAILABLE WARDROBE ITEMS list above.
2. DO NOT hallucinate or invent item IDs. If a suitable item is not available, leave that field as null.
3. You must output exactly in JSON format, matching this schema:

{{
  "message": "A friendly explanation of why you chose this outfit.",
  "outfit": {{
    "top_id": "string (or null)",
    "bottom_id": "string (or null)",
    "outerwear_id": "string (or null)",
    "shoes_id": "string (or null)"
  }}
}}
"""
