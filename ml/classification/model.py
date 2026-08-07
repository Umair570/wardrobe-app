"""
model.py — Global model loading for the Classification Pipeline.

Architecture: FashionCLIP (patrickjohncyh/fashion-clip)
  - Fine-tuned on fashion data for superior clothing classification
  - Zero-shot classification — no training required, prompts are the labels
  - Same CLIP API, ~600MB, ~0.5s/image on CPU
"""

import torch
import os
from dotenv import load_dotenv
load_dotenv()
from transformers import CLIPProcessor, CLIPModel

_FASHION_CLIP_ID = os.getenv("FASHION_CLIP_MODEL_NAME", "patrickjohncyh/fashion-clip")

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
    "tunic", "peplum top", "halter top", "tube top", "camisole",
    "long sleeve shirt", "baseball t-shirt", "graphic tee",
    # Bottoms
    "pants", "jeans", "trousers", "chinos", "cargo pants",
    "shorts", "bermuda shorts", "denim shorts", "board shorts",
    "leggings", "joggers", "sweatpants", "yoga pants",
    "palazzo pants", "culottes", "flare jeans", "skinny jeans",
    # Dresses & Skirts
    "dress", "maxi dress", "mini dress", "sundress", "evening gown",
    "skirt", "mini skirt", "maxi skirt", "pleated skirt",
    "midi skirt", "pencil skirt", "wrap dress", "shirt dress", "midi dress",
    # Outerwear
    "jacket", "coat", "blazer", "windbreaker", "parka",
    "leather jacket", "denim jacket", "bomber jacket",
    "cardigan", "vest", "gilet", "trench coat", "pea coat",
    "puffer jacket", "poncho", "cape", "shacket", "fleece jacket",
    # Knitwear
    "sweater", "hoodie", "sweatshirt", "pullover", "turtleneck",
    "v-neck sweater", "crewneck sweater", "chunky knit sweater",
    # Suits & Formal
    "suit", "waistcoat", "tuxedo", "suit jacket", "dress pants",
    # Traditional & Specialty
    "kurta", "shalwar kameez", "saree", "kimono", "abaya", "thobe", "kaftan",
    "jumpsuit", "romper", "overalls", "dungarees",
    # Lingerie & Sleepwear
    "pajamas", "nightgown", "robe", "bra", "sports bra", "underwear", "boxers", "briefs",
    # Swimwear
    "swimsuit", "bikini", "swim trunks", "rash guard",
    # Footwear
    "shoes", "sneakers", "boots", "sandals", "heels",
    "loafers", "oxford shoes", "ankle boots", "flip flops",
    "running shoes", "slippers", "combat boots", "chelsea boots",
    "snow boots", "espadrilles", "mules", "slide sandals", "brogues",
    "high tops", "wedge heels", "ballet flats",
    # Bags
    "bag", "handbag", "backpack", "tote bag", "clutch",
    "messenger bag", "crossbody bag", "duffel bag", "wallet", "purse", "fanny pack",
    # Accessories
    "scarf", "winter scarf", "silk scarf", "pashmina",
    "hat", "cap", "baseball cap", "fedora", "bucket hat", "visor", "beanie",
    "belt", "tie", "bow tie", "suspenders",
    "watch", "sunglasses", "gloves", 
    "necklace", "bracelet", "earrings", "ring", "cufflinks",
]

# Map every granular label → broad parent category
CATEGORY_MAP = {
    # Tops
    "shirt": "shirt", "t-shirt": "shirt", "blouse": "shirt", "polo shirt": "shirt",
    "tank top": "shirt", "crop top": "shirt", "henley shirt": "shirt",
    "button-down shirt": "shirt", "flannel shirt": "shirt", "tunic": "shirt",
    "peplum top": "shirt", "halter top": "shirt", "tube top": "shirt",
    "camisole": "shirt", "long sleeve shirt": "shirt", "baseball t-shirt": "shirt",
    "graphic tee": "shirt",
    # Bottoms
    "pants": "pants", "jeans": "pants", "trousers": "pants", "chinos": "pants",
    "cargo pants": "pants", "leggings": "pants", "joggers": "pants",
    "sweatpants": "pants", "yoga pants": "pants", "palazzo pants": "pants",
    "culottes": "pants", "flare jeans": "pants", "skinny jeans": "pants",
    "shorts": "shorts", "bermuda shorts": "shorts", "denim shorts": "shorts",
    "board shorts": "shorts",
    # Dresses & Skirts
    "dress": "dress", "maxi dress": "dress", "mini dress": "dress",
    "sundress": "dress", "evening gown": "dress", "wrap dress": "dress",
    "shirt dress": "dress", "midi dress": "dress",
    "skirt": "skirt", "mini skirt": "skirt", "maxi skirt": "skirt",
    "pleated skirt": "skirt", "midi skirt": "skirt", "pencil skirt": "skirt",
    # Outerwear
    "jacket": "jacket", "coat": "jacket", "blazer": "jacket", "windbreaker": "jacket",
    "parka": "jacket", "leather jacket": "jacket", "denim jacket": "jacket",
    "bomber jacket": "jacket", "cardigan": "jacket", "vest": "jacket", "gilet": "jacket",
    "trench coat": "jacket", "pea coat": "jacket", "puffer jacket": "jacket",
    "poncho": "jacket", "cape": "jacket", "shacket": "jacket", "fleece jacket": "jacket",
    # Knitwear
    "sweater": "sweater", "hoodie": "sweater", "sweatshirt": "sweater",
    "pullover": "sweater", "turtleneck": "sweater", "v-neck sweater": "sweater",
    "crewneck sweater": "sweater", "chunky knit sweater": "sweater",
    # Suits & Formal
    "suit": "suit", "waistcoat": "suit", "tuxedo": "suit", "suit jacket": "suit",
    "dress pants": "suit",
    # Traditional & Specialty
    "kurta": "traditional", "shalwar kameez": "traditional", "saree": "traditional",
    "kimono": "traditional", "abaya": "traditional", "thobe": "traditional", "kaftan": "traditional",
    "jumpsuit": "one-piece", "romper": "one-piece", "overalls": "one-piece", "dungarees": "one-piece",
    # Lingerie & Sleepwear
    "pajamas": "sleepwear", "nightgown": "sleepwear", "robe": "sleepwear",
    "bra": "underwear", "sports bra": "underwear", "underwear": "underwear",
    "boxers": "underwear", "briefs": "underwear",
    # Swimwear
    "swimsuit": "swimwear", "bikini": "swimwear", "swim trunks": "swimwear", "rash guard": "swimwear",
    # Footwear
    "shoes": "shoes", "sneakers": "shoes", "boots": "shoes", "sandals": "shoes",
    "heels": "shoes", "loafers": "shoes", "oxford shoes": "shoes",
    "ankle boots": "shoes", "flip flops": "shoes", "running shoes": "shoes",
    "slippers": "shoes", "combat boots": "shoes", "chelsea boots": "shoes",
    "snow boots": "shoes", "espadrilles": "shoes", "mules": "shoes",
    "slide sandals": "shoes", "brogues": "shoes", "high tops": "shoes",
    "wedge heels": "shoes", "ballet flats": "shoes",
    # Bags
    "bag": "bag", "handbag": "bag", "backpack": "bag", "tote bag": "bag",
    "clutch": "bag", "messenger bag": "bag", "crossbody bag": "bag",
    "duffel bag": "bag", "wallet": "bag", "purse": "bag", "fanny pack": "bag",
    # Accessories
    "scarf": "accessory", "winter scarf": "accessory", "silk scarf": "accessory",
    "pashmina": "accessory", "hat": "accessory", "cap": "accessory",
    "baseball cap": "accessory", "fedora": "accessory", "bucket hat": "accessory",
    "visor": "accessory", "beanie": "accessory", "belt": "accessory",
    "tie": "accessory", "bow tie": "accessory", "suspenders": "accessory",
    "watch": "accessory", "sunglasses": "accessory", "gloves": "accessory",
    "necklace": "accessory", "bracelet": "accessory", "earrings": "accessory",
    "ring": "accessory", "cufflinks": "accessory",
}

# ── REGION → LABEL BANK ───────────────────────────────────────────────────────
# The segmentation stage tells us which body region a cutout came from. Scoring
# a shoe crop against the full 150-label bank invites nonsense matches ("blouse"
# at 0.31), so each region is scored only against labels that can plausibly
# occupy it. Derived from CATEGORY_MAP so the two never drift apart.

REGION_TO_CATEGORIES: dict[str, set[str]] = {
    "top":       {"shirt", "sweater", "suit", "swimwear", "underwear", "sleepwear"},
    "outerwear": {"jacket", "sweater", "suit"},
    # Dresses land here when CLIPSeg reads a knee-length dress as the lower
    # region. Keeping dress categories in this bank lets FashionCLIP settle
    # "midi skirt vs shirt dress" from the cutout, which is a call it makes well.
    "bottom":    {"pants", "shorts", "skirt", "dress", "one-piece"},
    "shoes":     {"shoes"},
    "bag":       {"bag"},
    "dress":     {"dress", "one-piece", "traditional"},
}

HEADWEAR_LABELS = [
    "hat", "cap", "baseball cap", "fedora", "bucket hat", "visor", "beanie",
]


def labels_for_region(region: str | None) -> list[str]:
    """
    Return the candidate label bank for a segmentation region.
    Unknown regions (and flat-lay's generic "garment") get the full bank.
    """
    if region == "headwear":
        return HEADWEAR_LABELS

    categories = REGION_TO_CATEGORIES.get(region or "")
    if not categories:
        return CATEGORY_LABELS

    scoped = [lbl for lbl in CATEGORY_LABELS if CATEGORY_MAP.get(lbl) in categories]
    return scoped or CATEGORY_LABELS


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
    "clothing for summer weather like t-shirt, shorts, tank top, sundress, short sleeves",
    "clothing for winter weather like heavy coat, parka, sweater, scarf, thick jacket",
    "clothing for spring or autumn weather like light jacket, long sleeve shirt, cardigan",
    "all-season versatile year-round clothing like jeans, basic pants, sneakers",
]

SEASON_MAP = {
    "clothing for summer weather like t-shirt, shorts, tank top, sundress, short sleeves": "summer",
    "clothing for winter weather like heavy coat, parka, sweater, scarf, thick jacket": "winter",
    "clothing for spring or autumn weather like light jacket, long sleeve shirt, cardigan": "spring/fall",
    "all-season versatile year-round clothing like jeans, basic pants, sneakers": "all-season",
}

# Override season based on the exact garment type to prevent logic flaws
SEASON_OVERRIDE = {
    "t-shirt": "summer",
    "tank top": "summer",
    "shorts": "summer",
    "bermuda shorts": "summer",
    "denim shorts": "summer",
    "board shorts": "summer",
    "sundress": "summer",
    "skirt": "summer",
    "mini skirt": "summer",
    "maxi skirt": "summer",
    "pleated skirt": "summer",
    "flip flops": "summer",
    "sandals": "summer",
    "swimsuit": "summer",
    "bikini": "summer",
    "swim trunks": "summer",
    "coat": "winter",
    "parka": "winter",
    "scarf": "winter",
    "winter scarf": "winter",
    "beanie": "winter",
    "gloves": "winter",
    "snow boots": "winter",
    "turtleneck": "winter",
    "puffer jacket": "winter",
    "chunky knit sweater": "winter",
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
# 100+ named colors covering every common fashion shade.
# RGB values tuned to match real-world fabric colors.

COLOR_NAMES = {
    # Neutrals
    "black":        (0, 0, 0),
    "charcoal":     (54, 54, 54),
    "dark charcoal":(30, 30, 30),      # Shadow interceptor for pitch dark gray fabric
    "dark gray":    (90, 90, 90),
    "gray":         (140, 140, 140),
    "light gray":   (195, 195, 195),
    "silver":       (210, 210, 210),
    "off-white":    (240, 235, 225),
    "white":        (255, 255, 255),
    "ivory":        (255, 255, 240),
    "cream":        (255, 253, 208),
    "taupe":        (179, 139, 109),
    "greige":       (175, 165, 155),
    "alabaster":    (242, 240, 230),
    "oat":          (223, 208, 184),

    # Browns & Tans
    "brown":        (120, 66, 18),
    "dark brown":   (75, 40, 10),
    "very dark brown": (45, 25, 10),
    "chocolate":    (92, 51, 23),
    "tan":          (190, 150, 110),
    "camel":        (193, 154, 107),
    "beige":        (205, 185, 155),
    "sand":         (225, 210, 180),
    "khaki":        (170, 160, 120),
    "coffee":       (110, 70, 35),
    "rust":         (183, 65, 14),
    "terracotta":   (226, 114, 91),
    "mahogany":     (192, 64, 0),

    # Reds
    "red":          (210, 30, 30),
    "dark red":     (139, 0, 0),
    "maroon":       (110, 20, 20),
    "burgundy":     (128, 0, 32),
    "crimson":      (173, 25, 45),
    "wine":         (114, 22, 38),
    "coral":        (255, 127, 80),
    "salmon":       (250, 128, 114),
    "ruby":         (224, 17, 95),
    "brick red":    (203, 65, 84),
    "cherry":       (222, 49, 99),

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
    "dark olive":   (60, 65, 40),      # Explicit hook for completely undersaturated shadow greens
    "army green":   (75, 83, 32),
    "sage":         (140, 160, 120),
    "mint":         (152, 224, 173),
    "lime":         (150, 205, 50),
    "emerald":      (0, 155, 85),
    "teal":         (0, 128, 128),
    "seafoam":      (159, 226, 191),
    "hunter green": (53, 94, 59),
    "chartreuse":   (127, 255, 0),
    "jade":         (0, 168, 107),
    "pistachio":    (147, 197, 114),

    # Blues
    "blue":         (70, 130, 180),
    "light blue":   (140, 190, 220),
    "sky blue":     (120, 186, 230),
    "baby blue":    (160, 210, 235),
    "navy":         (20, 30, 80),
    "dark navy":    (15, 15, 35),      # Shadow interceptor for pitch dark blue fabric
    "dark blue":    (10, 20, 100),
    "royal blue":   (40, 80, 180),
    "cobalt":       (0, 71, 171),
    "denim":        (92, 132, 172),
    "indigo":       (50, 0, 110),
    "cyan":         (0, 200, 220),
    "turquoise":    (64, 200, 200),
    "sapphire":     (15, 82, 186),
    "cerulean":     (0, 123, 167),
    "slate blue":   (106, 90, 205),
    "midnight blue":(25, 25, 112),

    # Purples
    "purple":       (128, 0, 128),
    "dark purple":  (70, 0, 90),
    "plum":         (142, 69, 133),
    "lavender":     (180, 150, 210),
    "lilac":        (200, 162, 200),
    "mauve":        (153, 102, 153),
    "violet":       (127, 0, 255),
    "magenta":      (200, 0, 130),
    "eggplant":     (97, 64, 81),

    # Pinks
    "pink":         (255, 182, 193),
    "light pink":   (255, 210, 215),
    "hot pink":     (255, 65, 145),
    "blush":        (222, 165, 164),
    "rose":         (200, 100, 120),
    "fuchsia":      (215, 0, 120),
    "dusty pink":   (210, 140, 150),
    "flamingo":     (252, 142, 172),
    "bubblegum":    (255, 193, 204),
}