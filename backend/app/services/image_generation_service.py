"""Provider-agnostic image generation foundation for wardrobe visualization.

Live Gemini and Qwen API integrations will replace the temporary return values
once the team chooses a provider and supplies the relevant API credentials.
"""

from abc import ABC, abstractmethod


class ImageGenerator(ABC):
    @abstractmethod
    def generate_img(self, prompt: str) -> str:
        """Generate an image from a prompt and return its URL or file path."""
        raise NotImplementedError


import os
import httpx


class GeminiImageGeneration(ImageGenerator):
    def generate_img(self, prompt: str) -> str:
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            return f"Gemini generated image for: {prompt}"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"Generate a high fashion, realistic full body photo of a person wearing: {prompt}. Studio lighting, professional portrait."
                }]
            }]
        }
        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
                parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                for part in parts:
                    if "inlineData" in part:
                        mime = part["inlineData"]["mimeType"]
                        b64 = part["inlineData"]["data"]
                        return f"data:{mime};base64,{b64}"
                    if "text" in part:
                        return f"Gemini generated image for: {prompt}"
        except Exception as err:
            print(f"[GeminiImageGen] API Notice: {err}")

        return f"Gemini generated image for: {prompt}"




class QwenImageGeneration(ImageGenerator):
    def generate_img(self, prompt: str) -> str:
        # TODO: Replace with Qwen-specific image generation API logic.
        return f"Qwen generated image for: {prompt}"


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


def generate_image(prompt: str, model_name: str) -> str:
    """Generate an image through the selected provider implementation."""
    img_gen_model = ImageGenerationFactory.get_img_gen_model(model_name)
    return img_gen_model.generate_img(prompt)
