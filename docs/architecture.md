# Chatbot and visualization MVP decision

The chatbot receives only wardrobe metadata (item ID, category, type, color, and tags) and returns a concise outfit suggestion. Day 1 uses temporary mock items; Day 2 replaces them with Mahad's wardrobe API data.

Visualization is intentionally a 2D overlay: the frontend places a selected transparent garment PNG over a static body-template image using category-specific CSS positions. Full virtual try-on, pose estimation, and diffusion models are outside the 3-day MVP scope.
