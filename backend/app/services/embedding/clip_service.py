"""
Phase 6 – OpenAI CLIP Embedding Service (ViT-B/32).

Model card:  openai/clip-vit-base-patch32
License:     MIT
Dim:         512
HF Hub:      https://huggingface.co/openai/clip-vit-base-patch32

Install:     pip install transformers torch pillow
Download:    ~600 MB on first use (auto-cached by HuggingFace)
"""

import logging
from typing import List, Optional

from PIL import Image
from app.services.embedding.base import BaseEmbeddingService

logger = logging.getLogger(__name__)

try:
    from transformers import CLIPProcessor, CLIPModel
    import torch
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    _TRANSFORMERS_AVAILABLE = False
    logger.warning("[CLIPService] transformers/torch not installed. CLIPService will be unavailable.")


class CLIPService(BaseEmbeddingService):
    """
    Standard OpenAI CLIP (ViT-B/32) – the baseline embedding model.
    General-purpose vision-language model, not fashion-specific.
    """

    MODEL_NAME:              str  = "clip-vit-b32"
    MODEL_ID:                str  = "openai/clip-vit-base-patch32"
    EMBEDDING_DIM:           int  = 512
    LICENSE:                 str  = "MIT"
    LOCAL_INFERENCE:         bool = True
    INTEGRATION_COMPLEXITY:  str  = "Low"
    EXTERNAL_DEPENDENCIES:   str  = "None"

    def __init__(self):
        self._model    = None
        self._processor = None
        self._device   = "cpu"

        if not _TRANSFORMERS_AVAILABLE:
            return

        try:
            import torch
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            self._processor = CLIPProcessor.from_pretrained(self.MODEL_ID)
            self._model     = CLIPModel.from_pretrained(self.MODEL_ID).to(self._device)
            self._model.eval()
            logger.info("[CLIPService] Loaded %s on %s", self.MODEL_ID, self._device)
        except Exception as e:
            logger.warning("[CLIPService] Could not load model: %s", e)

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
            feats = feats / feats.norm(dim=-1, keepdim=True)   # L2 normalise
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
