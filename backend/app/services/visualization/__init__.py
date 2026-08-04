from app.services.visualization.base import VirtualTryOnAdapter
from app.services.visualization.ootd_vton import OOTDiffusionAdapter

def get_vton_model() -> VirtualTryOnAdapter:
    """
    Factory to retrieve the active Virtual Try-On adapter.
    For Phase 16, this is hardcoded to OOTDiffusion to support multi-garment generation.
    """
    return OOTDiffusionAdapter()
