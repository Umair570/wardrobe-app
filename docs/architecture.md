# Chatbot and visualization MVP decision

The chatbot receives only wardrobe metadata (item ID, category, type, color, and tags) and returns a concise outfit suggestion. Day 1 uses temporary mock items; Day 2 replaces them with Mahad's wardrobe API data.

Visualization is intentionally a 2D overlay: the frontend places a selected transparent garment PNG over a static body-template image using category-specific CSS positions. Full virtual try-on, pose estimation, and diffusion models are outside the 3-day MVP scope.

An `ImageGenerationFactory` foundation is available for a future Gemini or Qwen enhancement. It is provider-agnostic and currently returns placeholders only; live API integration, storage, and frontend rendering belong to the Day 2 visualization work. The static overlay remains the MVP fallback if image generation is unavailable or fails.
