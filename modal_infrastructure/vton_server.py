import modal
import os
import sys
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Optional
import urllib.request
from pydantic import BaseModel
from fastapi import FastAPI, Request

# ==============================================================================
# Modal Application Setup
# ==============================================================================
# Using a unique app name to track Native VTON execution
app = modal.App("wardrobe-vton-native")

# Deploy a persistent network drive to cache 20GB of diffusers weights across cold-boots
vton_volume = modal.Volume.from_name("fashn-weights-cache", create_if_missing=True)

# Build a monolithic deep-learning image
image = (
    modal.Image.from_registry("nvidia/cuda:12.1.1-devel-ubuntu22.04", add_python="3.10")
    .apt_install("git", "libgl1-mesa-glx", "libglib2.0-0")
    # Freezing PyTorch and Transformers to bypass a zero-day Hugging Face bleeding-edge incompatibility
    .run_commands("pip install torch==2.3.0 torchvision==0.18.0 torchaudio==2.3.0 --index-url https://download.pytorch.org/whl/cu121")
    .pip_install("transformers==4.40.1", "onnxruntime-gpu", "huggingface_hub", "pillow", "fastapi[standard]", "pydantic", "httpx")
    # Clone the entire repository natively to access internal shell utility scripts that pip drops
    .run_commands(
        "git clone https://github.com/fashn-AI/fashn-vton-1.5.git /fashn-core",
        "pip install -e /fashn-core"
    )
)

# Optional helper step to prime the Volume prior to running the app
@app.function(image=image, volumes={"/weights": vton_volume}, timeout=1500)
def download_models():
    from huggingface_hub import snapshot_download, hf_hub_download
    print("Initiating FASHN Model Download to Persistent Volume via HuggingFace Hub...")
    
    # Download FASHN weights seamlessly into the Modal network volume
    snapshot_download(repo_id="fashn-ai/fashn-vton-1.5", local_dir="/weights")
    
    # Manually pull dwpose ONNX files as expected by TryOnPipeline
    hf_hub_download(repo_id="yzd-v/DWPose", filename="yolox_l.onnx", local_dir="/weights/dwpose")
    hf_hub_download(repo_id="yzd-v/DWPose", filename="dw-ll_ucoco_384.onnx", local_dir="/weights/dwpose")
    
    vton_volume.commit()
    print("Download Succeeded.")

# ==============================================================================
# The Core AI Inference Runner
# ==============================================================================
@app.cls(
    image=image, 
    gpu="A10G", 
    volumes={"/weights": vton_volume},
    scaledown_window=120, # Keeps GPU warm between immediate rapid-fire tryons
    timeout=1200
)
class NativeFashnEngine:
    @modal.enter()
    def preload_pipeline(self):
        print("Spinning up VRAM and mounting native weights...")
        from fashn_vton import TryOnPipeline
        self.pipeline = TryOnPipeline(weights_dir="/weights")

    @modal.method()
    def process_pass(self, person_bytes: bytes, garment_bytes: bytes, category: str) -> bytes:
        from PIL import Image
        import io

        print(f"Executing native FASHN-VTON pass for {category}")
        person = Image.open(io.BytesIO(person_bytes)).convert("RGB")
        garment = Image.open(io.BytesIO(garment_bytes)).convert("RGB")

        result = self.pipeline(
            person_image=person,
            garment_image=garment,
            category=category,
            num_timesteps=40,
            guidance_scale=1.5,
            segmentation_free=True
        )

        out_buffer = io.BytesIO()
        result.images[0].save(out_buffer, format="PNG")
        return out_buffer.getvalue()

# ==============================================================================
# Web API Endpoint for Backend Communication
# ==============================================================================
web_app = FastAPI()

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@web_app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Modal RequestValidationError: " + str(exc.errors())}
    )

class VTONRequest(BaseModel):
    person_image_b64: str
    top_garment_b64: Optional[str] = None
    bottom_garment_b64: Optional[str] = None
    dress_garment_b64: Optional[str] = None
    hf_token: Optional[str] = None

@web_app.post("/")
def process_vton(req: VTONRequest):
    try:
        import base64
        print("API Hit: Deserializing base64 payload from Webhook...")

        def _b64_to_bytes(b64_str: str) -> bytes:
            if not b64_str: return b""
            # Strip data URI header if randomly attached by frontend proxy bugs
            if b64_str.startswith("data:"):
                b64_str = b64_str.split(",", 1)[1]
            return base64.b64decode(b64_str)

        current_img_bytes = _b64_to_bytes(req.person_image_b64)
        engine = NativeFashnEngine()

        if req.dress_garment_b64:
            local_garm = _b64_to_bytes(req.dress_garment_b64)
            current_img_bytes = engine.process_pass.remote(current_img_bytes, local_garm, "one-pieces")
        else:
            if req.top_garment_b64:
                local_top = _b64_to_bytes(req.top_garment_b64)
                current_img_bytes = engine.process_pass.remote(current_img_bytes, local_top, "tops")
            
            if req.bottom_garment_b64:
                local_bot = _b64_to_bytes(req.bottom_garment_b64)
                current_img_bytes = engine.process_pass.remote(current_img_bytes, local_bot, "bottoms")

        b64_str = base64.b64encode(current_img_bytes).decode("utf-8")
        return {"output_b64": b64_str, "success": True}
        
    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        return {"success": False, "error": str(e), "traceback": trace}

@app.function(image=image, timeout=600)
@modal.asgi_app()
def fastapi_app():
    return web_app
