# AI Wardrobe Assistant — MVP

An AI-powered wardrobe app: upload clothing photos, auto-segment and classify items, browse a digital wardrobe, get outfit suggestions from a wardrobe-aware chatbot, and preview garments on a body template (2D overlay).

**Team:** Umair (ML) · Mahad (Backend/DB) · Ayesha (Frontend) · Abdulrehman (Chatbot + Visualization)

---

## Current status (Aug 2026)

| Area | Owner | Status | JIRA |
| --- | --- | --- | --- |
| Segmentation + classification | Umair | Done | WMVP-6 |
| Backend (FastAPI) + MongoDB | Mahad | Done | WMVP-7 |
| Frontend (upload, wardrobe, UI) | Ayesha | Done | WMVP-8 |
| Chatbot + visualization integration | Abdulrehman | **Done** | **WMVP-20** |
| Refine chatbot + visualization | Abdulrehman | **Done** | **WMVP-21** |


### End-to-end flow (working)

```
Upload photo → ML segmentation + classification → MongoDB
      ↓
Wardrobe gallery (slot-based outfit builder)
      ↓
Chatbot (POST /chat) — complete outfit suggestions + per-item visualize
      ↓
Visualization (POST /visualization) — 2D garment overlay on mannequin
```

---

## WMVP-20 — Complete

All phases delivered:

| Phase | Deliverable |
| --- | --- |
| 1 | `ChatbotService` fetches live items from MongoDB |
| 2 | Frontend wired to `POST /chat` (chat dock + stylist page) |
| 3 | `VisualizationService` + `POST /visualization` overlay contract |
| 4 | `OutfitVisualizationPage` renders positioned PNG cutouts |
| 5 | Unit tests in `backend/tests/test_chatbot_service.py` and `test_visualization_service.py` |

### Chatbot features

- Wardrobe-aware replies from MongoDB (fallback to local outfit picker if OpenRouter is unavailable)
- Structured response: `{ reply, recommended_items[] }` — **no raw MongoDB IDs shown to users**
- Complete outfit picking: one top + one bottom + shoes (deduped by slot)
- Per-item **Visualize** buttons + **Visualize full outfit** in chat UI

### Visualization features

- 2D overlay mode (`mode: "overlay"`) with `position` + `z_index` per garment
- Slot mapping: `shirt/sweater → top`, `pants/shorts/skirt → bottom`, `shoes → shoes`, `jacket → outerwear`
- Wardrobe outfit builder: select one item per slot → **Visualize Outfit**
- Bags/accessories are stored but not visualizable (by design)

---

## WMVP-21 — When to start

**You can start WMVP-21 now.** WMVP-20 is marked Done in JIRA; WMVP-21 is scheduled from early August and is the natural next step.

### WMVP-21 scope (from JIRA)

- Improve overlay positioning accuracy on the mannequin
- Enhance chatbot response quality (LLM prompts, edge cases)
- Harden fallback scenarios (backend offline, empty wardrobe, misclassified items)
- Fix issues found during end-to-end demo testing
- Optional stretch: wire `image_generation_service.py` (Gemini/Qwen) — not required for MVP sign-off

### Known issues to address in WMVP-21

| Issue | Area |
| --- | --- |
| Color mislabels (e.g. black shirt → "tan", white shoes → "khaki") | ML classifier (Umair) |
| Misclassified items (bag/skirt from clothing photo) | ML segmentation/classifier |
| 2D overlay looks basic / cutouts show hangers | Segmentation quality + CSS positioning |
| Gemini/Qwen image gen is stub-only | `image_generation_service.py` (optional) |

---

## Quick start

### 1. Environment

Create `.env` in the **repo root** (`wardrobe-app/.env`):

```env
# MongoDB (Mahad)
MONGODB_URI=mongodb+srv://...
MONGODB_DB_NAME=wardrobe_app
UPLOAD_DIR=uploads

# Chatbot (Abdulrehman) — optional; local outfit picker works without these
LLM_PROVIDER=openrouter
LLM_MODEL=openrouter/free
OPENROUTER_API_KEY=your_key_here
```

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

Never commit `.env` files or API keys.

### 2. Backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# From repo root — serves on http://localhost:8000
uvicorn backend.app.main:app --reload --app-dir .
```

Swagger UI: http://localhost:8000/docs

### 3. Frontend

```powershell
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

---

## API reference

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/upload/` | Upload image → segment, classify, save to MongoDB |
| `GET` | `/wardrobe/` | List all wardrobe items |
| `GET` | `/wardrobe/{id}` | Single item |
| `DELETE` | `/wardrobe/{id}` | Remove item |
| `POST` | `/chat` | Wardrobe-aware outfit suggestion |
| `POST` | `/visualization` | 2D overlay layout for selected item IDs |
| `GET` | `/health` | Health check |

### `POST /chat` request / response

```json
// Request
{ "message": "What should I wear today?", "user_id": "default_user" }

// Response
{
  "reply": "Here's a complete look from your wardrobe: Tan T-shirt, Charcoal Shorts, and White Sneakers.",
  "recommended_items": [
    { "id": "...", "label": "Tan T-shirt", "slot": "top", "category": "shirt", "color": "tan", "type": "t-shirt" }
  ]
}
```

### `POST /visualization` request / response

```json
// Request
{ "item_ids": ["66ad1234...", "66ad5678..."], "mode": "overlay" }

// Response
{
  "mode": "overlay",
  "items": [
    {
      "id": "66ad1234...",
      "category": "top",
      "type": "t-shirt",
      "image_url": "/ml/outputs/item_0.png",
      "position": { "x": 50, "y": 30, "width": 72, "height": 28 },
      "z_index": 3
    }
  ]
}
```

Static files: `/uploads` and `/ml/outputs` are mounted in `backend/app/main.py`.

---

## Demo script (acceptance test)

1. **Upload** — POST a clothing photo via Upload page or `/upload/`
2. **Wardrobe** — confirm item appears with segmentation PNG
3. **Outfit builder** — select top + bottom + shoes → **Visualize Outfit**
4. **Chatbot** — ask *"What should I wear today?"* → verify item cards with individual Visualize buttons
5. **Single item** — click Visualize on one item → only that garment on mannequin

---

## Tests

```powershell
# All backend tests
python -m unittest discover -s backend/tests -p "test_*.py" -v

# Chatbot only
python -m unittest backend.tests.test_chatbot_service -v

# Visualization only
python -m unittest backend.tests.test_visualization_service -v

# Image generation factory (stubs)
python -m unittest backend.tests.test_image_generation_service -v
```

---

## Project structure

```text
wardrobe-app/
├── ml/                          # [Umair] CLIPSeg + SAM2 + FashionCLIP pipeline
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, static mounts
│   │   ├── ml_loader.py         # Lazy ML import
│   │   ├── database/            # MongoDB connection + models
│   │   ├── routes/
│   │   │   ├── upload.py
│   │   │   ├── wardrobe.py
│   │   │   ├── chatbot.py       # POST /chat
│   │   │   └── visualization.py # POST /visualization
│   │   └── services/
│   │       ├── chatbot_service.py
│   │       ├── visualization_service.py
│   │       └── image_generation_service.py  # Gemini/Qwen stubs (WMVP-21+)
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── api/                 # chatbotApi, wardrobeApi, stylistApi
│   │   ├── components/          # ChatbotDock, ChatOutfitSuggestions
│   │   ├── pages/               # Wardrobe, Stylist, OutfitVisualization
│   │   └── utils/outfitSlots.js # Category → slot mapping
│   └── .env
└── docs/architecture.md
```

---

## MVP boundaries (PRD)

| In scope | Out of scope |
| --- | --- |
| Upload, segment, classify, store | Photorealistic virtual try-on |
| Wardrobe hanger/gallery view | Multi-user social features |
| 2D body-template overlay | Outfit history / wear analytics |
| Wardrobe-aware chatbot | Custom ML model training |
| Error handling for bad uploads | Native mobile app |

### AI image generation (optional, post-MVP)

`image_generation_service.py` has a Gemini/Qwen factory pattern but **returns placeholders only** — not wired to the visualization route. To improve visuals later:

- **Gemini** — free tier on [Google AI Studio](https://aistudio.google.com) (daily limits)
- **Qwen** — DashScope free trial, then paid
- **2D overlay** remains the required fallback per PRD

---

## User identity (MVP policy)

If no auth token is sent, the app uses `user_id: "default_user"` and queries the global wardrobe collection. Post-MVP: JWT/Supabase session will scope items per user.
