"""
inference.py — Production-Grade Wardrobe Segmentation Pipeline
==============================================================

Architecture:
  Step 1  rembg (U2Net)  → Remove background, get perfect global silhouette
  Step 2  CLIPSeg        → Semantic heatmaps for each garment class
  Step 3  Argmax + Seal  → Divide foreground pixels between garment classes
  Step 4  Crop & Save    → Transparent PNG per garment item

This hybrid approach is optimal because:
  - rembg perfectly separates foreground from background (no color bias)
  - CLIPSeg divides the foreground into semantic items (shirt vs pants)
  - The intersection ensures we never include background pixels in any item
"""

import torch
import multiprocessing

num_cores = multiprocessing.cpu_count()
torch.set_num_threads(num_cores)
torch.set_grad_enabled(False)

import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from rembg import remove, new_session
import time
from pprint import pprint

from ml.segmentation.model import CLIP_PROCESSOR, CLIP_MODEL
from ml.segmentation.utils import load_image, create_output_directory

OUTPUT_DIRECTORY = "ml/outputs"

# ── TUNING CONSTANTS ──────────────────────────────────────────────────────────
MAX_DIM             = 640    # Max working resolution (speed vs quality)
CLIPSEG_THRESHOLD   = 0.30   # Min peak confidence to accept a semantic class
MIN_ITEM_AREA_RATIO = 0.005  # Drop masks smaller than 0.5% of image
MAX_ITEM_AREA_RATIO = 0.97   # Drop masks covering almost the entire image
GAUSSIAN_BLUR_SIZE  = 31     # Smooth CLIPSeg boundary seams (must be odd int)
MORPH_CLOSE_SIZE    = 25     # Bridge small contour gaps (e.g. color-contrast tags)
PADDING             = 6      # Extra padding around each cropped item

# Load rembg session once at module level for speed (avoids reloading per call)
_REMBG_SESSION = new_session("u2net")


def _extract_global_alpha(image: Image.Image) -> np.ndarray:
    """
    Use rembg (U2Net) to get a clean binary foreground mask.
    Returns uint8 array of shape (H, W) with values 0 or 255.
    """
    result = remove(image, session=_REMBG_SESSION, alpha_matting=False)
    alpha = np.array(result)[:, :, 3]

    # Smooth edges slightly and re-binarize
    blurred = cv2.GaussianBlur(alpha, (5, 5), 0)
    _, binary = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY)

    h, w = binary.shape

    # STEP 1: Morphological close — scale-relative kernel bridges exterior notches
    # (e.g. tan leather tag creating a U-shaped gap at the top of blue jeans).
    # Kernel sized to ~5% of the smaller image dimension so it adapts to any resolution.
    close_radius = max(30, int(min(h, w) * 0.05))
    close_radius += (close_radius % 2 == 0)   # ensure odd for symmetry
    bridge_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_radius * 2 + 1, close_radius * 2 + 1))
    bridged = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, bridge_kernel)

    # STEP 2: Flood-fill from corner — definitively marks the exterior background.
    # Pad by 1 pixel so the fill seed reaches all image edges.
    padded = cv2.copyMakeBorder(bridged, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=0)
    flood_fill_mask = np.zeros((padded.shape[0] + 2, padded.shape[1] + 2), dtype=np.uint8)
    cv2.floodFill(padded, flood_fill_mask, (0, 0), 255)

    # After flood-fill, pixels that are white are BACKGROUND. Invert to get foreground.
    exterior = padded[1:-1, 1:-1]   # remove the temporary 1px border
    filled = cv2.bitwise_not(exterior)

    # Combine: foreground from bridged OR foreground from fill inversion
    filled = cv2.bitwise_or(bridged, filled)

    # STEP 3: Final contour fill to clean up any remaining small interior holes
    contours, _ = cv2.findContours(filled, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    final = np.zeros_like(filled)
    cv2.drawContours(final, contours, -1, 255, cv2.FILLED)
    return final


def _get_clipseg_masks(image: Image.Image, prompts: list, img_w: int, img_h: int):
    """
    Run CLIPSeg and return (valid_indices, valid_probs as np array).
    valid_probs has shape (N, img_h, img_w).
    """
    inputs = CLIP_PROCESSOR(
        text=prompts,
        images=[image] * len(prompts),
        padding="max_length",
        return_tensors="pt",
    )

    with torch.no_grad():
        outputs = CLIP_MODEL(**inputs)

    logits = outputs.logits                            # (N, H_clip, W_clip)
    probs  = torch.sigmoid(logits).detach().cpu().numpy()

    valid_indices = []
    valid_probs   = []

    for i, prompt in enumerate(prompts):
        resized = cv2.resize(probs[i], (img_w, img_h))
        peak    = float(np.percentile(resized, 99.5))
        if peak >= CLIPSEG_THRESHOLD:
            valid_indices.append(i)
            valid_probs.append(resized)

    return valid_indices, (np.array(valid_probs) if valid_probs else None)


def process_image(image_path: str, output_directory: str = OUTPUT_DIRECTORY) -> dict:
    start_time = time.time()
    create_output_directory(output_directory)

    # ── Load & resize ─────────────────────────────────────────────────────────
    image    = load_image(image_path)  # PIL RGB
    img_w, img_h = image.size

    if max(img_w, img_h) > MAX_DIM:
        scale  = MAX_DIM / max(img_w, img_h)
        img_w  = int(img_w * scale)
        img_h  = int(img_h * scale)
        image  = image.resize((img_w, img_h), Image.Resampling.LANCZOS)

    img_area   = img_w * img_h
    image_np   = np.array(image)    # uint8 RGB (H, W, 3) — kept pristine for compositing

    print(f"\n{'='*60}")
    print(f"Segmenting : {Path(image_path).name}")
    print(f"Processing size : {img_w} × {img_h}")

    result = {
        "success":         True,
        "image_name":      Path(image_path).name,
        "image_path":      image_path,
        "processing_time": None,
        "items":           [],
    }
    image_stem = Path(image_path).stem

    # ── Step 1: rembg — global foreground silhouette ───────────────────────────
    global_alpha = _extract_global_alpha(image)   # uint8 (H, W)

    # ── Step 2: CLIPSeg — semantic class detection ────────────────────────────
    prompts = [
        "top clothing or shirt",
        "pants or bottom clothing",
        "shoes or footwear",
        "bag or purse",
    ]

    valid_indices, valid_probs = _get_clipseg_masks(image, prompts, img_w, img_h)

    for i, prompt in enumerate(prompts):
        if i in valid_indices:
            idx = valid_indices.index(i)
            peak = float(np.percentile(valid_probs[idx], 99.5))
            print(f"[{image_stem}] Peak confidence for '{prompt}': {peak:.3f}  ✓")
        else:
            print(f"[{image_stem}] Peak confidence for '{prompt}': skip")

    if valid_probs is None:
        print(f"[{image_stem}] No confident classes — saving whole foreground")
        # Fallback: save the full U2Net foreground as a single item
        rgba = np.dstack([image_np, global_alpha])
        cx, cy, cw, ch = cv2.boundingRect(global_alpha)
        if cw > 0 and ch > 0:
            x1, y1 = max(0, cx - PADDING), max(0, cy - PADDING)
            x2, y2 = min(img_w, cx + cw + PADDING), min(img_h, cy + ch + PADDING)
            crop = rgba[y1:y2, x1:x2]
            out  = Image.fromarray(crop, mode="RGBA")
            fn   = f"{image_stem}_item_0.png"
            out.save(Path(output_directory) / fn)
            result["items"] = [{"file_name": fn, "path": str(Path(output_directory) / fn), "label": "item"}]
        result["processing_time"] = round(time.time() - start_time, 3)
        result["total_items"] = len(result["items"])
        return result

    # ── Step 3: Argmax — divide foreground between detected classes ────────────
    # Argmax ensures every foreground pixel belongs to exactly one garment class
    argmax_map = np.argmax(valid_probs, axis=0)   # (H, W), values = local index

    kept_items = []

    for local_i, global_i in enumerate(valid_indices):
        prompt = prompts[global_i]

        # Raw semantic mask for this class
        semantic_raw = (argmax_map == local_i).astype(np.uint8) * 255

        # Smooth the CLIPSeg seams for organic garment boundaries
        blurred = cv2.GaussianBlur(semantic_raw, (GAUSSIAN_BLUR_SIZE, GAUSSIAN_BLUR_SIZE), 0)
        _, semantic_hard = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY)

        # Intersection with global silhouette: NEVER include background
        # This is the key step — CLIPSeg can bleed into background, rembg prevents this
        item_mask = cv2.bitwise_and(global_alpha, semantic_hard)

        # Bridge gaps from contrasting features (dark tags on light fabric, etc.)
        kernel    = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (MORPH_CLOSE_SIZE, MORPH_CLOSE_SIZE))
        item_mask = cv2.morphologyEx(item_mask, cv2.MORPH_CLOSE, kernel)

        # Re-seal inner holes after closing
        contours, _ = cv2.findContours(item_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        sealed = np.zeros_like(item_mask)
        cv2.drawContours(sealed, contours, -1, 255, cv2.FILLED)
        item_mask = sealed

        # ── Quality gate ──────────────────────────────────────────────────────
        area  = int(np.count_nonzero(item_mask))
        ratio = area / img_area

        if not (MIN_ITEM_AREA_RATIO <= ratio <= MAX_ITEM_AREA_RATIO):
            print(f"[{image_stem}] '{prompt}' area ratio {ratio:.4f} out of range — skipping")
            continue

        # ── Compose RGBA ──────────────────────────────────────────────────────
        # Use np.dstack to cleanly attach the alpha channel to original RGB
        rgba = np.dstack([image_np, item_mask])

        # Tight crop with padding
        cx_f, cy_f, cw_f, ch_f = cv2.boundingRect(item_mask)
        x1 = max(0, cx_f - PADDING)
        y1 = max(0, cy_f - PADDING)
        x2 = min(img_w, cx_f + cw_f + PADDING)
        y2 = min(img_h, cy_f + ch_f + PADDING)

        crop = rgba[y1:y2, x1:x2]
        if crop.shape[0] < 2 or crop.shape[1] < 2:
            continue

        # ── Save ─────────────────────────────────────────────────────────────
        out_img  = Image.fromarray(crop, mode="RGBA")
        filename = f"{image_stem}_item_{len(kept_items)}.png"
        save_path = Path(output_directory) / filename
        out_img.save(save_path)

        kept_items.append({
            "file_name":  filename,
            "path":       str(save_path),
            "label":      prompt,
            "area_ratio": round(ratio, 4),
        })

    result["items"]           = kept_items
    result["processing_time"] = round(time.time() - start_time, 3)
    result["total_items"]     = len(kept_items)

    print(f"Extracted {result['total_items']} items in {result['processing_time']}s")
    for item in result["items"]:
        print(f"  → {item['file_name']}  ({item['label']})")

    return result


if __name__ == "__main__":
    test_folder      = Path("ml/test_images")
    image_extensions = {".jpg", ".jpeg", ".png", ".webp"}

    for image_path in sorted(test_folder.iterdir()):
        if image_path.suffix.lower() in image_extensions and not image_path.name.startswith("."):
            result = process_image(str(image_path))
            pprint(result)