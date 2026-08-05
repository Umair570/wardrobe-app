"""
model.py — Global model loading for the Wardrobe Segmentation Pipeline.

Architecture: Bria RMBG-1.4
  - Flawless, pixel-perfect e-commerce background removal
  - Capable of isolating any garment with sharp edge alpha accuracy
"""
from transformers import pipeline

print("Loading Bria RMBG-1.4 for flawless e-commerce background removal...")
# trust_remote_code is required for RMBG-1.4, which executes optimized pytorch graph
SEG_PIPELINE = pipeline("image-segmentation", model="briaai/RMBG-1.4", trust_remote_code=True)
print("RMBG-1.4 loaded.\n")