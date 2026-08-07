"""
Phase 6 – Embedding Model Benchmark Runner.

Measures ALL evaluation metrics for each candidate embedding model.
Models are benchmarked only if they are already downloaded/cached;
missing models are skipped gracefully and marked "not_available".

Metrics measured per model:
  Static (no model load required):
    - embedding_dim
    - approx_model_size_mb
    - license
    - local_inference
    - integration_complexity
    - external_dependencies

  Dynamic (requires model to be loaded + available):
    - available:            True/False
    - image_latency_ms:     avg over N_RUNS test image embeds
    - text_latency_ms:      avg over N_RUNS test text embeds
    - vram_usage_mb:        GPU memory used after load (0 on CPU)
    - embedding_dim_actual: confirmed from actual vector length
    - text_image_similarity:cosine similarity between "white shirt" → image embed
    - retrieval_recall_at_k: recall@K over SYNTHETIC_QUERIES (text→image)

Usage:
  result = await run_embedding_benchmark()
  # Returns list of BenchmarkResult dicts, one per model.
"""

import time
import logging
import asyncio
from typing import List, Dict, Any, Optional

from app.services.embedding.model_registry import EMBEDDING_MODEL_CATALOG

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Benchmark configuration
# ---------------------------------------------------------------------------

N_RUNS     = 5      # Number of timed runs to average latency
RECALL_K   = 3      # Recall@K for retrieval accuracy test

# Synthetic test prompts and matching garment descriptions
# Used to measure text-image alignment quality without real images.
SYNTHETIC_QUERIES = [
    {"text": "white formal oxford shirt",  "expected_category": "top"},
    {"text": "black slim fit trousers",    "expected_category": "bottom"},
    {"text": "brown leather boots",        "expected_category": "shoes"},
    {"text": "navy blue wool blazer",      "expected_category": "outerwear"},
    {"text": "red casual summer dress",    "expected_category": "dress"},
]

# ---------------------------------------------------------------------------
# Benchmark result schema
# ---------------------------------------------------------------------------

def _empty_result(model_meta: dict) -> dict:
    return {
        # Static info
        "key":                   model_meta["key"],
        "model_name":            model_meta["model_name"],
        "model_id":              model_meta["model_id"],
        "license":               model_meta["license"],
        "local_inference":       model_meta["local_inference"],
        "integration_complexity": model_meta["integration_complexity"],
        "external_dependencies": model_meta["external_dependencies"],
        "approx_model_size_mb":  model_meta["approx_model_size_mb"],
        "notes":                 model_meta["notes"],
        "recommended_for":       model_meta["recommended_for"],

        # Dynamic – filled in if model is available
        "available":             False,
        "skip_reason":           None,
        "embedding_dim_declared": model_meta["embedding_dim"],
        "embedding_dim_actual":  None,
        "image_latency_ms_avg":  None,
        "text_latency_ms_avg":   None,
        "vram_usage_mb":         None,
        "device":                None,
        "text_image_similarity": None,
        "retrieval_recall_at_k": None,
        "recall_k":              RECALL_K,
    }


# ---------------------------------------------------------------------------
# VRAM helper
# ---------------------------------------------------------------------------

def _vram_mb() -> float:
    """Current GPU memory allocated in MB (0 if no GPU)."""
    try:
        import torch
        if torch.cuda.is_available():
            return torch.cuda.memory_allocated() / (1024 ** 2)
    except Exception:
        pass
    return 0.0


def _device_str() -> str:
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


# ---------------------------------------------------------------------------
# Synthetic image helper (creates a plain-colour PIL image for latency tests)
# ---------------------------------------------------------------------------

def _make_test_image(width: int = 224, height: int = 224):
    """Returns a simple synthetic PIL image (no real fashion image needed)."""
    from PIL import Image as PILImage
    import random
    color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
    return PILImage.new("RGB", (width, height), color=color)


# ---------------------------------------------------------------------------
# Per-model benchmark function
# ---------------------------------------------------------------------------

def _benchmark_model(model_meta: dict) -> dict:
    """
    Synchronous benchmark for a single model.
    Returns a filled result dict.
    """
    result = _empty_result(model_meta)

    # Dynamically import the correct service class
    key = model_meta["key"]
    try:
        if key == "clip":
            from app.services.embedding.clip_service import CLIPService as Svc
        elif key == "fashion-clip":
            from app.services.embedding.fashion_clip_service import FashionCLIPService as Svc
        elif key == "siglip":
            from app.services.embedding.siglip_service import SigLIPService as Svc
        else:
            result["skip_reason"] = f"Unknown model key: {key}"
            return result
    except ImportError as e:
        result["skip_reason"] = f"Import error: {e}"
        return result

    # Instantiate (this loads the model if cached; skips if not)
    try:
        svc = Svc()
    except Exception as e:
        result["skip_reason"] = f"Instantiation error: {e}"
        return result

    if not svc.is_available():
        result["skip_reason"] = "Model not downloaded / library missing. Run: pip install transformers torch && python -c \"from transformers import CLIPModel; CLIPModel.from_pretrained('" + model_meta['model_id'] + "')\""
        return result

    result["available"] = True
    result["device"]    = _device_str()

    # ------------------------------------------------------------------
    # 1. Image latency (N_RUNS averaged)
    # ------------------------------------------------------------------
    test_img = _make_test_image()
    latencies = []
    vec = []
    for _ in range(N_RUNS):
        vec, ms = svc.timed_embed_image(test_img)
        latencies.append(ms)
    result["image_latency_ms_avg"] = round(sum(latencies) / len(latencies), 2)
    result["embedding_dim_actual"] = len(vec)

    # ------------------------------------------------------------------
    # 2. Text latency (N_RUNS averaged)
    # ------------------------------------------------------------------
    test_text = "casual white t-shirt"
    latencies = []
    for _ in range(N_RUNS):
        _, ms = svc.timed_embed_text(test_text)
        latencies.append(ms)
    result["text_latency_ms_avg"] = round(sum(latencies) / len(latencies), 2)

    # ------------------------------------------------------------------
    # 3. VRAM usage
    # ------------------------------------------------------------------
    result["vram_usage_mb"] = round(_vram_mb(), 2)

    # ------------------------------------------------------------------
    # 4. Text-image cosine similarity (same concept = high score expected)
    # ------------------------------------------------------------------
    try:
        img_vec  = svc.embed_image(test_img)
        text_vec = svc.embed_text(test_text)
        result["text_image_similarity"] = round(
            svc.cosine_similarity(img_vec, text_vec), 4
        )
    except Exception as e:
        logger.warning("[benchmark][%s] Similarity test failed: %s", key, e)

    # ------------------------------------------------------------------
    # 5. Retrieval Recall@K (text → text, synthetic)
    # Embeds each query text, compares against all other query texts,
    # checks if the top-K retrieved include the "expected" category match.
    # This is a proxy for real fashion retrieval without real images.
    # ------------------------------------------------------------------
    try:
        texts   = [q["text"] for q in SYNTHETIC_QUERIES]
        vecs    = [svc.embed_text(t) for t in texts]
        correct = 0

        for i, query_meta in enumerate(SYNTHETIC_QUERIES):
            query_vec = vecs[i]
            # Score against all OTHER texts
            scores = [
                (j, svc.cosine_similarity(query_vec, vecs[j]))
                for j in range(len(vecs)) if j != i
            ]
            scores.sort(key=lambda x: x[1], reverse=True)
            top_k_indices = [idx for idx, _ in scores[:RECALL_K]]

            # "Correct" if any top-K result shares the same expected_category
            expected_cat = query_meta["expected_category"]
            for j in top_k_indices:
                if SYNTHETIC_QUERIES[j]["expected_category"] == expected_cat:
                    correct += 1
                    break

        result["retrieval_recall_at_k"] = round(correct / len(SYNTHETIC_QUERIES), 3)
    except Exception as e:
        logger.warning("[benchmark][%s] Retrieval recall test failed: %s", key, e)

    return result


# ---------------------------------------------------------------------------
# Public async benchmark runner
# ---------------------------------------------------------------------------

async def run_embedding_benchmark(
    model_keys: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Run the full benchmark suite.

    Args:
        model_keys: List of model keys to benchmark.
                    Defaults to all models in EMBEDDING_MODEL_CATALOG.

    Returns:
        List of result dicts sorted by retrieval_recall_at_k desc (available models first).
    """
    catalog = EMBEDDING_MODEL_CATALOG
    if model_keys:
        catalog = [m for m in catalog if m["key"] in model_keys]

    results = []
    loop = asyncio.get_event_loop()

    for model_meta in catalog:
        logger.info("[benchmark] Benchmarking: %s", model_meta["key"])
        # Run in thread pool so it doesn't block the event loop
        result = await loop.run_in_executor(None, _benchmark_model, model_meta)
        results.append(result)

    # Sort: available models first, then by retrieval_recall_at_k desc
    results.sort(
        key=lambda r: (
            0 if r["available"] else 1,
            -(r["retrieval_recall_at_k"] or 0),
        )
    )

    return results


# ---------------------------------------------------------------------------
# Summary printer (for CLI use)
# ---------------------------------------------------------------------------

def print_benchmark_summary(results: List[Dict[str, Any]]) -> None:
    print("\n" + "=" * 80)
    print("  EMBEDDING MODEL BENCHMARK RESULTS")
    print("=" * 80)
    for r in results:
        print(f"\n  Model:       {r['model_name']} ({r['key']})")
        print(f"  Available:   {r['available']}")
        if not r["available"]:
            print(f"  Skip Reason: {r['skip_reason']}")
            continue
        print(f"  Device:      {r['device']}")
        print(f"  Dim:         declared={r['embedding_dim_declared']}  actual={r['embedding_dim_actual']}")
        print(f"  License:     {r['license']}")
        print(f"  Complexity:  {r['integration_complexity']}")
        print(f"  Model Size:  ~{r['approx_model_size_mb']} MB")
        print(f"  VRAM Used:   {r['vram_usage_mb']} MB")
        print(f"  Latency:     image={r['image_latency_ms_avg']} ms  text={r['text_latency_ms_avg']} ms")
        print(f"  Txt-Img Sim: {r['text_image_similarity']}")
        print(f"  Recall@{r['recall_k']}:   {r['retrieval_recall_at_k']}")
        print(f"  Notes:       {r['notes']}")
    print("=" * 80 + "\n")
