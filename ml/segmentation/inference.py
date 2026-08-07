"""
inference.py — Production-Grade Wardrobe Segmentation Pipeline
==============================================================

Architecture:
  Step 0  Route   → decide whether the photo is ON-BODY (person wearing an
                    outfit) or FLAT-LAY (a single garment on a plain surface)
  Step 1  CLIPSeg → semantic heatmap per garment region
  Step 2  Argmax  → assign every pixel to exactly one region, derive a box
  Step 3  SAM2    → pixel-perfect mask from each box prompt
  Step 4  Crop    → transparent PNG per garment, cut from the ORIGINAL
                    full-resolution image so classification sees real detail

Every returned item carries a `region` ("top" / "bottom" / "shoes" / "bag" /
"headwear" / "dress" / "garment"). The classifier uses that region to constrain
its label bank, which is what keeps shoes from being classified as blouses.
"""

import logging
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

from ml.segmentation.model import get_clipseg, get_sam2
from ml.segmentation.utils import create_output_directory, load_image

logger = logging.getLogger(__name__)

_ml_dir = Path(__file__).resolve().parent.parent
OUTPUT_DIRECTORY = str(_ml_dir / ".outputs")

# ── TUNING CONSTANTS ──────────────────────────────────────────────────────────
WORK_DIM            = 640     # Detection resolution (CLIPSeg is 352² internally)
EXPORT_MAX_DIM      = 1536    # Cap on the exported cutout's long edge
CLIPSEG_THRESHOLD   = 0.30    # Min peak confidence to accept a semantic region
PERSON_THRESHOLD    = 0.22    # Skin/face response above this suggests a worn outfit
MIN_REGIONS_ON_BODY = 2       # …or this many distinct garment regions, which is
                              #   the more reliable signal when skin is covered up
DRESS_MARGIN        = 1.25    # Dress must beat BOTH top & bottom by this factor
MIN_ITEM_AREA_RATIO = 0.005   # Drop masks smaller than 0.5% of the image
MAX_ITEM_AREA_RATIO = 0.97    # Drop masks covering almost the entire image
PADDING             = 6       # Extra padding (work-res px) around each crop

# Spatially disjoint regions — argmax assigns each pixel to exactly one of them.
# Outerwear earns its own region because an open coat occupies the flanks while
# the garment underneath holds the centre, so argmax can genuinely split them.
#
# "skin" is not a garment. It competes in the argmax purely so that bare arms and
# legs are claimed by it instead of bleeding into a clothing region — without it,
# the calves below a short dress get exported and classified as "blush leggings".
REGION_PROMPTS: list[tuple[str, str]] = [
    ("top",       "the shirt, t-shirt, blouse or sweater worn on the upper body"),
    ("outerwear", "the open jacket, coat, blazer or cardigan worn as an outer layer"),
    ("bottom",    "the pants, jeans, trousers, shorts or skirt worn on the lower body"),
    ("shoes",     "the shoes, sneakers, boots or sandals on the feet"),
    ("bag",       "the handbag, backpack or purse"),
    ("headwear",  "the hat, cap or beanie worn on the head"),
    ("skin",      "bare uncovered skin, bare arms, bare legs, a face and neck"),
]

NON_GARMENT_REGIONS = frozenset({"skin"})
REGION_NAMES = [name for name, _ in REGION_PROMPTS]

# Probes that are scored but never segmented directly.
DRESS_PROMPT = "a full length dress or gown covering the whole body"
FLATLAY_PROMPT = "the clothing garment"


# ══════════════════════════════════════════════════════════════════════════════
# CLIPSeg helpers
# ══════════════════════════════════════════════════════════════════════════════

def _clipseg_probs(image: Image.Image, prompts: list[str], out_w: int, out_h: int) -> np.ndarray:
    """Run CLIPSeg for every prompt. Returns probabilities shaped (N, out_h, out_w)."""
    processor, model = get_clipseg()

    inputs = processor(
        text=prompts,
        images=[image] * len(prompts),
        padding="max_length",
        return_tensors="pt",
    )

    with torch.no_grad():
        outputs = model(**inputs)

    logits = outputs.logits
    # A single prompt collapses the batch dimension — restore it.
    if logits.ndim == 2:
        logits = logits.unsqueeze(0)

    probs = torch.sigmoid(logits).detach().cpu().numpy()
    return np.stack([cv2.resize(p, (out_w, out_h)) for p in probs])


def _peak(prob_map: np.ndarray) -> float:
    """Robust peak confidence — 99.5th percentile ignores single hot pixels."""
    return float(np.percentile(prob_map, 99.5))


@dataclass
class Scene:
    """Everything one CLIPSeg pass tells us about an image."""
    region_probs: np.ndarray           # (len(REGION_PROMPTS), H, W)
    dress_prob: np.ndarray
    garment_prob: np.ndarray
    peaks: dict[str, float]
    dress_peak: float

    @property
    def person_peak(self) -> float:
        return self.peaks["skin"]

    @property
    def confident_regions(self) -> list[str]:
        return [name for name, peak in self.peaks.items() if peak >= CLIPSEG_THRESHOLD]

    @property
    def confident_garment_regions(self) -> list[str]:
        return [r for r in self.confident_regions if r not in NON_GARMENT_REGIONS]

    def is_on_body(self) -> bool:
        """
        Decide whether someone is wearing these clothes.

        Visible skin is the obvious signal but an unreliable one on its own — a
        hooded sweatshirt shot from below barely shows any. Finding several
        distinct garment regions (a torso above a pair of legs) is the sturdier
        tell, so either signal is enough.
        """
        return (
            self.person_peak >= PERSON_THRESHOLD
            or len(self.confident_garment_regions) >= MIN_REGIONS_ON_BODY
        )


def analyse_scene(image: Image.Image, w: int, h: int) -> Scene:
    """Run every prompt in a single CLIPSeg batch and package the results."""
    prompts = [p for _, p in REGION_PROMPTS] + [DRESS_PROMPT, FLATLAY_PROMPT]

    probs = _clipseg_probs(image, prompts, w, h)
    n = len(REGION_NAMES)
    region_probs = probs[:n]

    return Scene(
        region_probs=region_probs,
        dress_prob=probs[n],
        garment_prob=probs[n + 1],
        peaks={name: _peak(region_probs[i]) for i, name in enumerate(REGION_NAMES)},
        dress_peak=_peak(probs[n]),
    )


# ══════════════════════════════════════════════════════════════════════════════
# SAM2 helper
# ══════════════════════════════════════════════════════════════════════════════

def _sam2_masks(image_np: np.ndarray, boxes: list[list[int]], w: int, h: int) -> list[np.ndarray]:
    """Prompt SAM2 with boxes; return one uint8 mask (0/255) per box at (h, w)."""
    sam2 = get_sam2()
    results = sam2(image_np, bboxes=boxes, verbose=False)

    if not results or results[0].masks is None:
        return []

    masks = []
    for m in results[0].masks.data:
        arr = (m.cpu().numpy() * 255).astype(np.uint8)
        if arr.shape[:2] != (h, w):
            arr = cv2.resize(arr, (w, h), interpolation=cv2.INTER_NEAREST)
        masks.append(arr)
    return masks


def _drop_fragments(mask: np.ndarray, keep_ratio: float = 0.25) -> np.ndarray:
    """
    Keep only the substantial connected components of a mask.

    A real garment cutout is one coherent shape, or a few when an arm crosses it.
    Heavily occluded regions instead come back as a spray of small scraps, which
    then get classified as if they were clothing. Anything under `keep_ratio` of
    the largest component is discarded as debris.
    """
    count, labels, stats, _ = cv2.connectedComponentsWithStats((mask > 127).astype(np.uint8), 8)
    if count <= 1:
        return mask

    areas = stats[1:, cv2.CC_STAT_AREA]
    threshold = areas.max() * keep_ratio
    keep = {i + 1 for i, area in enumerate(areas) if area >= threshold}

    cleaned = np.where(np.isin(labels, list(keep)), mask, 0).astype(np.uint8)
    return cleaned


def _constrain_to_region(sam_mask: np.ndarray, owned: np.ndarray, region: str, stem: str) -> np.ndarray:
    """
    Keep SAM2's crisp edges but confine them to the region CLIPSeg identified.

    Given a box that covers most of the frame, SAM2 will happily return the
    whole box — a garment cutout that still contains the building behind it.
    Intersecting with a generously dilated semantic mask discards that runaway
    while leaving normal masks untouched, since a well-behaved SAM2 mask already
    sits inside its own region.
    """
    kernel = np.ones((21, 21), np.uint8)
    allowed = cv2.dilate(owned, kernel, iterations=2)

    constrained = cv2.bitwise_and(sam_mask, allowed)

    sam_area = int(np.count_nonzero(sam_mask))
    kept_area = int(np.count_nonzero(constrained))
    owned_area = int(np.count_nonzero(owned))

    if kept_area < owned_area * 0.20:
        # SAM2 latched onto something unrelated to this region entirely.
        logger.info("[segmentation] %s: SAM2 mask for '%s' missed the region — using CLIPSeg mask.",
                    stem, region)
        return cv2.morphologyEx(owned, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))

    if sam_area > kept_area * 1.5:
        logger.info("[segmentation] %s: clipped runaway SAM2 mask for '%s' (%d → %d px).",
                    stem, region, sam_area, kept_area)

    return constrained


# ══════════════════════════════════════════════════════════════════════════════
# Export
# ══════════════════════════════════════════════════════════════════════════════

def _export_item(
    mask_work: np.ndarray,
    full_rgb: np.ndarray,
    scale: float,
    region: str,
    image_stem: str,
    index: int,
    output_directory: str,
) -> dict | None:
    """
    Upscale a work-resolution mask back to the original image, crop the garment
    with a soft alpha edge, and write a transparent PNG.
    """
    full_h, full_w = full_rgb.shape[:2]

    mask_full = cv2.resize(mask_work, (full_w, full_h), interpolation=cv2.INTER_LINEAR)
    # Feather the boundary so fabric edges do not look cut out with scissors.
    mask_full = cv2.GaussianBlur(mask_full, (5, 5), 0)

    ys, xs = np.where(mask_full > 127)
    if ys.size == 0:
        return None

    pad = max(1, int(round(PADDING / max(scale, 1e-6))))
    x1 = max(0, int(xs.min()) - pad)
    y1 = max(0, int(ys.min()) - pad)
    x2 = min(full_w, int(xs.max()) + pad + 1)
    y2 = min(full_h, int(ys.max()) + pad + 1)

    if (x2 - x1) < 8 or (y2 - y1) < 8:
        return None

    rgba = np.dstack([full_rgb, mask_full])[y1:y2, x1:x2]
    out_img = Image.fromarray(rgba, mode="RGBA")

    # Keep exported cutouts a sane size for downstream CLIP passes.
    if max(out_img.size) > EXPORT_MAX_DIM:
        ratio = EXPORT_MAX_DIM / max(out_img.size)
        out_img = out_img.resize(
            (int(out_img.width * ratio), int(out_img.height * ratio)),
            Image.Resampling.LANCZOS,
        )

    filename = f"{image_stem}_item_{index}_{region}.png"
    save_path = Path(output_directory) / filename
    out_img.save(save_path)

    return {
        "file_name": filename,
        "path": str(save_path),
        "region": region,
        "label": region,
        "bbox": [int(x1), int(y1), int(x2), int(y2)],
    }


# ══════════════════════════════════════════════════════════════════════════════
# Segmentation strategies
# ══════════════════════════════════════════════════════════════════════════════

def _segment_on_body(scene, image_np, full_rgb, scale, img_area, w, h, stem, out_dir):
    """Multi-garment extraction from a photo of a person wearing an outfit."""
    region_probs, dress_prob, peaks, dress_peak = (
        scene.region_probs, scene.dress_prob, scene.peaks, scene.dress_peak
    )

    # A dress occupies the torso AND the legs, so it competes with top+bottom
    # rather than sitting beside them. Only swap when it clearly beats both —
    # a blazer over a crop top also lights up the dress prompt moderately.
    is_dress = (
        dress_peak >= CLIPSEG_THRESHOLD
        and dress_peak >= peaks["top"] * DRESS_MARGIN
        and dress_peak >= peaks["bottom"] * DRESS_MARGIN
    )

    if is_dress:
        keep = ("outerwear", "shoes", "bag", "headwear", "skin")
        active = [("dress", dress_prob)]
        active += [
            (n, region_probs[i]) for i, n in enumerate(REGION_NAMES)
            if n in keep and peaks[n] >= CLIPSEG_THRESHOLD
        ]
    else:
        active = [
            (n, region_probs[i]) for i, n in enumerate(REGION_NAMES)
            if peaks[n] >= CLIPSEG_THRESHOLD
        ]

    if not active:
        logger.info("[segmentation] %s: no region passed the CLIPSeg threshold.", stem)
        return []

    # Argmax over the active regions guarantees non-overlapping boxes.
    stacked = np.stack([p for _, p in active])
    argmax_map = np.argmax(stacked, axis=0)

    boxes, regions, owned_masks = [], [], []
    for i, (region, prob) in enumerate(active):
        # Skin took part in the argmax so it could claim bare arms and legs.
        # Having done its job, it is not a garment and is never exported.
        if region in NON_GARMENT_REGIONS:
            continue

        owned = ((argmax_map == i) & (prob > 0.10)).astype(np.uint8) * 255
        contours, _ = cv2.findContours(owned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            continue

        # Shoes and bags legitimately appear as two blobs (left/right foot), so
        # union every contour that is at least a third of the largest one.
        largest = max(cv2.contourArea(c) for c in contours)
        keep = [c for c in contours if cv2.contourArea(c) >= largest / 3.0]

        for c in keep if region in ("shoes", "bag") else [max(contours, key=cv2.contourArea)]:
            cx, cy, cw, ch = cv2.boundingRect(c)
            if cw > 5 and ch > 5:
                boxes.append([cx, cy, cx + cw, cy + ch])
                regions.append(region)
                # Per-box semantic mask, used to keep SAM2 honest below.
                blob = np.zeros_like(owned)
                cv2.drawContours(blob, [c], -1, 255, thickness=cv2.FILLED)
                owned_masks.append(blob)

    if not boxes:
        logger.info("[segmentation] %s: no usable bounding boxes.", stem)
        return []

    masks = _sam2_masks(image_np, boxes, w, h)
    if not masks:
        logger.warning("[segmentation] %s: SAM2 returned no masks.", stem)
        return []

    items = []
    for mask, region, owned in zip(masks, regions, owned_masks):
        mask = _drop_fragments(_constrain_to_region(mask, owned, region, stem))
        ratio = float(np.count_nonzero(mask)) / img_area
        if not (MIN_ITEM_AREA_RATIO <= ratio <= MAX_ITEM_AREA_RATIO):
            logger.info("[segmentation] %s: '%s' area ratio %.4f out of range — skipped.",
                        stem, region, ratio)
            continue


        item = _export_item(mask, full_rgb, scale, region, stem, len(items), out_dir)
        if item:
            item["area_ratio"] = round(ratio, 4)
            items.append(item)

    return items


def _segment_flat_lay(scene, image_np, full_rgb, scale, img_area, w, h, stem, out_dir):
    """Single-garment extraction from a flat-lay / hanger / product photo."""
    garment_prob = scene.garment_prob
    logger.info("[segmentation] %s flat-lay garment peak=%.3f", stem, _peak(garment_prob))

    clipseg_mask = (garment_prob > 0.25).astype(np.uint8) * 255
    clipseg_mask = cv2.morphologyEx(clipseg_mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))

    contours, _ = cv2.findContours(clipseg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        cx, cy, cw, ch = cv2.boundingRect(max(contours, key=cv2.contourArea))
        box = [cx, cy, cx + cw, cy + ch]
    else:
        # CLIPSeg found nothing definite — prompt with almost the whole frame,
        # inset by a pixel because SAM2 rejects a box flush with the border.
        box = [1, 1, w - 1, h - 1]

    masks = _sam2_masks(image_np, [box], w, h)
    if masks:
        best = masks[0]
    elif np.count_nonzero(clipseg_mask):
        # SAM2 declined to refine this one. The CLIPSeg mask is coarser but it is
        # a real garment mask, so degrade to it rather than dropping the upload.
        logger.info("[segmentation] %s: SAM2 gave no mask — using the CLIPSeg mask.", stem)
        best = clipseg_mask
    else:
        logger.warning("[segmentation] %s: no flat-lay mask available.", stem)
        return []

    ratio = float(np.count_nonzero(best)) / img_area
    if not (MIN_ITEM_AREA_RATIO <= ratio <= MAX_ITEM_AREA_RATIO):
        logger.info("[segmentation] %s: flat-lay area ratio %.4f out of range.", stem, ratio)
        return []

    item = _export_item(best, full_rgb, scale, "garment", stem, 0, out_dir)
    if not item:
        return []
    item["area_ratio"] = round(ratio, 4)
    return [item]


# ══════════════════════════════════════════════════════════════════════════════
# Public entrypoint
# ══════════════════════════════════════════════════════════════════════════════

def process_image(image_path: str, output_directory: str = OUTPUT_DIRECTORY) -> dict:
    """
    Segment every garment in an image.

    Returns a dict with `success`, `total_items` and an `items` list where each
    entry has file_name / path / region / label / bbox / area_ratio.
    """
    start_time = time.time()
    create_output_directory(output_directory)

    full_image = load_image(image_path)          # PIL RGB, original resolution
    full_rgb = np.array(full_image)
    orig_w, orig_h = full_image.size

    # Detection runs at a reduced resolution; crops are cut from the original.
    scale = min(1.0, WORK_DIM / max(orig_w, orig_h))
    work_w, work_h = max(1, int(orig_w * scale)), max(1, int(orig_h * scale))
    image = full_image.resize((work_w, work_h), Image.Resampling.LANCZOS) if scale < 1.0 else full_image
    image_np = np.array(image)
    img_area = work_w * work_h
    stem = Path(image_path).stem

    result = {
        "success": True,
        "image_name": Path(image_path).name,
        "image_path": image_path,
        "processing_time": None,
        "items": [],
    }

    # ── Step 0: one CLIPSeg pass answers both "who is wearing this?" and
    #            "where is each garment?" ─────────────────────────────────────
    try:
        scene = analyse_scene(image, work_w, work_h)
    except Exception as e:
        logger.error("[segmentation] CLIPSeg pass failed for %s: %s", stem, e, exc_info=True)
        return {"success": False, "error": str(e), "total_items": 0, "items": []}

    mode = "on_body" if scene.is_on_body() else "flat_lay"
    logger.info(
        "[segmentation] %s: person=%.3f regions=%s dress=%.3f → mode=%s",
        stem, scene.person_peak, scene.confident_regions, scene.dress_peak, mode,
    )

    args = (scene, image_np, full_rgb, scale, img_area, work_w, work_h, stem, output_directory)
    try:
        items = _segment_on_body(*args) if mode == "on_body" else _segment_flat_lay(*args)
    except Exception as e:
        logger.error("[segmentation] %s: %s pass failed: %s", stem, mode, e, exc_info=True)
        return {"success": False, "error": str(e), "total_items": 0, "items": []}

    # An on-body photo that yielded nothing is often a close-up of one garment.
    if not items and mode == "on_body":
        logger.info("[segmentation] %s: on-body pass empty — retrying as flat-lay.", stem)
        try:
            items = _segment_flat_lay(*args)
            mode = "flat_lay_fallback"
        except Exception as e:
            logger.error("[segmentation] %s: flat-lay fallback failed: %s", stem, e)

    result["mode"] = mode
    result["person_score"] = round(scene.person_peak, 4)
    result["region_scores"] = {k: round(v, 3) for k, v in scene.peaks.items()}
    result["items"] = items
    result["total_items"] = len(items)
    result["processing_time"] = round(time.time() - start_time, 3)

    logger.info("[segmentation] %s: extracted %d item(s) in %.2fs (%s)",
                stem, len(items), result["processing_time"], mode)
    return result


if __name__ == "__main__":
    import sys
    from pprint import pprint

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    targets = sys.argv[1:]
    if not targets:
        folder = _ml_dir / "test_images"
        exts = {".jpg", ".jpeg", ".png", ".webp"}
        targets = [
            str(p) for p in sorted(folder.iterdir())
            if p.suffix.lower() in exts and not p.name.startswith(".")
        ]

    for path in targets:
        pprint(process_image(path))
