import logging
import os
import httpx

from app.core.config import settings
from app.services.visualization.base import VirtualTryOnAdapter
from app.services.visualization.schemas import VirtualTryOnRequest, VirtualTryOnResponse
from app.services.visualization_service import VisualizationService

logger = logging.getLogger(__name__)


class FashnVtonAdapter(VirtualTryOnAdapter):
    """Adapter for the FASHN modal-backed virtual try-on service."""

    async def generate(self, request: VirtualTryOnRequest) -> VirtualTryOnResponse:
        try:
            request.check_has_garment()
        except ValueError as error:
            return VirtualTryOnResponse(
                success=False,
                error_message=str(error),
                provider="FASHN modal",
            )

        fashn_url = settings.fashn_vton_endpoint
        if not fashn_url:
            return VirtualTryOnResponse(
                success=False,
                error_message="FASHN_VTON_ENDPOINT is not set (legacy MODAL_OOTD_ENDPOINT is still accepted).",
                provider="FASHN modal",
            )

        modal_token = os.getenv("MODAL_API_TOKEN", "")
        viz = VisualizationService()

        logger.info("========== FASHN VTON INPUT ==========")
        logger.info("PERSON URL: %s", request.person_image_url)
        logger.info("TOP URL: %s", request.top_garment_url)
        logger.info("BOTTOM URL: %s", request.bottom_garment_url)
        logger.info("DRESS URL: %s", request.dress_garment_url)
        logger.info("======================================")

        person_b64 = await viz._to_base64(str(request.person_image_url))

        payload = {
            "person_image_b64": person_b64,
            "hf_token": request.hf_token or settings.hf_token,
        }

        if request.dress_garment_url:
            payload["dress_garment_b64"] = await viz._to_base64(str(request.dress_garment_url))

        if request.top_garment_url:
            payload["top_garment_b64"] = await viz._to_base64(str(request.top_garment_url))

        if request.bottom_garment_url:
            payload["bottom_garment_b64"] = await viz._to_base64(str(request.bottom_garment_url))

        logger.info(
            "BASE64 sizes | person=%d top=%s bottom=%s dress=%s",
            len(person_b64),
            len(payload.get("top_garment_b64", "")),
            len(payload.get("bottom_garment_b64", "")),
            len(payload.get("dress_garment_b64", "")),
        )

        headers = {"Content-Type": "application/json"}
        if modal_token:
            headers["Authorization"] = f"Bearer {modal_token}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(fashn_url, json=payload, headers=headers, timeout=600.0)
                response.raise_for_status()
                data = response.json()

                if not data.get("success"):
                    return VirtualTryOnResponse(
                        success=False,
                        error_message=data.get("error", "Unknown FASHN error"),
                        provider="FASHN modal",
                    )

                output_b64 = data.get("output_b64")
                if not output_b64:
                    return VirtualTryOnResponse(
                        success=False,
                        error_message="Empty B64 output from FASHN modal",
                        provider="FASHN modal",
                    )

                return VirtualTryOnResponse(
                    success=True,
                    ai_image_url=f"data:image/png;base64,{output_b64}",
                    provider="FASHN modal",
                )
            except httpx.HTTPStatusError as error:
                body = (error.response.text or "").strip() or "(empty response body)"
                logger.error("[FashnVtonAdapter] Modal HTTP %s: %s", error.response.status_code, body)
                return VirtualTryOnResponse(
                    success=False,
                    error_message=f"FASHN modal returned HTTP {error.response.status_code}: {body}",
                    provider="FASHN modal",
                )
            except httpx.TimeoutException:
                logger.error("[FashnVtonAdapter] Modal request timed out.")
                return VirtualTryOnResponse(
                    success=False,
                    error_message=(
                        "The try-on service timed out. This is usually a cold start — "
                        "the GPU container is loading its weights. Please try again shortly."
                    ),
                    provider="FASHN modal",
                )
            except Exception as error:
                logger.error("[FashnVtonAdapter] Modal API call failed: %s", error)
                return VirtualTryOnResponse(
                    success=False,
                    error_message=f"FASHN modal API error: {error}",
                    provider="FASHN modal",
                )