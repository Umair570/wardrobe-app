"""
Phase 6 – Embedding Benchmark API Router.

GET  /api/v1/benchmark/embeddings
     Returns static catalog + live benchmark results for all models.
     Models not downloaded are included with available=false and skip_reason.

GET  /api/v1/benchmark/embeddings/catalog
     Returns static model catalog only (no benchmark run, instant response).

POST /api/v1/benchmark/embeddings/select
     Update the active embedding model at runtime (writes to in-memory only;
     to persist, set EMBEDDING_MODEL in .env).
"""

import json
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.core.security import UserContext
from app.auth.dependencies import get_current_user
from app.services.embedding.model_registry import EMBEDDING_MODEL_CATALOG, embedding_service
from app.services.embedding.benchmark import run_embedding_benchmark

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/benchmark", tags=["benchmark"])


# ---------------------------------------------------------------------------
# GET /benchmark/embeddings – full benchmark run
# ---------------------------------------------------------------------------

@router.get("/embeddings")
async def benchmark_embeddings(
    models: str = Query(
        default="",
        description="Comma-separated model keys to benchmark (e.g. 'clip,fashion-clip'). Leave empty for all.",
    ),
    current_user: UserContext = Depends(get_current_user),
):
    """
    Run the full embedding model benchmark.
    Models not yet downloaded are included with available=false.
    Dynamic metrics (latency, VRAM, recall) only run for downloaded models.
    """
    model_keys = [k.strip() for k in models.split(",") if k.strip()] or None

    logger.info("[benchmark] Starting embedding benchmark for user %s", current_user.id)
    results = await run_embedding_benchmark(model_keys=model_keys)

    # Determine current active model
    active_key = embedding_service.active_key

    return {
        "timestamp":    datetime.utcnow().isoformat() + "Z",
        "active_model": active_key,
        "models_benchmarked": len(results),
        "results":      results,
        "recommendation": (
            "FashionCLIP is recommended for production — fashion-specific training "
            "provides the best garment retrieval accuracy at the same model size as generic CLIP."
        ),
    }


# ---------------------------------------------------------------------------
# GET /benchmark/embeddings/catalog – static info only (no benchmark run)
# ---------------------------------------------------------------------------

@router.get("/embeddings/catalog")
async def embedding_catalog(
    current_user: UserContext = Depends(get_current_user),
):
    """
    Returns the static model catalog with metadata for all candidate models.
    No model loading or downloading is performed.
    """
    return {
        "active_model": embedding_service.active_key,
        "catalog":      EMBEDDING_MODEL_CATALOG,
        "metrics_legend": {
            "embedding_dim":         "Vector dimension stored in Qdrant",
            "approx_model_size_mb":  "Approximate checkpoint size on disk (MB)",
            "license":               "Model license – check before commercial use",
            "local_inference":       "Can run without external API calls",
            "integration_complexity": "Low = drop-in, Medium = config change needed",
            "external_dependencies": "External services required (None = fully self-hosted)",
        },
        "cloud_inference_note": (
            "For production, consider running these models on Modal.com (serverless GPU). "
            "Implement a ModalEmbeddingService subclass that calls modal.Function.remote() "
            "and register it in model_registry.py with key 'modal-fashion-clip'. "
            "The ingestion pipeline will pick it up with zero other changes."
        ),
    }
