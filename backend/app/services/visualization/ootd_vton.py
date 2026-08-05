import logging
import httpx
import os
import uuid
import asyncio
from typing import Optional

from app.core.config import settings
from app.services.visualization.base import VirtualTryOnAdapter
from app.services.visualization.schemas import VirtualTryOnRequest, VirtualTryOnResponse
from app.services.storage.supabase import supabase_storage
from app.constants.storage_paths import BUCKET_VISUALIZATIONS

logger = logging.getLogger(__name__)

class OOTDiffusionAdapter(VirtualTryOnAdapter):
    """
    Adapter for OOTDiffusion Full-Body Model.
    Supports multi-garment try-on natively (Top + Bottom).
    This implementation calls the Modal.com serverless endpoint or Hugging Face Gradio space based on config.
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

        ootd_provider = settings.ootd_provider

        if ootd_provider == "modal":
            modal_url = settings.modal_ootd_endpoint
            if not modal_url:
                return VirtualTryOnResponse(success=False, error_message="MODAL_OOTD_ENDPOINT not set for Modal provider", provider="FASHN modal")
                
            modal_token = os.getenv("MODAL_API_TOKEN", "")
            # Download the images as Base64 natively instead of handing URLs to Modal, 
            # since Modal cannot resolve localhost/Dev proxy domains over the cloud
            from app.services.visualization_service import VisualizationService
            viz = VisualizationService()
            
            person_b64 = await viz._to_base64(str(request.person_image_url))
            
            payload = {
                "person_image_b64": person_b64,
                "hf_token": settings.hf_token
            }
            
            if request.dress_garment_url:
                payload["dress_garment_b64"] = await viz._to_base64(str(request.dress_garment_url))
            
            if request.top_garment_url:
                payload["top_garment_b64"] = await viz._to_base64(str(request.top_garment_url))
                
            if request.bottom_garment_url:
                payload["bottom_garment_b64"] = await viz._to_base64(str(request.bottom_garment_url))

            headers = {
                "Content-Type": "application/json",
            }
            if modal_token:
                headers["Authorization"] = f"Bearer {modal_token}"

            # Send byte stream to remote cloud.
            # The timeout has to cover a Modal cold start: spinning up the A10G
            # and mounting ~20 GB of FASHN weights takes minutes on the first
            # call, versus ~40 s once the container is warm. 300 s was short
            # enough to fail every cold request.
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.post(modal_url, json=payload, headers=headers, timeout=600.0)
                    response.raise_for_status()
                    data = response.json()
                    
                    if not data.get("success"):
                        return VirtualTryOnResponse(success=False, error_message=data.get("error", "Unknown Modal Error"), provider="FASHN Modal")
                    
                    b64 = data.get("output_b64")
                    if not b64:
                        return VirtualTryOnResponse(success=False, error_message="Empty B64 Output from Modal", provider="FASHN Modal")
                    
                    return VirtualTryOnResponse(
                        success=True,
                        ai_image_url=f"data:image/png;base64,{b64}",
                        provider="FASHN modal"
                    )
                except httpx.HTTPStatusError as e:
                    # Modal returns an empty body on gateway-level failures, so
                    # the status code has to be in the message or the error
                    # reaches the user as "Validation Error: " with no cause.
                    body = (e.response.text or "").strip() or "(empty response body)"
                    logger.error(
                        "[OOTDiffusionAdapter] Modal HTTP %s: %s", e.response.status_code, body
                    )
                    return VirtualTryOnResponse(
                        success=False,
                        error_message=f"Modal returned HTTP {e.response.status_code}: {body}",
                        provider="FASHN modal"
                    )
                except httpx.TimeoutException:
                    logger.error("[OOTDiffusionAdapter] Modal request timed out.")
                    return VirtualTryOnResponse(
                        success=False,
                        error_message=(
                            "The try-on service timed out. This is usually a cold start — "
                            "the GPU container is loading its weights. Please try again shortly."
                        ),
                        provider="FASHN modal"
                    )
                except Exception as e:
                    logger.error(f"[OOTDiffusionAdapter] Modal API Call Failed: {e}")
                    import traceback
                    traceback.print_exc()
                    return VirtualTryOnResponse(
                        success=False,
                        error_message=f"Modal API Error: {str(e)}",
                        provider="FASHN modal"
                    )
        
        elif ootd_provider == "gradio":
            gradio_space = os.getenv("OOTD_GRADIO_SPACE", "levihsu/OOTDiffusion")
            logger.info(f"[OOTDiffusionAdapter] Triggering Gradio OOTDiffusion on {gradio_space}")
            
            try:
                from gradio_client import Client, handle_file
                
                def _run_gradio_pass(person_img, garment_img, cat_type, api_name):
                    client = Client(gradio_space)
                    kwargs = {
                        "vton_img": handle_file(person_img),
                        "garm_img": handle_file(garment_img),
                        "n_samples": 1,
                        "n_steps": 20,
                        "image_scale": 2.0,
                        "seed": -1,
                    }
                    if api_name == "/process_dc":
                        kwargs["category"] = cat_type
                        
                    result = client.predict(api_name=api_name, **kwargs)
                    
                    if isinstance(result, tuple):
                        return result[0][0]['image'] if isinstance(result[0], list) and 'image' in result[0][0] else result[0]
                    elif isinstance(result, (list, str)):
                        return result[0]['image'] if isinstance(result, list) and len(result) > 0 and 'image' in result[0] else str(result)
                    return str(result)

                loop = asyncio.get_event_loop()
                current_img = request.person_image_url
                
                if request.dress_garment_url:
                    current_img = await loop.run_in_executor(
                        None, _run_gradio_pass, current_img, request.dress_garment_url, "Dress", "/process_dc"
                    )
                else:
                    if request.top_garment_url:
                        # Use HD for better quality if ONLY top, else DC for full-body compatibility
                        api = "/process_hd" if not request.bottom_garment_url else "/process_dc"
                        current_img = await loop.run_in_executor(
                            None, _run_gradio_pass, current_img, request.top_garment_url, "Upper-body", api
                        )
                    
                    if request.bottom_garment_url:
                        current_img = await loop.run_in_executor(
                            None, _run_gradio_pass, current_img, request.bottom_garment_url, "Lower-body", "/process_dc"
                        )
                        
                result_path = current_img
                
                # Upload the temp image to Supabase
                with open(result_path, "rb") as f:
                    file_bytes = f.read()
                    
                filename = f"ootd_vton_{uuid.uuid4().hex}.png"
                path = f"anon/{filename}"
                
                ai_url = await supabase_storage.upload_file_bytes(
                    bucket=BUCKET_VISUALIZATIONS,
                    path=path,
                    data=file_bytes,
                    content_type="image/png"
                )
                
                return VirtualTryOnResponse(
                    success=True,
                    ai_image_url=ai_url,
                    provider="OOTDiffusion Gradio"
                )
            except Exception as e:
                logger.error(f"[OOTDiffusionAdapter] Gradio Call Failed: {e}")
                return VirtualTryOnResponse(
                    success=False, 
                    error_message=f"Gradio space error: {str(e)}", 
                    provider="OOTDiffusion Gradio"
                )
                
        return VirtualTryOnResponse(success=False, error_message="Invalid OOTD_PROVIDER", provider="OOTDiffusion")
