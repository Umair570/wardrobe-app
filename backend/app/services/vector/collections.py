"""
Phase 7 – Qdrant Collection Manager.

Handles:
  - Collection creation with the correct vector dimension for the active
    embedding model (512 for CLIP/FashionCLIP, 768 for SigLIP).
  - Payload index creation so Qdrant can filter on user_id, category, season
    without doing a full scan.
  - Safe collection migration when switching between models with different dims.

Used by QdrantService at startup.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qmodels
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False


# ---------------------------------------------------------------------------
# Payload index fields (enables fast filtering without full scan)
# ---------------------------------------------------------------------------

INDEXED_PAYLOAD_FIELDS = [
    ("user_id",  "keyword"),   # always required – isolates per-user data
    ("category", "keyword"),   # top | bottom | shoes | outerwear
    ("season",   "keyword"),   # summer | winter | all-season
    ("style",    "keyword"),   # formal | casual
    ("color",    "keyword"),   # white | black | navy …
]


def _get_embedding_dim() -> int:
    """
    Reads the active embedding model's declared dimension from the registry
    without loading the model weights.
    Falls back to 512 if the registry is unavailable.
    """
    try:
        from app.services.embedding.model_registry import EMBEDDING_MODEL_CATALOG
        from app.core.config import settings
        active_key = getattr(settings, "embedding_model", "fashion-clip")
        for m in EMBEDDING_MODEL_CATALOG:
            if m["key"] == active_key:
                return m["embedding_dim"]
    except Exception as e:
        logger.warning("[collections] Could not resolve embedding dim: %s", e)
    return 512


def ensure_collection(
    client: "QdrantClient",
    collection_name: str,
    vector_size: Optional[int] = None,
) -> None:
    """
    Create the Qdrant collection if it does not exist.
    If it already exists with a DIFFERENT vector size (e.g. switching from
    CLIP 512 to SigLIP 768), logs a warning — manual migration is required.

    Args:
        client:          Qdrant client instance.
        collection_name: Collection to create / verify.
        vector_size:     Override dim; defaults to active embedding model dim.
    """
    if not QDRANT_AVAILABLE or client is None:
        return

    dim = vector_size or _get_embedding_dim()

    try:
        existing = [c.name for c in client.get_collections().collections]

        if collection_name not in existing:
            # Create fresh collection
            client.create_collection(
                collection_name=collection_name,
                vectors_config=qmodels.VectorParams(
                    size=dim,
                    distance=qmodels.Distance.COSINE,
                ),
            )
            logger.info(
                "[collections] Created collection '%s' (dim=%d, distance=COSINE)",
                collection_name, dim,
            )
            _create_payload_indexes(client, collection_name)

        else:
            # Verify existing collection has matching dim
            info = client.get_collection(collection_name)
            existing_dim = info.config.params.vectors.size  # type: ignore[union-attr]
            if existing_dim != dim:
                logger.warning(
                    "[collections] Collection '%s' exists with dim=%d but active model "
                    "expects dim=%d. Re-init required if you switched embedding models. "
                    "See: backend/app/services/vector/collections.py",
                    collection_name, existing_dim, dim,
                )
            else:
                logger.info(
                    "[collections] Collection '%s' already exists (dim=%d). OK.",
                    collection_name, existing_dim,
                )
            _create_payload_indexes(client, collection_name)

    except Exception as e:
        logger.error("[collections] Collection ensure failed for '%s': %s", collection_name, e)


def _create_payload_indexes(client: "QdrantClient", collection_name: str) -> None:
    """
    Create payload indexes for fast filtered search.
    Idempotent — Qdrant ignores duplicate index creation.
    """
    for field_name, field_type in INDEXED_PAYLOAD_FIELDS:
        try:
            schema = (
                qmodels.PayloadSchemaType.KEYWORD
                if field_type == "keyword"
                else qmodels.PayloadSchemaType.INTEGER
            )
            client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=schema,
            )
        except Exception as e:
            msg = str(e).lower()
            if "already exists" in msg or "conflict" in msg:
                pass  # idempotent
            else:
                logger.warning(
                    "[collections] Index '%s' on '%s' failed: %s",
                    field_name, collection_name, e,
                )

    logger.info("[collections] Payload indexes ensured for '%s'", collection_name)
