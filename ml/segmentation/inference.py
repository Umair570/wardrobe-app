"""
inference.py — Pure SAM2 Automatic Segmentation Pipeline

Objective: 
Take an input image, automatically detect all foreground objects, 
and extract them as isolated transparent PNGs.

Logic:
1. Run SAM2 Auto-Segment.
2. Filter out masks that are too small or touch too much of the image border (backgrounds).
3. Deduplicate using Mask IoA (Intersection over Area) so fully enclosed 
   sub-components (like pockets) are removed.
4. Composite and save generic PNGs (item_0.png, item_1.png).
"""

from pathlib import Path
import time
from PIL import Image
from pprint import pprint
import numpy as np
import cv2

from ml.segmentation.model import SAM2_MODEL
from ml.segmentation.utils import load_image, create_output_directory

OUTPUT_DIRECTORY = "ml/outputs"

# Size filters (fraction of total image area)
MIN_ITEM_AREA_RATIO = 0.005  # Drops tiny speckles
MAX_ITEM_AREA_RATIO = 0.98   # Drops entire-image masks

def _compute_mask_ioa(mask_a: np.ndarray, mask_b: np.ndarray) -> float:
    """
    Intersection over Area using boolean masks.
    Returns what fraction of mask_a is completely inside mask_b.
    """
    intersection = np.logical_and(mask_a, mask_b).sum()
    area_a = mask_a.sum()
    return intersection / area_a if area_a > 0 else 0.0

def process_image(image_path: str, output_directory: str = OUTPUT_DIRECTORY):
    start_time = time.time()
    create_output_directory(output_directory)

    image     = load_image(image_path)
    img_w, img_h = image.size
    img_area  = img_w * img_h
    image_np  = np.array(image)  # H×W×3 RGB

    print(f"\n{'='*60}")
    print(f"Segmenting : {Path(image_path).name}")
    print(f"Image size : {img_w} × {img_h}")

    result = {
        "success":         True,
        "image_name":      Path(image_path).name,
        "image_path":      image_path,
        "processing_time": None,
        "items":           []
    }
    image_stem = Path(image_path).stem

    # ── Step 1: SAM2 automatic segmentation ──────────────────────────────────
    try:
        sam_results = SAM2_MODEL.predict(source=image_np, verbose=False)
        sam_result = sam_results[0]

        if sam_result.masks is None or len(sam_result.masks) == 0:
            print("SAM2 found no masks.")
            result.update({"success": False, "error": "SAM2 found no segments"})
            return result

        masks_data = sam_result.masks.data.cpu().numpy().astype(bool)
        print(f"SAM2 generated {len(masks_data)} raw segments.")
    except Exception as exc:
        print(f"SAM2 failed: {exc}")
        result.update({"success": False, "error": str(exc)})
        return result

    # ── Step 2: Filter by size and discard backgrounds ────────────────────────
    valid_masks = []
    
    for mask in masks_data:
        area  = int(mask.sum())
        ratio = area / img_area
        if not (MIN_ITEM_AREA_RATIO <= ratio <= MAX_ITEM_AREA_RATIO):
            continue
            
        # Is this a background mask? Check boundary pixels
        top_border = mask[0, :]
        bot_border = mask[-1, :]
        lft_border = mask[:, 0]
        rgt_border = mask[:, -1]
        
        border_pixels = len(top_border) + len(bot_border) + len(lft_border) + len(rgt_border)
        border_hits   = top_border.sum() + bot_border.sum() + lft_border.sum() + rgt_border.sum()
        
        # If >60% of the image border pixels belong to this mask, it's a background
        if (border_hits / border_pixels) > 0.60:
            continue
            
        valid_masks.append(mask)

    # ── Step 3: Deduplicate — remove fully enclosed parts (pockets, tags) ─────
    # Sort by mask area (largest first)
    valid_masks.sort(key=lambda m: m.sum(), reverse=True)
    kept_masks = []
    
    for mask in valid_masks:
        is_enclosed = False
        for kept in kept_masks:
            ioa = _compute_mask_ioa(mask, kept)
            if ioa > 0.85:  # If mask is 85%+ contained inside a larger kept mask
                is_enclosed = True
                break
                
        if not is_enclosed:
            kept_masks.append(mask)

    print(f"Retained {len(kept_masks)} unique items after filtering.")

    # ── Step 4: Composite mask onto RGBA and save ─────────────────────────────
    if not kept_masks:
        result.update({"success": False, "error": "No items found after filtering"})
        return result

    image_rgba = np.array(image.convert("RGBA"))

    for i, mask in enumerate(kept_masks):
        # Bounding box from mask to crop
        rows = np.where(mask.any(axis=1))[0]
        cols = np.where(mask.any(axis=0))[0]
        if len(rows) == 0 or len(cols) == 0:
            continue
        y1, y2 = int(rows.min()), int(rows.max())
        x1, x2 = int(cols.min()), int(cols.max())

        # Apply mask as alpha — pixels outside mask are fully transparent
        composited = image_rgba.copy()
        alpha = (mask.astype(np.uint8) * 255)

        # Smooth the alpha edge to remove jagged pixels
        alpha = cv2.GaussianBlur(alpha, (5, 5), 0)
        _, alpha = cv2.threshold(alpha, 127, 255, cv2.THRESH_BINARY)
        composited[:, :, 3] = alpha

        # Crop to item
        item_crop = composited[y1:y2, x1:x2]

        # Trim pure padding
        alpha_ch = item_crop[:, :, 3]
        cx, cy, cw, ch = cv2.boundingRect(alpha_ch)
        if cw <= 0 or ch <= 0:
            continue

        tp  = 4
        tx1 = max(0, cx - tp)
        ty1 = max(0, cy - tp)
        tx2 = min(item_crop.shape[1], cx + cw + tp)
        ty2 = min(item_crop.shape[0], cy + ch + tp)

        final_item = Image.fromarray(item_crop[ty1:ty2, tx1:tx2])

        filename  = f"{image_stem}_item_{i}.png"
        save_path = Path(output_directory) / filename
        final_item.save(save_path)

        result["items"].append({
            "file_name": filename,
            "path":      str(save_path),
        })

    result["processing_time"] = round(time.time() - start_time, 3)
    result["total_items"]     = len(result["items"])

    print(f"Extracted {result['total_items']} items in {result['processing_time']}s")
    for item in result["items"]:
        print(f"  → {item['file_name']}")

    return result


if __name__ == "__main__":
    test_folder      = Path("ml/test_images")
    image_extensions = {".jpg", ".jpeg", ".png"}

    for image_path in sorted(test_folder.iterdir()):
        if image_path.suffix.lower() in image_extensions:
            result = process_image(str(image_path))
            pprint(result)