"""
model.py — Global model loading for the Wardrobe Segmentation Pipeline.

Architecture: rembg (U2Net) + CLIPSeg
  - rembg   : Removes background to produce a clean global silhouette
  - CLIPSeg : Zero-shot semantic segmentation to separate individual items
"""

from rembg import new_session
from transformers import CLIPSegProcessor, CLIPSegForImageSegmentation

print("Loading U2Net (rembg) for background removal...")
REMBG_SESSION = new_session("u2net")
print("U2Net loaded.\n")

print("Loading CLIPSeg for semantic item separation...")
CLIP_PROCESSOR = CLIPSegProcessor.from_pretrained("CIDAS/clipseg-rd64-refined")
CLIP_MODEL     = CLIPSegForImageSegmentation.from_pretrained("CIDAS/clipseg-rd64-refined")
CLIP_MODEL.eval()
print("CLIPSeg loaded.\n")