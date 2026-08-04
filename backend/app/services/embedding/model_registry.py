"""
Phase 6 – Embedding Model Registry.

Selects and exposes the active embedding model via a single singleton:
    from app.services.embedding.model_registry import embedding_service

Active model is controlled by EMBEDDING_MODEL in .env:
    EMBEDDING_MODEL=fashion-clip   # default (recommended)
    EMBEDDING_MODEL=clip
    EMBEDDING_MODEL=siglip

Adding a new model:
  1. Create a subclass of BaseEmbeddingService in a new file.
  2. Register it in _REGISTRY below.
  3. Set EMBEDDING_MODEL=<key> in .env.

Cloud inference (Phase 16+):
  When Modal.com integration is ready, add a ModalEmbeddingService subclass
  that calls a Modal function remotely and register it here as "modal-fashion-clip".
  The ingestion pipeline will pick it up without any other code changes.
"""

import logging
from typing import Dict, Type

from app.core.config import settings
from app.services.embedding.base import BaseEmbeddingService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Registry mapping – key → class (lazy-loaded to avoid importing heavy libs
# at startup when they are not the active model)
# ---------------------------------------------------------------------------

def _get_registry() -> Dict[str, Type[BaseEmbeddingService]]:
    from app.services.embedding.clip_service         import CLIPService
    from app.services.embedding.fashion_clip_service import FashionCLIPService
    from app.services.embedding.siglip_service       import SigLIPService

    return {
        "clip":         CLIPService,
        "fashion-clip": FashionCLIPService,
        "siglip":       SigLIPService,
    }


# ---------------------------------------------------------------------------
# Static metadata table (no model download required)
# Used by the benchmark endpoint to list all candidate models.
# ---------------------------------------------------------------------------

EMBEDDING_MODEL_CATALOG = [
    {
        "key":                   "clip",
        "model_name":            "CLIP ViT-B/32",
        "model_id":              "openai/clip-vit-base-patch32",
        "embedding_dim":         512,
        "license":               "MIT",
        "local_inference":       True,
        "integration_complexity": "Low",
        "external_dependencies": "None",
        "approx_model_size_mb":  600,
        "notes":                 "General-purpose baseline. Not fashion-specific.",
        "recommended_for":       "Baseline comparison",
    },
    {
        "key":                   "fashion-clip",
        "model_name":            "FashionCLIP",
        "model_id":              "patrickjohncyh/fashion-clip",
        "embedding_dim":         512,
        "license":               "MIT",
        "local_inference":       True,
        "integration_complexity": "Low",
        "external_dependencies": "None",
        "approx_model_size_mb":  600,
        "notes":                 "CLIP fine-tuned on 700K+ fashion images. Best for garment retrieval.",
        "recommended_for":       "Production (recommended)",
    },
    {
        "key":                   "siglip",
        "model_name":            "SigLIP (Google)",
        "model_id":              "google/siglip-base-patch16-224",
        "embedding_dim":         768,
        "license":               "Apache 2.0",
        "local_inference":       True,
        "integration_complexity": "Low",
        "external_dependencies": "None",
        "approx_model_size_mb":  900,
        "notes":                 "768-dim. Requires Qdrant collection re-init if switching from 512-dim models.",
        "recommended_for":       "Experimentation (larger dim, more capacity)",
    },
]


# ---------------------------------------------------------------------------
# Active model singleton
# ---------------------------------------------------------------------------

class _LazyEmbeddingService:
    """
    Wraps the active embedding service with lazy initialisation.
    The model is only loaded on first use (first embed call), not at import time.
    This prevents slow server startup when the model is not yet downloaded.
    """

    def __init__(self):
        self._instance: BaseEmbeddingService | None = None
        self._model_key: str = getattr(settings, "embedding_model", "fashion-clip")

    def _load(self) -> BaseEmbeddingService:
        if self._instance is not None:
            return self._instance

        registry = _get_registry()
        cls = registry.get(self._model_key)

        if cls is None:
            logger.error(
                "[ModelRegistry] Unknown EMBEDDING_MODEL '%s'. Falling back to FashionCLIP.",
                self._model_key,
            )
            from app.services.embedding.fashion_clip_service import FashionCLIPService
            cls = FashionCLIPService

        logger.info("[ModelRegistry] Loading embedding model: %s", self._model_key)
        self._instance = cls()

        if not self._instance.is_available():
            logger.warning(
                "[ModelRegistry] Model '%s' loaded but reported unavailable (missing library or download needed).",
                self._model_key,
            )

        return self._instance

    # Proxy all relevant calls to the underlying instance
    def embed_image(self, image) -> list:
        return self._load().embed_image(image)

    def embed_text(self, text: str) -> list:
        return self._load().embed_text(text)

    def embed_image_from_path(self, path: str) -> list:
        return self._load().embed_image_from_path(path)

    def cosine_similarity(self, a: list, b: list) -> float:
        return self._load().cosine_similarity(a, b)

    def timed_embed_image(self, image) -> tuple:
        return self._load().timed_embed_image(image)

    def timed_embed_text(self, text: str) -> tuple:
        return self._load().timed_embed_text(text)

    def is_available(self) -> bool:
        return self._load().is_available()

    def model_info(self) -> dict:
        return self._load().model_info()

    @property
    def active_key(self) -> str:
        return self._model_key


# Singleton – import this everywhere
embedding_service = _LazyEmbeddingService()
