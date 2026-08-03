"""
model.py — Global model loading for the Wardrobe Segmentation Pipeline.

Architecture: CLIPSeg + SAM2
  - CLIPSeg : Zero-shot semantic segmentation to find bounding boxes of items
  - SAM2    : Pixel-perfect instance mask extraction
"""

from transformers import CLIPSegProcessor, CLIPSegForImageSegmentation
from ultralytics import SAM

import os
import os
from dotenv import load_dotenv
load_dotenv()

print("Loading SAM2-Tiny for pixel-perfect mask extraction...")
default_sam2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sam2_t.pt")
sam2_path = os.getenv("SAM2_MODEL_PATH", default_sam2)
SAM2_MODEL = SAM(sam2_path)
print("SAM2 loaded.\n")

print("Loading CLIPSeg for semantic item location...")
clip_model_name = os.getenv("CLIPSEG_MODEL_NAME", "CIDAS/clipseg-rd64-refined")
CLIP_PROCESSOR = CLIPSegProcessor.from_pretrained(clip_model_name)
CLIP_MODEL     = CLIPSegForImageSegmentation.from_pretrained(clip_model_name)
CLIP_MODEL.eval()
print("CLIPSeg loaded.\n")