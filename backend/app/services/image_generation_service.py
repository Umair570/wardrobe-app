"""Provider-agnostic image generation for wardrobe visualization.

GeminiImageGeneration calls Gemini's real image model (gemini-2.5-flash-image,
aka "Nano Banana") directly and returns an actual generated image saved to
disk -- no third-party proxy involved.

If you pass `person_image_b64` (the user's uploaded body photo) and
`garment_image_urls` (the wardrobe item photos), Gemini performs true
image-to-image virtual try-on: it edits the person photo to show them wearing
those specific garments. If you only pass a text prompt, it falls back to
generating a generic fashion photo from the description -- still a real
Gemini image, just not tied to a specific person/garment pair.
"""

from __future__ import annotations

import base64
import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

import httpx


class ImageGenerator(ABC):
    @abstractmethod
    def generate_img(
        self,
        prompt: str,
        person_image_b64: str | None = None,
        garment_image_urls: list[str] | None = None,
    ) -> str:
        """Generate/edit an image and return a URL or file path to it.

        person_image_b64: base64-encoded JPEG/PNG of the user's body photo
            (no "data:image/..." prefix), if available.
        garment_image_urls: URLs (or local static paths) of the wardrobe item
            photos to place on the person.
        """
        raise NotImplementedError


class GeminiImageGeneration(ImageGenerator):
    MODEL = "gemini-2.5-flash-image"
    ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

    # Adjust this to wherever your FastAPI app mounts static files, e.g.
    #   app.mount("/static", StaticFiles(directory="static"), name="static")
    OUTPUT_DIR = Path("static/generated")
    OUTPUT_URL_PREFIX = "/static/generated"

    def generate_img(
        self,
        prompt: str,
        person_image_b64: str | None = None,
        garment_image_urls: list[str] | None = None,
    ) -> str:
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Get a free key from Google AI "
                "Studio and add it to the backend .env."
            )

        parts: list[dict] = []
        instruction = "Generate a single photorealistic full-body fashion photo. "

        if person_image_b64 and garment_image_urls:
            instruction += (
                "The first image below is a photo of the person -- keep their "
                "face, body shape, pose, and skin tone identical to that photo. "
                "Dress them in the garment(s) shown in the following image(s), "
                "matching realistic fit, fabric drape, and the lighting of the "
                "original photo. Do not add any clothing that isn't shown. "
            )
        instruction += f"Outfit description: {prompt}"
        parts.append({"text": instruction})

        if person_image_b64:
            parts.append({"inline_data": {"mime_type": "image/jpeg", "data": person_image_b64}})

        for url in garment_image_urls or []:
            img_b64, mime = self._fetch_as_b64(url)
            if img_b64:
                parts.append({"inline_data": {"mime_type": mime, "data": img_b64}})

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {"responseModalities": ["IMAGE"]},
        }
        headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}

        with httpx.Client(timeout=45.0) as client:
            res = client.post(self.ENDPOINT, json=payload, headers=headers)

        if res.status_code != 200:
            raise RuntimeError(f"Gemini image API error {res.status_code}: {res.text[:300]}")

        image_b64 = self._first_inline_image(res.json())
        if not image_b64:
            raise RuntimeError(f"Gemini returned no image data: {res.text[:300]}")

        return self._save_image(image_b64)

    @staticmethod
    def _first_inline_image(data: dict) -> str | None:
        for cand in data.get("candidates", []):
            for part in cand.get("content", {}).get("parts", []):
                inline = part.get("inlineData") or part.get("inline_data")
                if inline and inline.get("data"):
                    return inline["data"]
        return None

    @staticmethod
    def _fetch_as_b64(url: str) -> tuple[str | None, str]:
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.get(url)
            res.raise_for_status()
            mime = res.headers.get("content-type", "image/jpeg").split(";")[0]
            return base64.b64encode(res.content).decode("utf-8"), mime
        except Exception as err:
            print(f"[GeminiImageGen] Could not fetch garment image {url}: {err}")
            return None, "image/jpeg"

    def _save_image(self, image_b64: str) -> str:
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid.uuid4().hex}.png"
        path = self.OUTPUT_DIR / filename
        path.write_bytes(base64.b64decode(image_b64))
        return f"{self.OUTPUT_URL_PREFIX}/{filename}"


class IDMVTONImageGeneration(ImageGenerator):
    OUTPUT_DIR = Path("static/generated")
    OUTPUT_URL_PREFIX = "/static/generated"

    def generate_img(
        self,
        prompt: str,
        person_image_b64: str | None = None,
        garment_image_urls: list[str] | None = None,
    ) -> str:
        if not person_image_b64 or not garment_image_urls:
            raise ValueError("IDM-VTON requires both a person image and at least one garment image.")

        import uuid
        import tempfile
        import base64
        import os
        from gradio_client import Client, handle_file

        fd_person, temp_person_path = tempfile.mkstemp(suffix=".jpg")
        fd_garment, temp_garment_path = tempfile.mkstemp(suffix=".png")

        try:
            # 1. Decode person photo
            with os.fdopen(fd_person, 'wb') as f:
                f.write(base64.b64decode(person_image_b64))

            # 2. Fetch the garment file and write raw bytes to temp
            import httpx
            garment_url = garment_image_urls[0]
            with httpx.Client(timeout=15.0) as http_client:
                res = http_client.get(garment_url)
            res.raise_for_status()
            
            with os.fdopen(fd_garment, 'wb') as f:
                f.write(res.content)

            # Implement High-Availability clustering for free HuggingFace spaces.
            # We place the zero-traffic clones FIRST. The official yisol server has a massive
            # global queue which causes 2-minute timeouts. By hitting clones entirely, it executes instantly!
            hf_spaces = [
                "Nymbo/Virtual-Try-On",    # Clone (Zero Traffic)
                "wild-child/IDM-VTON",     # Clone (Zero Traffic)
                "practice-it/IDM-VTON",    # Clone (Zero Traffic)
                "renyuan/IDM-VTON",        # Clone (Zero Traffic)
                "yisol/IDM-VTON",          # Official (Heavy Traffic Queue - use as last resort)
            ]

            print(f"Connecting to HuggingFace Free Cluster... Uploading local temp files...")
            
            result = None
            last_err = None
            
            import os
            hf_token = os.getenv("HF_TOKEN")
            
            for space in hf_spaces:
                try:
                    print(f"[*] Attemping inference on HF Space: {space}")
                    # Modern gradio_client uses 'token' instead of 'hf_token'
                    if hf_token:
                        client = Client(space, token=hf_token)
                    else:
                        client = Client(space)
                    result = client.predict(
                        {"background": handle_file(temp_person_path), "layers": [], "composite": None},
                        handle_file(temp_garment_path),
                        prompt,
                        True,   # is_checked (Auto-crop & Resizing)
                        False,  # is_checked_crop
                        30,     # denoise_steps
                        42,     # seed
                        api_name="/tryon"
                    )
                    if result:
                        print(f"[+] Successfully generated image using {space}!")
                        break
                except Exception as e:
                    print(f"[-] Space {space} failed or is overloaded: {e}")
                    last_err = e
                    continue
            
            if not result:
                raise RuntimeError(f"All free HuggingFace clustered spaces are currently overloaded. Last error: {last_err}")

            # result is a tuple, index 0 is the output image path (saved in gradio's local cache)
            if isinstance(result, (list, tuple)):
                out_img_path = result[0]
            else:
                out_img_path = result

            # Read the generated image and save to static
            with open(out_img_path, "rb") as f:
                image_bytes = f.read()
            out_b64 = base64.b64encode(image_bytes).decode("utf-8")
            
            return self._save_image(out_b64)

        finally:
            for p in [temp_person_path, temp_garment_path]:
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass

    def _save_image(self, image_b64: str) -> str:
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        import uuid
        filename = f"vton_{uuid.uuid4().hex}.png"
        path = self.OUTPUT_DIR / filename
        import base64
        path.write_bytes(base64.b64decode(image_b64))
        return f"{self.OUTPUT_URL_PREFIX}/{filename}"


class ImageGenerationFactory:
    @staticmethod
    def get_img_gen_model(generator_name: str) -> ImageGenerator:
        """Return a provider implementation using a case-insensitive name."""
        name_lower = generator_name.lower()

        if name_lower == "gemini":
            return GeminiImageGeneration()
        if name_lower == "idm-vton":
            return IDMVTONImageGeneration()
        raise ValueError(f"Unknown generator model: {generator_name}")


def generate_image(
    prompt: str,
    model_name: str,
    person_image_b64: str | None = None,
    garment_image_urls: list[str] | None = None,
) -> str:
    """Generate an image through the selected provider implementation."""
    img_gen_model = ImageGenerationFactory.get_img_gen_model(model_name)
    return img_gen_model.generate_img(prompt, person_image_b64, garment_image_urls)