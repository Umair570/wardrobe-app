"""
inference.py — Production-Grade Wardrobe Segmentation Pipeline
==============================================================

Architecture:
  Step 1  Bria RMBG-1.4 → Extract pristine pristine soft alpha masks of all foreground clothing items
  Step 2  Connected Components → Identify separate disconnected garments internally
  Step 3  Crop & Export → Produce transparent PNGs ready for classification
"""

import cv2
import numpy as np
from PIL import Image
from pathlib import Path
import time
import torch

from ml.segmentation.model import SEG_PIPELINE
from ml.segmentation.utils import load_image, create_output_directory

_ml_dir = Path(__file__).resolve().parent.parent
OUTPUT_DIRECTORY = str(_ml_dir / ".outputs")

# ── TUNING CONSTANTS ──────────────────────────────────────────────────────────
MAX_DIM             = 1024   # Use high res for perfect fabric edges
MIN_ITEM_AREA_RATIO = 0.04   # Ignore dust, specks, tags or tiny artifacts
MAX_ITEM_AREA_RATIO = 0.99 
PADDING             = 15     # Keep generous padding

def process_image(image_path: str, output_directory: str = OUTPUT_DIRECTORY) -> dict:
    start_time = time.time()
    create_output_directory(output_directory)

    # ── Load ──────────────────────────────────────────────────────────────────
    image = load_image(image_path)  # PIL RGB
    orig_w, orig_h = image.size
    
    if max(orig_w, orig_h) > MAX_DIM:
        scale = MAX_DIM / max(orig_w, orig_h)
        work_w = int(orig_w * scale)
        work_h = int(orig_h * scale)
        image = image.resize((work_w, work_h), Image.Resampling.LANCZOS)
    else:
        work_w, work_h = orig_w, orig_h
        
    img_area = work_w * work_h
    image_np = np.array(image)

    print(f"\n{'='*60}")
    print(f"Segmenting (RMBG): {Path(image_path).name}")

    result = {
        "success":         True,
        "image_name":      Path(image_path).name,
        "image_path":      image_path,
        "processing_time": None,
        "items":           [],
    }
    image_stem = Path(image_path).stem

    # ── Step 1: Bria RMBG-1.4 Alpha Extraction ────────────────────────────────
    try:
        pipeline_out = SEG_PIPELINE(image)
        
        # RMBG can return a list or a direct PIL image
        if isinstance(pipeline_out, list):
            mask_img = pipeline_out[0].get("mask", pipeline_out[0].get("image"))
        else:
            mask_img = pipeline_out
            
        if mask_img.mode == "RGBA":
            # Extract alpha channel
            alpha_mask = np.array(mask_img)[:, :, 3]
        else:
            # Grayscale mask
            alpha_mask = np.array(mask_img.convert("L"))
            
    except Exception as e:
        print(f"RMBG execution failed: {e}")
        return {"success": False, "error": str(e), "total_items": 0}

    # Remove floating semi-transparent noise pixels
    _, binary_mask = cv2.threshold(alpha_mask, 150, 255, cv2.THRESH_BINARY)
    
    # Optional morphological closing to bridge tiny gaps inside a garment
    kernel = np.ones((5, 5), np.uint8)
    binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel)

    # ── Step 2: Component Separation ──────────────────────────────────────────
    kept_items = []
    
    # Isolate separately laid out garments (connected components)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary_mask, connectivity=8)
    
    for i in range(1, num_labels):  # Skip background (0)
        area = stats[i, cv2.CC_STAT_AREA]
        ratio = area / img_area
        
        # Ignore artifacts that are too small or too huge bounding box
        if not (MIN_ITEM_AREA_RATIO <= ratio <= MAX_ITEM_AREA_RATIO):
            continue
            
        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]
        
        # Instance mask filters out other disconnected garments
        instance_binary = (labels == i).astype(np.uint8)
        
        # We retain the original soft alpha map for this instance for gorgeous edges
        smooth_instance_mask = cv2.bitwise_and(alpha_mask, alpha_mask, mask=instance_binary)
        
        # ── Step 3: Crop & Export ─────────────────────────────────────────────
        rgba = np.dstack([image_np, smooth_instance_mask])
        
        x1 = max(0, x - PADDING)
        y1 = max(0, y - PADDING)
        x2 = min(work_w, x + w + PADDING)
        y2 = min(work_h, y + h + PADDING)
        
        crop = rgba[y1:y2, x1:x2]
        if crop.shape[0] < 5 or crop.shape[1] < 5:
            continue
            
        out_img  = Image.fromarray(crop, mode="RGBA")
        filename = f"{image_stem}_item_{len(kept_items)}.png"
        save_path = Path(output_directory) / filename
        out_img.save(save_path)
        
        kept_items.append({
            "file_name":  filename,
            "path":       str(save_path),
            "label":      "extracted_foreground",
            "area_ratio": round(ratio, 4),
        })

    result["items"]           = kept_items
    result["processing_time"] = round(time.time() - start_time, 3)
    result["total_items"]     = len(kept_items)

    print(f"Extracted {result['total_items']} items in {result['processing_time']}s")
    for item in result["items"]:
        print(f"  → {item['file_name']}")

    return result

if __name__ == "__main__":
    test_folder = Path("ml/test_images")
    image_extensions = {".jpg", ".jpeg", ".png", ".webp"}

    for image_path in sorted(test_folder.iterdir()):
        if image_path.suffix.lower() in image_extensions and not image_path.name.startswith("."):
            from pprint import pprint
            result = process_image(str(image_path))
            pprint(result)