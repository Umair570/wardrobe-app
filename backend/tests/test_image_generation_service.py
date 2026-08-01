import unittest

from backend.app.services.image_generation_service import (
    GeminiImageGeneration,
    ImageGenerationFactory,
    QwenImageGeneration,
    generate_image,
)


class ImageGenerationFactoryTests(unittest.TestCase):
    def test_selects_gemini_case_insensitively(self) -> None:
        self.assertIsInstance(
            ImageGenerationFactory.get_img_gen_model("GeMiNi"), GeminiImageGeneration
        )

    def test_selects_qwen_case_insensitively(self) -> None:
        self.assertIsInstance(
            ImageGenerationFactory.get_img_gen_model("qwen"), QwenImageGeneration
        )

    def test_rejects_unknown_model(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown generator model"):
            ImageGenerationFactory.get_img_gen_model("unknown")

    def test_generates_through_selected_provider(self) -> None:
        self.assertEqual(
            generate_image("black shirt and blue jeans", "gemini"),
            "Gemini generated image for: black shirt and blue jeans",
        )


if __name__ == "__main__":
    unittest.main()
