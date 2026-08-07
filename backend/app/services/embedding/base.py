"""
Phase 6 – Abstract Embedding Base.

All embedding model implementations (CLIP, FashionCLIP, SigLIP, future models)
must subclass BaseEmbeddingService and implement embed_image() and embed_text().

This keeps the ingestion pipeline model-agnostic:
  - Swap the active model via EMBEDDING_MODEL in .env
  - For cloud inference (Modal.com), implement a ModalEmbeddingService
    subclass that calls modal.Function.remote() instead of running locally.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from PIL import Image
import time
import logging

logger = logging.getLogger(__name__)


class BaseEmbeddingService(ABC):
    """
    Abstract interface every embedding model must satisfy.
    Implementations: CLIPService, FashionCLIPService, SigLIPService (local)
                     ModalCLIPService (cloud – Phase 16+)
    """

    # Subclasses must declare these as class-level attributes
    MODEL_NAME: str = "base"
    MODEL_ID: str = ""          # HuggingFace model ID or API endpoint
    EMBEDDING_DIM: int = 512
    LICENSE: str = "unknown"
    LOCAL_INFERENCE: bool = True
    INTEGRATION_COMPLEXITY: str = "Low"   # Low | Medium | High
    EXTERNAL_DEPENDENCIES: str = "None"   # None | Preferred | Required

    # ------------------------------------------------------------------
    # Abstract methods – must be implemented by every subclass
    # ------------------------------------------------------------------

    @abstractmethod
    def embed_image(self, image: Image.Image) -> List[float]:
        """
        Encode a PIL image into a normalised float vector.
        Returns a list of floats of length EMBEDDING_DIM.
        """
        ...

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """
        Encode a text query into a normalised float vector.
        Returns a list of floats of length EMBEDDING_DIM.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """
        Returns True if the model is loaded and ready to use.
        Implementations should return False gracefully if the model
        library is not installed (ImportError) rather than crashing.
        """
        ...

    # ------------------------------------------------------------------
    # Concrete helpers available to all subclasses
    # ------------------------------------------------------------------

    def embed_image_from_path(self, image_path: str) -> List[float]:
        """Convenience wrapper: load image from disk then embed."""
        image = Image.open(image_path).convert("RGB")
        return self.embed_image(image)

    def cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Compute cosine similarity between two L2-normalised vectors."""
        if not vec_a or not vec_b:
            return 0.0
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = sum(a ** 2 for a in vec_a) ** 0.5
        norm_b = sum(b ** 2 for b in vec_b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def timed_embed_image(self, image: Image.Image) -> tuple[List[float], float]:
        """Returns (vector, latency_ms)."""
        t0 = time.perf_counter()
        vec = self.embed_image(image)
        return vec, (time.perf_counter() - t0) * 1000

    def timed_embed_text(self, text: str) -> tuple[List[float], float]:
        """Returns (vector, latency_ms)."""
        t0 = time.perf_counter()
        vec = self.embed_text(text)
        return vec, (time.perf_counter() - t0) * 1000

    def model_info(self) -> dict:
        """Return static metadata about this model (used by benchmark runner)."""
        return {
            "model_name":            self.MODEL_NAME,
            "model_id":              self.MODEL_ID,
            "embedding_dim":         self.EMBEDDING_DIM,
            "license":               self.LICENSE,
            "local_inference":       self.LOCAL_INFERENCE,
            "integration_complexity": self.INTEGRATION_COMPLEXITY,
            "external_dependencies": self.EXTERNAL_DEPENDENCIES,
        }
