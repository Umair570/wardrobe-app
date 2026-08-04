"""
Phase 6 – SigLIP Embedding Service.

Model card:  google/siglip-base-patch16-224
License:     Apache 2.0
Dim:         768
HF Hub:      https://huggingface.co/google/siglip-base-patch16-224

SigLIP (Sigmoid Loss for Language Image Pre-Training) by Google replaces
softmax contrastive loss with sigmoid loss, improving performance especially
at small batch sizes. Larger embedding dim (768) captures richer features.

Install:     pip install transformers torch pillow
Download:    ~900 MB on first use (auto-cached by HuggingFace)
"""

import logging
from typing import List

from PIL import Image
from app.services.embedding.base import BaseEmbeddingService

logger = logging.getLogger(__name__)

try:
    from transformers import AutoProcessor, AutoModel
    import torch
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    _TRANSFORMERS_AVAILABLE = False
    logger.warning("[SigLIPService] transformers/torch not installed. SigLIPService will be unavailable.")


class SigLIPService(BaseEmbeddingService):
    """
    Google SigLIP – state-of-the-art image-text model with 768-dim embeddings.
    Higher representational capacity; may improve rare garment type retrieval.
    NOTE: 768-dim vectors require Qdrant collection to be re-initialised
    with vector_size=768 when switching from 512-dim models.
    """

    MODEL_NAME:              str  = "siglip-base"
    MODEL_ID:                str  = "google/siglip-base-patch16-224"
    EMBEDDING_DIM:           int  = 768
    LICENSE:                 str  = "Apache 2.0"
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
            self._processor = AutoProcessor.from_pretrained(self.MODEL_ID)
            self._model     = AutoModel.from_pretrained(self.MODEL_ID).to(self._device)
            self._model.eval()
            logger.info("[SigLIPService] Loaded %s on %s", self.MODEL_ID, self._device)
        except Exception as e:
            logger.warning("[SigLIPService] Could not load model: %s", e)

    def is_available(self) -> bool:
        return self._model is not None and self._processor is not None

    def embed_image(self, image: Image.Image) -> List[float]:
        if not self.is_available():
            return []
        import torch
        inputs = self._processor(images=image, return_tensors="pt").to(self._device)
        with torch.no_grad():
            feats = self._model.get_image_features(**inputs)
            feats = feats / feats.norm(dim=-1, keepdim=True)
        return feats[0].cpu().tolist()

    def embed_text(self, text: str) -> List[float]:
        if not self.is_available():
            return []
        import torch
        inputs = self._processor(text=[text], return_tensors="pt", padding=True).to(self._device)
        with torch.no_grad():
            feats = self._model.get_text_features(**inputs)
            feats = feats / feats.norm(dim=-1, keepdim=True)
        return feats[0].cpu().tolist()
