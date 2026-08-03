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
)


def _load_rgba_image(image_path: str) -> tuple[Image.Image, np.ndarray]:
    """
    Load a transparent PNG. Returns (PIL Image in RGB, alpha mask as uint8 ndarray).
    If the image has no alpha channel, assumes fully opaque.
    """
    img = Image.open(image_path).convert("RGBA")
    arr = np.array(img)
    alpha = arr[:, :, 3]
    rgb = img.convert("RGB")
    return rgb, alpha


def _clip_zero_shot(image: Image.Image, candidate_labels: list[str]) -> tuple[str, float, dict]:
    """
    Run CLIP zero-shot classification on an image against candidate labels.
    Returns (best_label, best_score, all_scores_dict).
    """
    inputs = CLIP_CLASSIFIER_PROCESSOR(
        text=candidate_labels,
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
      1. KMeans cluster the foreground pixels into n groups
      2. Pick the cluster with the HIGHEST saturation (most chromatic/vibrant)
         → This prevents washed-out denim from averaging to "gray"
      3. For genuinely achromatic items (black/white/gray), fall back to the largest cluster
      4. Map the winning cluster center to the nearest named color
    """
    # Get only foreground pixels (alpha > 200 to prevent background bleed)
    fg_mask = alpha > 200
    fg_pixels = image_np_rgb[fg_mask]

    if len(fg_pixels) < 10:
        return "unknown"

    # Subsample for speed (max 8000 pixels for better accuracy)
    if len(fg_pixels) > 8000:
        indices = np.random.choice(len(fg_pixels), 8000, replace=False)
        fg_pixels = fg_pixels[indices]

    # KMeans to find dominant color clusters
    fg_float = fg_pixels.astype(np.float32)
    actual_clusters = min(n_clusters, len(fg_pixels))
    kmeans = KMeans(n_clusters=actual_clusters, n_init=5, random_state=42)
    kmeans.fit(fg_float)

    centers = kmeans.cluster_centers_          # (n_clusters, 3) in RGB
    counts  = np.bincount(kmeans.labels_)      # pixel count per cluster

    # Convert cluster centers to HSV to measure saturation
    centers_uint8 = np.clip(centers, 0, 255).astype(np.uint8).reshape(1, -1, 3)
    centers_hsv   = cv2.cvtColor(centers_uint8, cv2.COLOR_RGB2HSV).reshape(-1, 3)
    
    # Saturation values (0-255 scale in OpenCV HSV)
    saturations = centers_hsv[:, 1].astype(np.float32)

    # Decide strategy: if ANY cluster has decent saturation (>30), pick the most saturated
    # Otherwise the item is genuinely achromatic — pick the largest cluster
    SATURATION_THRESHOLD = 30

    if np.max(saturations) > SATURATION_THRESHOLD:
        # Force the algorithm to prioritize large clusters to avoid bright noise pixels winning
        # Normalize count to a percentage (0 to 1) so it scales with saturation
        volume_ratio = counts.astype(np.float32) / np.sum(counts)
        scores = saturations * volume_ratio
        best_idx = int(np.argmax(scores))
    else:
        # Achromatic item (black/white/gray) — just pick the biggest cluster
        best_idx = int(np.argmax(counts))

    dominant_rgb = centers[best_idx]
    return _nearest_color_name(dominant_rgb)


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
        
        # Euclidean distance in LAB space (deltaE CIE76)
        dist = np.sqrt(np.sum((lab_pixel.astype(np.float32) - ref_lab.astype(np.float32)) ** 2))
        
        if dist < min_dist:
            min_dist = dist
            best_name = name

    return best_name


def classify_item(image_path: str) -> dict:
    """
    Classify a single segmented clothing item.

    Args:
        image_path: Path to a transparent PNG from the segmentation pipeline.

    Returns:
        Dictionary with keys: category, type, style, color, confidence, tags
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    # ── Load image ────────────────────────────────────────────────────────────
    rgb_image, alpha = _load_rgba_image(image_path)

    # ── Step 1: Category + Type (one CLIP call) ──────────────────────────────
    # CLIP classifies against all granular labels at once
    # The best match gives us both the specific type AND the broad category via CATEGORY_MAP
    best_type, type_conf, all_type_scores = _clip_zero_shot(rgb_image, CATEGORY_LABELS)

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
    tags = list(set([
        category,
        best_type,
        style,
        season,
        pattern,
        color,
    ]))
    tags.sort()

    result = {
        "category":   category,
        "type":       best_type,
        "style":      style,
        "season":     season,
        "pattern":    pattern,
        "color":      color,
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