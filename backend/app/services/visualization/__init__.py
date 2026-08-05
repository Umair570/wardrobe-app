from app.services.visualization.base import VirtualTryOnAdapter
from app.services.visualization.fashn_vton import FashnVtonAdapter

def get_vton_model() -> VirtualTryOnAdapter:
    """
    Factory to retrieve the active Virtual Try-On adapter.
    FASHN VTON is the active modal-backed provider.
    """
    return FashnVtonAdapter()
