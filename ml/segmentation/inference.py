"""
inference.py — Production-Grade Wardrobe Segmentation Pipeline
==============================================================

Architecture:
  Step 1  CLIPSeg → Semantic heatmaps for each garment class
  Step 2  Argmax  → Divide foreground to find unique class blobs
  Step 3  SAM2    → Fast pixel-perfect segmentation from bounding box prompts
  Step 4  Crop    → Transparent PNG per garment item
"""

import torch
import cv2
import numpy as np
from PIL import Image
from pathlib import Path
import time
from pprint import pprint

from ml.segmentation.model import CLIP_PROCESSOR, CLIP_MODEL, SAM2_MODEL
from ml.segmentation.utils import load_image, create_output_directory

OUTPUT_DIRECTORY = "ml/outputs"

# ── TUNING CONSTANTS ──────────────────────────────────────────────────────────
MAX_DIM             = 640    # Max working resolution (speed vs quality)
CLIPSEG_THRESHOLD   = 0.30   # Min peak confidence to accept a semantic class
MIN_ITEM_AREA_RATIO = 0.005  # Drop masks smaller than 0.5% of image
MAX_ITEM_AREA_RATIO = 0.97   # Drop masks covering almost the entire image
PADDING             = 6      # Extra padding around each cropped item


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
    image_np   = np.array(image)    # uint8 RGB (H, W, 3)

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

    # ── Step 1: CLIPSeg — semantic class detection ────────────────────────────
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
        print(f"[{image_stem}] No confident classes found.")
        result["processing_time"] = round(time.time() - start_time, 3)
        result["total_items"] = 0
        return result

    # ── Step 2: Argmax to Box ─────────────────────────────────────────────────
    # Argmax ensures every pixel belongs to exactly one garment class (no box overlapping)
    argmax_map = np.argmax(valid_probs, axis=0)   # (H, W)
    
    boxes = []
    box_prompts = []
    
    for local_i, global_i in enumerate(valid_indices):
        prompt = prompts[global_i]
        semantic_raw = (argmax_map == local_i).astype(np.uint8) * 255
        
        # Threshold to remove weak tail probabilities
        mask_prob = valid_probs[local_i] > 0.1
        semantic_raw = cv2.bitwise_and(semantic_raw, semantic_raw, mask=mask_prob.astype(np.uint8))
        
        # Filter tiny semantic noise islands
        contours, _ = cv2.findContours(semantic_raw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            continue
            
        largest_contour = max(contours, key=cv2.contourArea)
        cx, cy, cw, ch = cv2.boundingRect(largest_contour)
        
        if cw > 5 and ch > 5:
            # Format SAM2 expects: [x1, y1, x2, y2]
            boxes.append([cx, cy, cx + cw, cy + ch])
            box_prompts.append(prompt)

    if not boxes:
        print(f"[{image_stem}] Bounding box generation failed.")
        result["processing_time"] = round(time.time() - start_time, 3)
        result["total_items"] = 0
        return result

    # ── Step 3: SAM2 Pixel-Perfect Extraction ─────────────────────────────────
    sam_results = SAM2_MODEL(image_np, bboxes=boxes, verbose=False)
    
    if len(sam_results) == 0 or sam_results[0].masks is None:
        print(f"[{image_stem}] SAM2 failed to generate masks.")
        result["processing_time"] = round(time.time() - start_time, 3)
        result["total_items"] = 0
        return result
        
    sam_masks_tensor = sam_results[0].masks.data
    # Convert tensor (N, H, W) to list of uint8 numpy arrays
    sam_masks = [cv2.resize((m.cpu().numpy() * 255).astype(np.uint8), (img_w, img_h)) for m in sam_masks_tensor]

    # ── Step 4: Crop & Save ───────────────────────────────────────────────────
    kept_items = []
    
    for idx, item_mask in enumerate(sam_masks):
        prompt = box_prompts[idx]
        
        area  = int(np.count_nonzero(item_mask))
        ratio = area / img_area

        if not (MIN_ITEM_AREA_RATIO <= ratio <= MAX_ITEM_AREA_RATIO):
            print(f"[{image_stem}] '{prompt}' area ratio {ratio:.4f} out of range — skipping")
            continue

        rgba = np.dstack([image_np, item_mask])

        cx_f, cy_f, cw_f, ch_f = cv2.boundingRect(item_mask)
        x1 = max(0, cx_f - PADDING)
        y1 = max(0, cy_f - PADDING)
        x2 = min(img_w, cx_f + cw_f + PADDING)
        y2 = min(img_h, cy_f + ch_f + PADDING)

        crop = rgba[y1:y2, x1:x2]
        if crop.shape[0] < 2 or crop.shape[1] < 2:
            continue

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