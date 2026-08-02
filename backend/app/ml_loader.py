"""Lazy loader for Umair's ML pipeline.

The ML pipeline (cv2, torch, SAM2, FashionCLIP, etc.) is only imported when
the upload endpoint actually receives a request. This keeps the FastAPI server
startable without the heavy ML dependencies installed.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _ensure_repo_on_path() -> None:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))


def process_wardrobe_upload(source_path: str) -> dict:
    """Proxy that lazily imports the real pipeline on first call.

    Raises ImportError with a clear message if cv2/torch are not installed.
    """
    _ensure_repo_on_path()
    try:
        from ml.pipeline import process_wardrobe_upload as _real  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "ML pipeline is not installed. Run: pip install opencv-python torch "
            "torchvision segment-anything-2 transformers\n"
            f"Original error: {exc}"
        ) from exc
    return _real(source_path)


__all__ = ["process_wardrobe_upload"]