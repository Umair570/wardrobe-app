import logging
import httpx
import os
from typing import Optional

from app.core.config import settings
from app.services.visualization.base import VirtualTryOnAdapter
from app.services.visualization.schemas import VirtualTryOnRequest, VirtualTryOnResponse

logger = logging.getLogger(__name__)

class OOTDiffusionAdapter(VirtualTryOnAdapter):
    """
    Adapter for OOTDiffusion Full-Body Model.
    Supports multi-garment try-on natively (Top + Bottom).
    This implementation calls the Modal.com serverless endpoint (Phase 18).
    """
    
    async def generate(self, request: VirtualTryOnRequest) -> VirtualTryOnResponse:
        try:
            request.check_has_garment()
        except ValueError as e:
            return VirtualTryOnResponse(
                success=False, 
                error_message=str(e), 
                provider="OOTDiffusion"
            )

        # The URL for the Modal deployment (Phase 18)
        modal_url = os.getenv("MODAL_OOTD_ENDPOINT", "https://your-modal-workspace--ootd-generate.modal.run")
        modal_token = os.getenv("MODAL_API_TOKEN", "")

        # Map our agnostic payload to OOTDiffusion's specific format
        # OOTDiffusion expects category: 0=Upper, 1=Lower, 2=Dress
        # If we have both top and bottom, we send category=3 (Full-Body custom for our Modal API)
        # We will design our Modal API to accept 'top_url' and 'bottom_url'
        payload = {
            "person_image_url": request.person_image_url,
            "top_garment_url": request.top_garment_url,
            "bottom_garment_url": request.bottom_garment_url,
            "dress_garment_url": request.dress_garment_url,
        }

        # For Phase 16 testing, if Modal endpoint is not configured, we return a mock success
        if modal_url == "https://your-modal-workspace--ootd-generate.modal.run":
            logger.info(f"[OOTDiffusionAdapter] Mock generation triggered for {payload}")
            return VirtualTryOnResponse(
                success=True,
                ai_image_url="https://mock-modal-output.com/mock-vton.png",
                provider="OOTDiffusion (Mock)"
            )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {modal_token}"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(modal_url, json=payload, headers=headers, timeout=60.0)
                response.raise_for_status()
                data = response.json()
                
                return VirtualTryOnResponse(
                    success=True,
                    ai_image_url=data.get("output_url"),
                    provider="OOTDiffusion"
                )
        except Exception as e:
            logger.error(f"[OOTDiffusionAdapter] API Call Failed: {e}")
            return VirtualTryOnResponse(
                success=False,
                error_message=f"Modal API Error: {str(e)}",
                provider="OOTDiffusion"
            )
