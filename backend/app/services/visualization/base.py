from abc import ABC, abstractmethod
from app.services.visualization.schemas import VirtualTryOnRequest, VirtualTryOnResponse

class VirtualTryOnAdapter(ABC):
    """
    Abstract Base Class for Virtual Try-On models (Phase 16).
    Enforces a strict interface so that the backend router can swap underlying 
    AI models (OOTDiffusion, IDM-VTON, etc.) without breaking.
    """
    
    @abstractmethod
    async def generate(self, request: VirtualTryOnRequest) -> VirtualTryOnResponse:
        """
        Executes the Try-On generation.
        
        Args:
            request: VirtualTryOnRequest containing person image and garment URLs.
            
        Returns:
            VirtualTryOnResponse containing the resulting AI image URL or an error.
        """
        pass
