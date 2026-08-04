"""
Backward-compatibility shim.

Phase 7 moved the Qdrant service to:
    app.services.vector.qdrant_service

This file re-exports the canonical singleton so that any code that still
imports from the old location continues to work without modification.
New code should import directly from the canonical location:
    from app.services.vector.qdrant_service import qdrant_service
"""

from app.services.vector.qdrant_service import qdrant_service, QdrantService  # noqa: F401
