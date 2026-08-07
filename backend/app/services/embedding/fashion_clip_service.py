"""
Phase 6 – FashionCLIP Embedding Service.

Model card:  patrickjohncyh/fashion-clip
License:     MIT
Dim:         512
HF Hub:      https://huggingface.co/patrickjohncyh/fashion-clip

FashionCLIP is CLIP fine-tuned on 700K+ fashion product images with
rich attribute captions (color, type, material, style, season).
Expected to outperform generic CLIP for garment retrieval tasks.

Install:     pip install transformers torch pillow
Download:    ~600 MB on first use (auto-cached by HuggingFace)
"""

import logging
from typing import List

from PIL import Image
from app.services.embedding.base import BaseEmbeddingService

logger = logging.getLogger(__name__)

try:
    from transformers import CLIPProcessor, CLIPModel
    import torch
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    _TRANSFORMERS_AVAILABLE = False
    logger.warning("[FashionCLIPService] transformers/torch not installed. FashionCLIPService will be unavailable.")


class FashionCLIPService(BaseEmbeddingService):
    """
    FashionCLIP – CLIP fine-tuned on fashion product images.
    Best choice for garment attribute retrieval in this platform.
    """

    MODEL_NAME:              str  = "fashion-clip"
    MODEL_ID:                str  = "patrickjohncyh/fashion-clip"
    EMBEDDING_DIM:           int  = 512
    LICENSE:                 str  = "MIT"
    LOCAL_INFERENCE:         bool = True
    INTEGRATION_COMPLEXITY:  str  = "Low"
    EXTERNAL_DEPENDENCIES:   str  = "None"

    def __init__(self):
        self._model     = None
        self._processor = None
        self._device    = "cpu"

        if not _TRANSFORMERS_AVAILABLE:
            return

        try:
            import torch
            self._device    = "cuda" if torch.cuda.is_available() else "cpu"
            self._processor = CLIPProcessor.from_pretrained(self.MODEL_ID)
            self._model     = CLIPModel.from_pretrained(self.MODEL_ID).to(self._device)
            self._model.eval()
            logger.info("[FashionCLIPService] Loaded %s on %s", self.MODEL_ID, self._device)
        except Exception as e:
            logger.warning("[FashionCLIPService] Could not load model: %s", e)

    def is_available(self) -> bool:
        return self._model is not None and self._processor is not None

    def embed_image(self, image: Image.Image) -> List[float]:
        if not self.is_available():
            return []
        import torch
        inputs = self._processor(images=image, return_tensors="pt").to(self._device)
        with torch.no_grad():
            feats = self._model.get_image_features(**inputs)
            if hasattr(feats, "image_embeds") and feats.image_embeds is not None:
                feats = feats.image_embeds
            elif hasattr(feats, "pooler_output") and feats.pooler_output is not None:
                feats = feats.pooler_output
            feats = feats / feats.norm(dim=-1, keepdim=True)
        return feats[0].cpu().tolist()

    def embed_text(self, text: str) -> List[float]:
        if not self.is_available():
            return []
        import torch
        inputs = self._processor(text=[text], return_tensors="pt", padding=True).to(self._device)
        with torch.no_grad():
            feats = self._model.get_text_features(**inputs)
            if hasattr(feats, "text_embeds") and feats.text_embeds is not None:
                feats = feats.text_embeds
            elif hasattr(feats, "pooler_output") and feats.pooler_output is not None:
                feats = feats.pooler_output
            feats = feats / feats.norm(dim=-1, keepdim=True)
        return feats[0].cpu().tolist()
