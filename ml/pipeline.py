"""
pipeline.py — Unified Orchestrator for Wardrobe ML
==================================================
This module serves as the single access point for the backend FastAPI endpoints.
It orchestrates segmentation and classification, catching edge cases.
"""

import cv2
import time
from pathlib import Path

from ml.segmentation.inference import process_image
from ml.classification.inference import classify_item


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
            "code": "BLURRY_IMAGE"
        }

    # 2. Run Segmentation (SAM2 + CLIPSeg)
    try:
        seg_result = process_image(image_path, output_directory=output_directory)
    except Exception as e:
        return {"success": False, "error": f"Segmentation failed: {str(e)}", "code": "SEG_ERROR"}

    if not seg_result.get("success") or seg_result.get("total_items", 0) == 0:
        return {
            "success": False,
            "error": "No clear clothing items were detected in the photo.",
            "code": "NO_CLOTHING"
        }

    # 3. Run Classification on each detected item
    final_items = []
    
    for item in seg_result["items"]:
        try:
            class_result = classify_item(item["path"])
            
            final_items.append({
                "segmentation_file": item["file_name"],
                "segmentation_path": item["path"],
                "area_ratio": item["area_ratio"],
                
                # Merging classification data
                "category": class_result.get("category"),
                "type": class_result.get("type"),
                "style": class_result.get("style"),
                "season": class_result.get("season"),
                "pattern": class_result.get("pattern"),
                "color": class_result.get("color"),
                "tags": class_result.get("tags", []),
                "confidence_scores": class_result.get("confidence", {})
            })
        except Exception as e:
            print(f"Failed to classify {item['file_name']}: {str(e)}")
            continue

    if not final_items:
        return {
            "success": False,
            "error": "Failed to classify the detected clothing items.",
            "code": "CLASS_ERROR"
        }

    # 4. Compile Final Unified Response
    total_time = round(time.time() - start_time, 3)
    
    return {
        "success": True,
        "image_source": img_path_obj.name,
        "total_items": len(final_items),
        "items": final_items,
        "processing_time_sec": total_time
    }

if __name__ == "__main__":
    # Test script for the unifer
    import json
    test_img = "ml/test_images/image 2.jpg"
    if Path(test_img).exists():
        result = process_wardrobe_upload(test_img)
        print(json.dumps(result, indent=2))
