"""
inference.py — Production-Grade Clothing Classification Pipeline
================================================================

Takes a segmented transparent PNG and outputs structured metadata:
  - category:   broad garment class (shirt, pants, shoes, bag, etc.)
  - type:       specific sub-type (jeans, polo, sneakers, etc.)
  - style:      formality tag (casual, formal, sportswear, streetwear, traditional)
  - color:      dominant color name from non-transparent pixels
  - confidence: per-field classification confidence scores
  - tags:       auto-generated searchable list combining all fields

Architecture:
  1. CLIP zero-shot → category + type (one pass)
  2. CLIP zero-shot → style (second pass with style-specific prompts)
  3. OpenCV KMeans  → dominant color from foreground pixels
  4. Tag builder    → combine all fields into flat searchable tags list
"""

import torch
import numpy as np
import cv2
from PIL import Image
from pathlib import Path
from pprint import pprint
from sklearn.cluster import KMeans

from ml.classification.model import (
    CLIP_CLASSIFIER_PROCESSOR,
    CLIP_CLASSIFIER_MODEL,
    CATEGORY_LABELS,
    CATEGORY_MAP,
    STYLE_LABELS,
    STYLE_MAP,
    SEASON_LABELS,
    SEASON_MAP,
    SEASON_OVERRIDE,
    PATTERN_LABELS,
    PATTERN_MAP,
    COLOR_NAMES,
    labels_for_region,
)


def _load_rgba_image(image_path: str) -> tuple[Image.Image, np.ndarray]:
    """
    Load a transparent PNG. Returns (composited RGB image, alpha mask as uint8).

    `.convert("RGB")` would merely DISCARD the alpha channel, leaving the
    original background pixels visible underneath the cutout — CLIP would then
    classify the scene rather than the garment. Compositing over a neutral grey
    removes the background for real, matching the product-shot distribution
    FashionCLIP was trained on.
    """
    img = Image.open(image_path).convert("RGBA")
    arr = np.array(img)
    alpha = arr[:, :, 3]

    backdrop = Image.new("RGBA", img.size, (240, 240, 240, 255))
    rgb = Image.alpha_composite(backdrop, img).convert("RGB")
    return rgb, alpha


def _clip_zero_shot(image: Image.Image, candidate_labels: list[str]) -> tuple[str, float, dict]:
    """
    Run CLIP zero-shot classification on an image against candidate labels.
    Returns (best_label, best_score, all_scores_dict).

    Bare nouns ("polo shirt") sit off-distribution for CLIP's text tower, which
    was trained on captions. Short label banks are therefore wrapped in the
    standard "a photo of a …" template; long descriptive prompts (style, season,
    pattern) are already sentence-shaped and are passed through untouched.
    """
    prompts = [
        lbl if len(lbl.split()) > 4 else f"a photo of a {lbl}"
        for lbl in candidate_labels
    ]

    inputs = CLIP_CLASSIFIER_PROCESSOR(
        text=prompts,
        images=image,
        return_tensors="pt",
        padding=True,
    )

    with torch.no_grad():
        outputs = CLIP_CLASSIFIER_MODEL(**inputs)

    # logits_per_image shape: (1, num_labels)
    logits = outputs.logits_per_image[0]
    probs  = torch.softmax(logits, dim=0).cpu().numpy()

    scores = {label: round(float(prob), 4) for label, prob in zip(candidate_labels, probs)}
    best_idx   = int(np.argmax(probs))
    best_label = candidate_labels[best_idx]
    best_score = float(probs[best_idx])

    return best_label, best_score, scores


def _extract_dominant_color(image_np_rgb: np.ndarray, alpha: np.ndarray, n_clusters: int = 5) -> str:
    """
    Extract the dominant color name from non-transparent foreground pixels.

    Strategy:
      1. KMeans cluster the foreground pixels into n groups.
      2. Discard clusters that are just shadow — materially darker than the
         garment as a whole — unless the garment is genuinely dark throughout.
      3. Among what survives, pick the cluster covering the most fabric.
      4. Map the winning cluster center to the nearest named color.

    Picking the *most saturated* cluster instead (as this once did) reliably
    fails on pale garments: a pale pink coat's shadowed folds are far more
    saturated than its lit face, so the shadow wins and the coat reads "coffee".
    Fabric area is the honest signal; shadow rejection is what protects it.
    """
    # Alpha > 200 keeps feathered edge pixels (part background) out of the vote.
    fg_pixels = image_np_rgb[alpha > 200]

    if len(fg_pixels) < 10:
        return "unknown"

    if len(fg_pixels) > 8000:
        indices = np.random.choice(len(fg_pixels), 8000, replace=False)
        fg_pixels = fg_pixels[indices]

    fg_float = fg_pixels.astype(np.float32)
    actual_clusters = min(n_clusters, len(fg_pixels))
    kmeans = KMeans(n_clusters=actual_clusters, n_init=5, random_state=42)
    kmeans.fit(fg_float)

    centers = kmeans.cluster_centers_                        # (k, 3) RGB
    counts = np.bincount(kmeans.labels_, minlength=actual_clusters)
    volumes = counts.astype(np.float32) / max(counts.sum(), 1)

    # Perceptual lightness (CIE L*) of each cluster and of the garment overall.
    centers_uint8 = np.clip(centers, 0, 255).astype(np.uint8).reshape(1, -1, 3)
    centers_lab = cv2.cvtColor(centers_uint8, cv2.COLOR_RGB2LAB).reshape(-1, 3)
    center_lightness = centers_lab[:, 0].astype(np.float32)

    fg_lab = cv2.cvtColor(
        fg_pixels.reshape(1, -1, 3).astype(np.uint8), cv2.COLOR_RGB2LAB
    ).reshape(-1, 3)
    garment_lightness = float(np.median(fg_lab[:, 0]))

    DARK_GARMENT_L = 60          # Below this the item really is dark (OpenCV L* is 0-255)
    SHADOW_RATIO = 0.70          # Clusters below this share of overall lightness are shadow
    MIN_VOLUME = 0.05            # Ignore slivers

    candidates = [i for i in range(actual_clusters) if volumes[i] >= MIN_VOLUME]
    if not candidates:
        candidates = list(range(actual_clusters))

    # For a genuinely dark garment every cluster is dark, so shadow rejection
    # would throw away the real colour. Only apply it to mid/light garments.
    if garment_lightness >= DARK_GARMENT_L:
        lit = [i for i in candidates if center_lightness[i] >= garment_lightness * SHADOW_RATIO]
        if lit:
            candidates = lit

    best_idx = max(candidates, key=lambda i: volumes[i])
    return _nearest_color_name(centers[best_idx])


def _nearest_color_name(rgb: np.ndarray) -> str:
    """Map an RGB triplet to the nearest named color using CIE Lab perceptual distance."""
    # Convert input RGB to Lab
    rgb_uint8 = np.uint8([[[rgb[0], rgb[1], rgb[2]]]])
    lab_pixel = cv2.cvtColor(rgb_uint8, cv2.COLOR_RGB2LAB)[0][0]
    
    min_dist = float("inf")
    best_name = "unknown"

    for name, ref_rgb in COLOR_NAMES.items():
        ref_uint8 = np.uint8([[[ref_rgb[0], ref_rgb[1], ref_rgb[2]]]])
        ref_lab = cv2.cvtColor(ref_uint8, cv2.COLOR_RGB2LAB)[0][0]
        
        # Standard Euclidean distance in perceptual LAB space (Delta-E CIE76)
        dist = np.sqrt(np.sum((lab_pixel.astype(np.float32) - ref_lab.astype(np.float32)) ** 2))
        
        if dist < min_dist:
            min_dist = dist
            best_name = name

    return best_name


def classify_item(image_path: str, region: str | None = None) -> dict:
    """
    Classify a single segmented clothing item.

    Args:
        image_path: Path to a transparent PNG from the segmentation pipeline.
        region:     Body region the cutout came from ("top", "bottom", "shoes",
                    "bag", "headwear", "dress"). Constrains the label bank so a
                    shoe crop can never be scored against "blouse". None or
                    "garment" (flat-lay) scores against every label.

    Returns:
        Dictionary with keys: category, type, style, season, pattern, color,
        confidence, tags, region
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    # ── Load image ────────────────────────────────────────────────────────────
    rgb_image, alpha = _load_rgba_image(image_path)

    # ── Step 1: Category + Type (one CLIP call) ──────────────────────────────
    # CLIP scores the crop against every label the region can plausibly contain.
    # The best match gives us both the specific type AND the broad category.
    candidate_labels = labels_for_region(region)
    best_type, type_conf, all_type_scores = _clip_zero_shot(rgb_image, candidate_labels)

    category = CATEGORY_MAP.get(best_type, best_type)

    # ── Step 2: Formality, Season, and Pattern (CLIP Zero-Shot) ───────────────
    best_style_raw, style_conf, _ = _clip_zero_shot(rgb_image, STYLE_LABELS)
    style = STYLE_MAP.get(best_style_raw, best_style_raw)

    if best_type in SEASON_OVERRIDE:
        season = SEASON_OVERRIDE[best_type]
        season_conf = 1.0  # Hardware override
    else:
        best_season_raw, season_conf, _ = _clip_zero_shot(rgb_image, SEASON_LABELS)
        season = SEASON_MAP.get(best_season_raw, best_season_raw)

    best_pattern_raw, pattern_conf, _ = _clip_zero_shot(rgb_image, PATTERN_LABELS)
    pattern = PATTERN_MAP.get(best_pattern_raw, best_pattern_raw)

    # ── Step 3: Dominant Color ────────────────────────────────────────────────
    rgb_np = np.array(rgb_image)
    color = _extract_dominant_color(rgb_np, alpha)

    # ── Step 4: Auto-generate tags ────────────────────────────────────────────
    tags = list({t for t in (category, best_type, style, season, pattern, color) if t})
    tags.sort()

    result = {
        "category":   category,
        "type":       best_type,
        "style":      style,
        "season":     season,
        "pattern":    pattern,
        "color":      color,
        "region":     region or "garment",
        "confidence": {
            "category": round(type_conf, 4),
            "type":     round(type_conf, 4),
            "style":    round(style_conf, 4),
            "season":   round(season_conf, 4),
            "pattern":  round(pattern_conf, 4),
        },
        "tags": tags,
    }

    return result


def classify_all_outputs(output_directory: str = "ml/outputs") -> list[dict]:
    """
    Classify all segmented PNGs in the output directory.
    Returns a list of classification results, each with the source file name.
    """
    output_dir = Path(output_directory)
    results = []

    for png_path in sorted(output_dir.glob("*.png")):
        if png_path.name.startswith(".") or png_path.name == ".gitkeep":
            continue

        print(f"\n{'─'*50}")
        print(f"Classifying: {png_path.name}")

        try:
            result = classify_item(str(png_path))
            result["file_name"] = png_path.name
            result["file_path"] = str(png_path)

            print(f"  Category : {result['category']}")
            print(f"  Type     : {result['type']}  (conf: {result['confidence']['type']:.2f})")
            print(f"  Style    : {result['style']}  (conf: {result['confidence']['style']:.2f})")
            print(f"  Season   : {result['season']}  (conf: {result['confidence']['season']:.2f})")
            print(f"  Pattern  : {result['pattern']}  (conf: {result['confidence']['pattern']:.2f})")
            print(f"  Color    : {result['color']}")
            print(f"  Tags     : {result['tags']}")

            results.append(result)
        except Exception as e:
            print(f"  ERROR: {e}")

    print(f"\n{'='*50}")
    print(f"Classified {len(results)} items.")
    return results


if __name__ == "__main__":
    results = classify_all_outputs()
    print("\n\nFull Results:")
    for r in results:
        pprint(r)