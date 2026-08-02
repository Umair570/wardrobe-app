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


class QwenImageGeneration(ImageGenerator):
    def generate_img(
        self,
        prompt: str,
        person_image_b64: str | None = None,
        garment_image_urls: list[str] | None = None,
    ) -> str:
        # Not wired up. The old version returned a plain string labeled as an
        # "image" -- that's fake output, so it's removed rather than kept as
        # a silent no-op. Qwen-Image-Edit does support try-on (via Alibaba's
        # DashScope API), but it needs its own request/response handling --
        # ping me if you want this built out; don't route to this class until
        # then, or wire your frontend's provider toggle to only offer Gemini.
        raise NotImplementedError(
            "QwenImageGeneration is not implemented yet. Use 'gemini' as the "
            "provider until this is built."
        )


class ImageGenerationFactory:
    @staticmethod
    def get_img_gen_model(generator_name: str) -> ImageGenerator:
        """Return a provider implementation using a case-insensitive name."""
        name_lower = generator_name.lower()

        if name_lower == "gemini":
            return GeminiImageGeneration()
        if name_lower == "qwen":
            return QwenImageGeneration()
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