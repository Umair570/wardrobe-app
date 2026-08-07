"""
model.py — Global model loading for the Wardrobe Segmentation Pipeline.

Architecture: CLIPSeg + SAM2
  - CLIPSeg : Zero-shot semantic segmentation to locate each garment region
  - SAM2    : Pixel-perfect instance mask extraction from box prompts

Models are loaded lazily on first use so that importing this module (or the
FastAPI app) never blocks on a multi-GB download and never hard-fails when the
weights are not present yet.
"""

import os
import logging
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]

CLIPSEG_MODEL_NAME = os.getenv("CLIPSEG_MODEL_NAME", "CIDAS/clipseg-rd64-refined")
# ultralytics resolves a bare "sam2_t.pt" against its own weights cache and will
# auto-download it on first use. An explicit SAM2_MODEL_PATH overrides that.
SAM2_MODEL_PATH = os.getenv("SAM2_MODEL_PATH", str(REPO_ROOT / "sam2_t.pt"))

_clipseg = {"processor": None, "model": None}
_sam2 = {"model": None}


def get_clipseg():
    """Return (processor, model) for CLIPSeg, loading on first call."""
    if _clipseg["model"] is None:
        from transformers import CLIPSegProcessor, CLIPSegForImageSegmentation

        logger.info("[segmentation] Loading CLIPSeg (%s)...", CLIPSEG_MODEL_NAME)
        _clipseg["processor"] = CLIPSegProcessor.from_pretrained(CLIPSEG_MODEL_NAME)
        model = CLIPSegForImageSegmentation.from_pretrained(CLIPSEG_MODEL_NAME)
        model.eval()
        _clipseg["model"] = model
        logger.info("[segmentation] CLIPSeg loaded.")
    return _clipseg["processor"], _clipseg["model"]


def get_sam2():
    """Return the SAM2 model, loading (and auto-downloading weights) on first call."""
    if _sam2["model"] is None:
        from ultralytics import SAM

        # Prefer an explicit local checkpoint; otherwise let ultralytics fetch it.
        target = SAM2_MODEL_PATH if os.path.isfile(SAM2_MODEL_PATH) else "sam2_t.pt"
        logger.info("[segmentation] Loading SAM2 from %s...", target)
        _sam2["model"] = SAM(target)
        logger.info("[segmentation] SAM2 loaded.")
    return _sam2["model"]


def warm_up() -> None:
    """Eagerly load both models. Called by the API startup hook."""
    get_clipseg()
    get_sam2()
