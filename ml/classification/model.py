"""
model.py — Global model loading for the Classification Pipeline.

Architecture: FashionCLIP (patrickjohncyh/fashion-clip)
  - Fine-tuned on fashion data for superior clothing classification
  - Zero-shot classification — no training required, prompts are the labels
  - Same CLIP API, ~600MB, ~0.5s/image on CPU
"""

import torch
from transformers import CLIPProcessor, CLIPModel

_FASHION_CLIP_ID = "patrickjohncyh/fashion-clip"

print("Loading FashionCLIP for zero-shot clothing classification...")
CLIP_CLASSIFIER_PROCESSOR = CLIPProcessor.from_pretrained(_FASHION_CLIP_ID)
CLIP_CLASSIFIER_MODEL     = CLIPModel.from_pretrained(_FASHION_CLIP_ID)
CLIP_CLASSIFIER_MODEL.eval()
print("FashionCLIP classifier loaded.\n")

# ══════════════════════════════════════════════════════════════════════════════
# LABEL BANKS — Production-grade label sets for zero-shot classification
# ══════════════════════════════════════════════════════════════════════════════

# ── CATEGORY LABELS (garment type) ────────────────────────────────────────────
# CLIP scores each image against ALL of these to find the best match.
# The winning label becomes the "type", and CATEGORY_MAP maps it to a broad "category".

CATEGORY_LABELS = [
    # Tops
    "shirt", "t-shirt", "blouse", "polo shirt", "tank top", "crop top",
    "henley shirt", "button-down shirt", "flannel shirt",
    # Bottoms
    "pants", "jeans", "trousers", "chinos", "cargo pants",
    "shorts", "bermuda shorts", "denim shorts",
    "leggings", "joggers", "sweatpants",
    # Dresses & Skirts
    "dress", "maxi dress", "mini dress", "sundress", "evening gown",
    "skirt", "mini skirt", "maxi skirt", "pleated skirt",
    # Outerwear
    "jacket", "coat", "blazer", "windbreaker", "parka",
    "leather jacket", "denim jacket", "bomber jacket",
    "cardigan", "vest", "gilet",
    # Knitwear
    "sweater", "hoodie", "sweatshirt", "pullover", "turtleneck",
    # Suits & Formal
    "suit", "waistcoat",
    # Footwear
    "shoes", "sneakers", "boots", "sandals", "heels",
    "loafers", "oxford shoes", "ankle boots", "flip flops",
    "running shoes", "slippers",
    # Bags
    "bag", "handbag", "backpack", "tote bag", "clutch",
    "messenger bag", "crossbody bag", "duffel bag", "wallet", "purse",
    # Accessories
    "scarf", "hat", "cap", "belt", "tie", "bow tie",
    "watch", "sunglasses", "gloves", "beanie",
    "necklace", "bracelet", "earrings", "ring",
]

# Map every granular label → broad parent category
CATEGORY_MAP = {
    # Tops
    "shirt": "shirt", "t-shirt": "shirt", "blouse": "shirt", "polo shirt": "shirt",
    "tank top": "shirt", "crop top": "shirt", "henley shirt": "shirt",
    "button-down shirt": "shirt", "flannel shirt": "shirt",
    # Bottoms
    "pants": "pants", "jeans": "pants", "trousers": "pants", "chinos": "pants",
    "cargo pants": "pants", "leggings": "pants", "joggers": "pants", "sweatpants": "pants",
    "shorts": "shorts", "bermuda shorts": "shorts", "denim shorts": "shorts",
    # Dresses & Skirts
    "dress": "dress", "maxi dress": "dress", "mini dress": "dress",
    "sundress": "dress", "evening gown": "dress",
    "skirt": "skirt", "mini skirt": "skirt", "maxi skirt": "skirt", "pleated skirt": "skirt",
    # Outerwear
    "jacket": "jacket", "coat": "jacket", "blazer": "jacket", "windbreaker": "jacket",
    "parka": "jacket", "leather jacket": "jacket", "denim jacket": "jacket",
    "bomber jacket": "jacket", "cardigan": "jacket", "vest": "jacket", "gilet": "jacket",
    # Knitwear
    "sweater": "sweater", "hoodie": "sweater", "sweatshirt": "sweater",
    "pullover": "sweater", "turtleneck": "sweater",
    # Suits
    "suit": "suit", "waistcoat": "suit",
    # Footwear
    "shoes": "shoes", "sneakers": "shoes", "boots": "shoes", "sandals": "shoes",
    "heels": "shoes", "loafers": "shoes", "oxford shoes": "shoes",
    "ankle boots": "shoes", "flip flops": "shoes", "running shoes": "shoes",
    "slippers": "shoes",
    # Bags
    "bag": "bag", "handbag": "bag", "backpack": "bag", "tote bag": "bag",
    "clutch": "bag", "messenger bag": "bag", "crossbody bag": "bag",
    "duffel bag": "bag", "wallet": "bag", "purse": "bag",
    # Accessories
    "scarf": "accessory", "hat": "accessory", "cap": "accessory", "belt": "accessory",
    "tie": "accessory", "bow tie": "accessory", "watch": "accessory",
    "sunglasses": "accessory", "gloves": "accessory", "beanie": "accessory",
    "necklace": "accessory", "bracelet": "accessory", "earrings": "accessory",
    "ring": "accessory",
}

# ── STYLE / FORMALITY LABELS ─────────────────────────────────────────────────

STYLE_LABELS = [
    "casual everyday clothing, basic simple outfit",
    "formal professional business clothing, suit dress shirt",
    "sportswear athletic gym workout clothing",
    "streetwear urban trendy fashion clothing",
    "traditional ethnic cultural clothing",
    "loungewear pajamas sleepwear comfortable home clothing",
    "party evening glamorous night-out clothing",
    "bohemian boho free-spirited layered clothing",
    "minimalist clean modern simple clothing",
    "vintage retro old-school classic clothing",
]

STYLE_MAP = {
    "casual everyday clothing, basic simple outfit": "casual",
    "formal professional business clothing, suit dress shirt": "formal",
    "sportswear athletic gym workout clothing": "sportswear",
    "streetwear urban trendy fashion clothing": "streetwear",
    "traditional ethnic cultural clothing": "traditional",
    "loungewear pajamas sleepwear comfortable home clothing": "loungewear",
    "party evening glamorous night-out clothing": "party",
    "bohemian boho free-spirited layered clothing": "bohemian",
    "minimalist clean modern simple clothing": "minimalist",
    "vintage retro old-school classic clothing": "vintage",
}

# ── SEASON LABELS ─────────────────────────────────────────────────────────────

SEASON_LABELS = [
    "summer lightweight breathable clothing",
    "winter warm thick heavy clothing",
    "spring autumn transitional layering clothing",
    "all-season versatile year-round clothing",
]

SEASON_MAP = {
    "summer lightweight breathable clothing": "summer",
    "winter warm thick heavy clothing": "winter",
    "spring autumn transitional layering clothing": "spring/fall",
    "all-season versatile year-round clothing": "all-season",
}

# ── PATTERN LABELS ────────────────────────────────────────────────────────────

PATTERN_LABELS = [
    "solid plain single color clothing",
    "striped lines pattern clothing",
    "plaid checkered tartan pattern clothing",
    "floral flower pattern clothing",
    "polka dot spotted pattern clothing",
    "geometric abstract pattern clothing",
    "camouflage military camo pattern clothing",
    "animal print leopard zebra pattern clothing",
    "tie-dye colorful swirl pattern clothing",
    "graphic printed logo text pattern clothing",
]

PATTERN_MAP = {
    "solid plain single color clothing": "solid",
    "striped lines pattern clothing": "striped",
    "plaid checkered tartan pattern clothing": "plaid",
    "floral flower pattern clothing": "floral",
    "polka dot spotted pattern clothing": "polka dot",
    "geometric abstract pattern clothing": "geometric",
    "camouflage military camo pattern clothing": "camo",
    "animal print leopard zebra pattern clothing": "animal print",
    "tie-dye colorful swirl pattern clothing": "tie-dye",
    "graphic printed logo text pattern clothing": "graphic",
}

# ── COMPLETE COLOR PALETTE ────────────────────────────────────────────────────
# 50+ named colors covering every common fashion shade.
# RGB values tuned to match real-world fabric colors, not pure digital values.

COLOR_NAMES = {
    # Neutrals
    "black":        (0, 0, 0),
    "charcoal":     (54, 54, 54),
    "dark gray":    (90, 90, 90),
    "gray":         (140, 140, 140),
    "light gray":   (195, 195, 195),
    "silver":       (210, 210, 210),
    "off-white":    (240, 235, 225),
    "white":        (255, 255, 255),
    "ivory":        (255, 255, 240),
    "cream":        (255, 253, 208),

    # Browns & Tans
    "brown":        (120, 66, 18),
    "dark brown":   (75, 40, 10),
    "chocolate":    (92, 51, 23),
    "tan":          (210, 180, 140),
    "camel":        (193, 154, 107),
    "beige":        (232, 215, 185),
    "sand":         (220, 200, 160),
    "khaki":        (170, 160, 120),
    "coffee":       (110, 70, 35),
    "rust":         (183, 65, 14),

    # Reds
    "red":          (210, 30, 30),
    "dark red":     (139, 0, 0),
    "maroon":       (110, 20, 20),
    "burgundy":     (128, 0, 32),
    "crimson":      (173, 25, 45),
    "wine":         (114, 22, 38),
    "coral":        (255, 127, 80),
    "salmon":       (250, 128, 114),

    # Oranges & Yellows
    "orange":       (240, 140, 20),
    "burnt orange":  (191, 87, 0),
    "peach":        (255, 200, 160),
    "apricot":      (251, 206, 177),
    "yellow":       (240, 210, 30),
    "mustard":      (210, 170, 30),
    "gold":         (218, 185, 45),
    "amber":        (255, 191, 0),
    "lemon":        (255, 247, 100),

    # Greens
    "green":        (34, 120, 50),
    "dark green":   (0, 80, 20),
    "forest green": (34, 90, 34),
    "olive":        (107, 112, 47),
    "army green":   (75, 83, 32),
    "sage":         (140, 160, 120),
    "mint":         (152, 224, 173),
    "lime":         (150, 205, 50),
    "emerald":      (0, 155, 85),
    "teal":         (0, 128, 128),

    # Blues
    "blue":         (70, 130, 180),
    "light blue":   (140, 190, 220),
    "sky blue":     (120, 186, 230),
    "baby blue":    (160, 210, 235),
    "navy":         (20, 30, 80),
    "dark blue":    (10, 20, 100),
    "royal blue":   (40, 80, 180),
    "cobalt":       (0, 71, 171),
    "denim":        (92, 132, 172),
    "indigo":       (50, 0, 110),
    "cyan":         (0, 200, 220),
    "turquoise":    (64, 200, 200),

    # Purples
    "purple":       (128, 0, 128),
    "dark purple":  (70, 0, 90),
    "plum":         (142, 69, 133),
    "lavender":     (180, 150, 210),
    "lilac":        (200, 162, 200),
    "mauve":        (153, 102, 153),
    "violet":       (127, 0, 255),
    "magenta":      (200, 0, 130),

    # Pinks
    "pink":         (255, 182, 193),
    "light pink":   (255, 210, 215),
    "hot pink":     (255, 65, 145),
    "blush":        (222, 165, 164),
    "rose":         (200, 100, 120),
    "fuchsia":      (215, 0, 120),
    "dusty pink":   (200, 150, 155),
}
