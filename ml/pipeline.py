"""
pipeline.py — Unified Orchestrator for Wardrobe ML
==================================================
This module serves as the single access point for the backend FastAPI endpoints.
It orchestrates segmentation (CLIPSeg + SAM2) and classification (FashionCLIP),
catching edge cases.
"""

import logging
import time
from pathlib import Path

import cv2

from ml.classification.inference import classify_item
from ml.segmentation.inference import process_image

logger = logging.getLogger(__name__)


def is_image_blurry(image_path: str, threshold: float = 50.0) -> bool:
    """
    Checks the variance of the Laplacian to identify completely out-of-focus images.
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return False
    variance = cv2.Laplacian(img, cv2.CV_64F).var()
    return variance < threshold


_ml_dir = Path(__file__).resolve().parent
_default_out = str(_ml_dir / ".outputs")


def process_wardrobe_upload(image_path: str, output_directory: str = _default_out) -> dict:
    """
    Unified entrypoint for backend API.

    Args:
        image_path: Absolute or relative path to the uploaded image.
        output_directory: Where to save the segmented transparent PNGs.

    Returns:
        dict: Final payload to be saved into the user's wardrobe database.
    """
    start_time = time.time()
    img_path_obj = Path(image_path)

    if not img_path_obj.exists():
        return {"success": False, "error": "Image file not found.", "code": "NOT_FOUND"}

    # 1. Edge Case Handling: Blur Detection
    if is_image_blurry(image_path, threshold=30.0):
        return {
            "success": False,
            "error": "The image is too blurry. Please upload a clear photo of the clothing.",
            "code": "BLURRY_IMAGE",
        }

    # 2. Run Segmentation (CLIPSeg + SAM2)
    try:
        seg_result = process_image(image_path, output_directory=output_directory)
    except Exception as e:
        logger.error("[pipeline] Segmentation failed for %s: %s", image_path, e, exc_info=True)
        return {"success": False, "error": f"Segmentation failed: {e}", "code": "SEG_ERROR"}

    if not seg_result.get("success") or seg_result.get("total_items", 0) == 0:
        return {
            "success": False,
            "error": "No clear clothing items were detected in the photo.",
            "code": "NO_CLOTHING",
        }

    # 3. Run Classification on each detected item, scoped to its body region
    final_items = []

    for item in seg_result["items"]:
        try:
            class_result = classify_item(item["path"], region=item.get("region"))

            final_items.append({
                "segmentation_file": item["file_name"],
                "segmentation_path": item["path"],
                "area_ratio":        item["area_ratio"],
                "bbox":              item.get("bbox"),
                "region":            item.get("region"),

                # Merging classification data
                "category":          class_result.get("category"),
                "type":              class_result.get("type"),
                "style":             class_result.get("style"),
                "season":            class_result.get("season"),
                "pattern":           class_result.get("pattern"),
                "color":             class_result.get("color"),
                "tags":              class_result.get("tags", []),
                "confidence_scores": class_result.get("confidence", {}),
            })
        except Exception as e:
            logger.warning("[pipeline] Failed to classify %s: %s", item["file_name"], e)
            continue

    if not final_items:
        return {
            "success": False,
            "error": "Failed to classify the detected clothing items.",
            "code": "CLASS_ERROR",
        }

    # 4. Compile Final Unified Response
    return {
        "success": True,
        "image_source": img_path_obj.name,
        "mode": seg_result.get("mode"),
        "total_items": len(final_items),
        "items": final_items,
        "processing_time_sec": round(time.time() - start_time, 3),
    }


if __name__ == "__main__":
    import json
    import sys

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    for target in sys.argv[1:] or [str(_ml_dir / "test_images" / "image 2.jpg")]:
        if Path(target).exists():
            print(json.dumps(process_wardrobe_upload(target), indent=2))
        else:
            print(f"Skipping missing file: {target}")
