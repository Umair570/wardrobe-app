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

    @unittest.mock.patch("httpx.Client.post")
    def test_generates_through_selected_provider(self, mock_post) -> None:
        mock_response = unittest.mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"inline_data": {"data": "fakeb64data"}}]
                }
            }]
        }
        mock_post.return_value = mock_response

        with unittest.mock.patch.object(GeminiImageGeneration, "_save_image", return_value="/static/generated/fake.png"):
            result = generate_image("black shirt and blue jeans", "gemini")
            self.assertEqual(result, "/static/generated/fake.png")




if __name__ == "__main__":
    unittest.main()
