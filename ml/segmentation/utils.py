from pathlib import Path
from PIL import Image

def create_output_directory(output_directory: str):
    Path(output_directory).mkdir(parents=True, exist_ok=True)

def load_image(image_path: str):
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    return Image.open(image_path).convert("RGB")

def compute_iou(box_a, box_b):
    ax_min, ay_min, ax_max, ay_max = box_a
    bx_min, by_min, bx_max, by_max = box_b

    inter_x_min = max(ax_min, bx_min)
    inter_y_min = max(ay_min, by_min)
    inter_x_max = min(ax_max, bx_max)
    inter_y_max = min(ay_max, by_max)

    inter_width  = max(0, inter_x_max - inter_x_min)
    inter_height = max(0, inter_y_max - inter_y_min)
    intersection = inter_width * inter_height

    area_a = max(0, ax_max - ax_min) * max(0, ay_max - ay_min)
    area_b = max(0, bx_max - bx_min) * max(0, by_max - by_min)
    union = area_a + area_b - intersection

    if union == 0:
        return 0.0
    return intersection / union

def deduplicate_detections(detections, iou_threshold: float = 0.45):
    """
    Keep only the highest-confidence detection when two boxes overlap > iou_threshold.
    Lowered from 0.5 to 0.45 so partial overlaps (trousers/jeans) are merged more eagerly.
    """
    sorted_detections = sorted(detections, key=lambda d: d["confidence"], reverse=True)
    kept = []
    for candidate in sorted_detections:
        is_duplicate = False
        for kept_det in kept:
            if compute_iou(candidate["box"], kept_det["box"]) > iou_threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            kept.append(candidate)
    return kept