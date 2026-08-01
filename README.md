# AI Wardrobe Assistant - MVP

An AI-powered wardrobe application where users upload clothing photos, organize detected garments into a digital wardrobe, receive outfit suggestions, and visualize selected clothing.

## Current MVP status

| Area | Owner | Status | Notes |
| --- | --- | --- | --- |
| Segmentation and classification | Umair | Implemented | CLIPSeg + SAM2 segmentation, FashionCLIP metadata classification, and color extraction are available in `ml/`. |
| Backend and database | Mahad | Pending integration | FastAPI, database connection, upload/storage, wardrobe endpoints, and app router mounting are still required. |
| Main screen and wardrobe UI | Ayesha | Pending integration | Frontend project and API-connected screens are still required. |
| Chatbot and visualization | Abdulrehman | Foundation complete | OpenRouter-backed chatbot, mock wardrobe context, visualization architecture, and Gemini/Qwen factory foundation are ready for integration. |

## Features

- Upload a clothing image.
- Segment clothing items from the image background.
- Classify garment category, type, style, season, pattern, and color.
- Save classified items to a digital wardrobe.
- Ask the chatbot for outfit suggestions using wardrobe context.
- Visualize selected garments with a simple 2D overlay; AI image generation can be added later through the provider factory.

## Project structure and ownership

```text
wardrobe-app/
|
|- README.md                              # Shared project setup, status, and integration guide
|- requirements.txt                       # ML + lightweight FastAPI/chatbot dependencies
|- .env                                  # Local API keys only; ignored by Git
|
|- ml/                                    # [Umair] ML/CV pipeline
|  |- pipeline.py                         # process_wardrobe_upload() unified ML entry point
|  |- segmentation/
|  |  |- model.py                         # CLIPSeg and SAM2 model loading
|  |  |- inference.py                     # Segmentation, cutout creation, and PNG output
|  |  `- utils.py
|  |- classification/
|  |  |- model.py                         # FashionCLIP and color palette
|  |  `- inference.py                     # Metadata and dominant-color extraction
|  `- test_images/                        # Local test images (ignored by Git)
|
|- backend/
|  |- app/
|  |  |- main.py                          # [Mahad] FastAPI app and router mounting - pending
|  |  |- database/                        # [Mahad] MongoDB models/connection - pending
|  |  |- routes/
|  |  |  |- upload.py                     # [Mahad] Upload endpoint - pending
|  |  |  |- wardrobe.py                   # [Mahad] Wardrobe endpoints - pending
|  |  |  |- chatbot.py                    # [Abdulrehman] POST /chat router - ready to mount
|  |  |  `- visualization.py              # [Abdulrehman + Mahad] Visualization endpoint - pending
|  |  `- services/
|  |     |- segmentation_service.py       # [Mahad + Umair] ML bridge - pending
|  |     |- classification_service.py     # [Mahad + Umair] ML bridge - pending
|  |     |- chatbot_service.py            # [Abdulrehman] OpenRouter chatbot service - implemented
|  |     |- image_generation_service.py   # [Abdulrehman] Gemini/Qwen factory foundation - implemented
|  |     `- visualization_service.py      # [Abdulrehman] Visualization orchestration - pending
|  `- tests/
|     `- test_image_generation_service.py # [Abdulrehman] Factory tests
|
|- frontend/                              # [Ayesha] React/UI project - pending setup
`- docs/
   |- architecture.md                     # Chatbot/visualization MVP decisions
   `- api.md                              # [Mahad + team] API contract - pending
```

## Abdulrehman's completed work

### Chatbot foundation

- Added `POST /chat` in `backend/app/routes/chatbot.py`.
- Added `ChatbotService` in `backend/app/services/chatbot_service.py`.
- Uses OpenRouter with the local `OPENROUTER_API_KEY` and `LLM_MODEL` values.
- Uses temporary mock wardrobe data until the real wardrobe API is available.
- Creates a compact wardrobe-aware prompt using item ID, category, type, color, and tags.
- Handles missing settings, provider errors, empty messages, and unusable free-model replies.
- Validated with outfit suggestion, clothing-match, and wardrobe-list questions.

### Visualization foundation

- Documented the MVP fallback: a static body template with transparent segmented garment PNGs positioned by CSS.
- Added the supervisor-requested `ImageGenerator` abstraction and `ImageGenerationFactory`.
- Added Gemini and Qwen placeholder implementations. They currently return placeholder text; live API calls must be added after a provider is selected and its key is available.
- Added four unit tests covering model selection, case-insensitivity, unknown providers, and generation delegation.

## Local setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

For chatbot/backend work, install only the lightweight dependencies:

```powershell
python -m pip install fastapi uvicorn httpx python-dotenv
```

> Do not install the full ML requirements unless you are working on Umair's pipeline; those dependencies include large model packages.

Create a local `.env` file in the repository root:

```env
LLM_PROVIDER=openrouter
LLM_MODEL=openrouter/free
OPENROUTER_API_KEY=your_key_here
```

Never commit `.env` or API keys.

## Test the current chatbot route

The backend app is not mounted in `main.py` yet. Test the chatbot route directly:

```powershell
python -c "from fastapi import FastAPI; from fastapi.testclient import TestClient; from backend.app.routes.chatbot import router; app = FastAPI(); app.include_router(router); response = TestClient(app).post('/chat', json={'message': 'What should I wear today?'}); print(response.status_code); print(response.json())"
```

Expected result: `200` and a reply based only on the mock wardrobe items.

Test the image generation factory:

```powershell
python -m unittest backend.tests.test_image_generation_service -v
```

Expected result: four passing tests.

## Required integration contract

Mahad's wardrobe endpoint must expose the following fields so the chatbot and visualization can use real data:

```json
{
  "id": "wardrobe-item-id",
  "category": "shirt",
  "type": "t-shirt",
  "color": "black",
  "tags": ["casual", "solid"],
  "segmentation_url": "/uploads/item.png"
}
```

The final FastAPI app must mount the chatbot router:

```python
from backend.app.routes import chatbot

app.include_router(chatbot.router)
```

## Next integration order

1. Mahad creates and mounts the FastAPI app, upload flow, database, and wardrobe API.
2. Umair's ML pipeline returns segmented PNGs and metadata to the backend upload flow.
3. Abdulrehman replaces chatbot mock data with Mahad's real wardrobe records and adds a visualization endpoint.
4. Ayesha connects the frontend upload, wardrobe, chatbot, and visualization screens to the API.
5. The team runs end-to-end testing: upload -> classify -> wardrobe -> chatbot -> visualization.

## MVP boundaries

- The current visualization MVP is a 2D overlay, not a full virtual try-on system.
- Gemini/Qwen image generation is an optional enhancement and must retain the overlay fallback.
- No models are trained from scratch; the project uses pretrained models.
