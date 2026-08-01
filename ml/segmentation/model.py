"""
model.py — Global model loading for the Wardrobe Segmentation Pipeline.

Architecture: CLIPSeg + SAM2
  - CLIPSeg : Zero-shot semantic segmentation to find bounding boxes of items
  - SAM2    : Pixel-perfect instance mask extraction
"""

from transformers import CLIPSegProcessor, CLIPSegForImageSegmentation
from ultralytics import SAM

print("Loading SAM2-Tiny for pixel-perfect mask extraction...")
SAM2_MODEL = SAM("sam2_t.pt")
print("SAM2 loaded.\n")

print("Loading CLIPSeg for semantic item location...")
CLIP_PROCESSOR = CLIPSegProcessor.from_pretrained("CIDAS/clipseg-rd64-refined")
CLIP_MODEL     = CLIPSegForImageSegmentation.from_pretrained("CIDAS/clipseg-rd64-refined")
CLIP_MODEL.eval()
print("CLIPSeg loaded.\n")