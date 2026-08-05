"""Outfit slot classification shared by the agent and the visualization layer."""

from app.services.stylist.schemas import WardrobeItem

# Broad ML categories (from CATEGORY_MAP in ml/classification/model.py) → outfit slot.
# "other" marks things that are real wardrobe items but do not occupy one of the
# four outfit slots the visualiser renders.
_CATEGORY_SLOTS: dict[str, str] = {
    "jacket": "outerwear",
    "shoes": "shoes",
    "pants": "bottom",
    "shorts": "bottom",
    "skirt": "bottom",
    "shirt": "top",
    "sweater": "top",
    "suit": "top",
    "dress": "top",
    "one-piece": "top",
    "traditional": "top",
    "swimwear": "top",
    "underwear": "top",
    "sleepwear": "top",
    "bag": "other",
    "accessory": "other",
}

OUTFIT_SLOTS = ("top", "bottom", "outerwear", "shoes")

# Outfit field name on OutfitRecommendation ↔ slot.
SLOT_FIELDS: dict[str, str] = {
    "top": "top_id",
    "bottom": "bottom_id",
    "outerwear": "outerwear_id",
    "shoes": "shoes_id",
}
FIELD_SLOTS: dict[str, str] = {field: slot for slot, field in SLOT_FIELDS.items()}

_OUTERWEAR_TERMS = ("jacket", "coat", "blazer", "hoodie", "parka", "cardigan", "windbreaker")
_SHOE_TERMS = ("shoe", "boot", "sneaker", "heel", "sandal", "loafer", "flip flop", "espadrille")
_BOTTOM_TERMS = ("pant", "trouser", "short", "skirt", "jean", "chino", "legging", "jogger")


def slot_for_attributes(category: str | None, type_: str | None) -> str:
    """
    Map a garment's category/type onto one of: outerwear | shoes | bottom | top.

    The broad category is authoritative when we recognise it; the granular type
    is only consulted as a fallback, because a "denim jacket" whose category is
    already "jacket" should not be re-derived from substring matching.
    """
    cat = (category or "").lower().strip()
    typ = (type_ or "").lower().strip()

    if cat in _CATEGORY_SLOTS:
        return _CATEGORY_SLOTS[cat]

    if any(term in typ for term in _OUTERWEAR_TERMS):
        return "outerwear"
    if any(term in typ for term in _SHOE_TERMS):
        return "shoes"
    if any(term in typ for term in _BOTTOM_TERMS):
        return "bottom"
    return "top"


def get_slot(item: WardrobeItem) -> str:
    """Slot for a WardrobeItem."""
    return slot_for_attributes(item.category, item.type)
