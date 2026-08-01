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


class GeminiImageGeneration(ImageGenerator):
    def generate_img(self, prompt: str) -> str:
        # TODO: Replace with Gemini-specific image generation API logic.
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
