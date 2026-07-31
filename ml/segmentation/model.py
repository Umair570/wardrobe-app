"""
model.py — Loads ML models for the Wardrobe Project.

Architecture: Pure Segmentation
  - Uses SAM2 (Segment Anything Model 2) AutoMaskGenerator
  - Automatically finds and segments EVERY object in the image without prompts.
  - Classification (labeling items as 'shirt' or 'pants') is handled downstream.
"""

from ultralytics import SAM

# ── SAM2 (via Ultralytics) ────────────────────────────────────────────────────
# sam2.1_s.pt = fast + small.  sam2.1_l.pt = best quality (larger).
print("Loading SAM2 model for pure segmentation...")
SAM2_MODEL = SAM("sam2.1_s.pt")
print("SAM2 loaded successfully.\n")