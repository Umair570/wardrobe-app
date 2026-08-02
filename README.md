# 👗 AI Wardrobe Assistant

An AI-powered digital wardrobe application: upload clothing photos, automatically segment and classify garments into digital wardrobe slots, interact with a wardrobe-aware AI Stylist chatbot, and preview outfit combinations using **Interactive 2D Body Overlays** or **Photorealistic Gemini AI Virtual Try-On**.

---

## ✨ Features & Architecture

### 🤖 1. AI Stylist Chatbot (`POST /chat`)
- **Wardrobe-Aware Recommendations**: Queries your live MongoDB wardrobe items and generates personalized outfit recommendations tailored to weather, occasion, or style.
- **Structured Output**: Returns structured response payloads (`reply`, `recommended_items[]`, `source`) without exposing raw database IDs to the user interface.
- **Interactive Chat Buttons**: Each recommended outfit card includes individual **Visualize** buttons as well as a **Visualize Full Outfit** button.
- **Intelligent Query Relevance Matching**: Uses smart keyword scoring (matching colors, garment types, styles, and seasons) when operating in fallback mode.
- **Source Tracking**: Surfaces whether a response originated directly from the LLM (`source: "llm"`) or local fallback logic (`source: "fallback"`).

---

### 📐 2. Interactive 2D Layering Canvas & Body Photo Template (`POST /visualization`)
- **Category Slot Mapping**: Automatically maps items into standard clothing slots (`top`, `bottom`, `shoes`, `outerwear`) with designated coordinate positioning and z-indexing.
- **User Body Photo Template**: Upload a full-body photo of yourself to render as the canvas backdrop, allowing you to preview clothes directly on your real body shape.
- **Interactive Drag Controls**: Drag and adjust garment cutouts freely over the silhouette or your photo to inspect fit using `framer-motion`.
- **Color Harmony Detector**: Automated palette analysis displaying outfit color tones and harmony scores.
- **Layout Reset**: Reset layout controls to return garments to default backend positions instantly.

---

### ✨ 3. Gemini AI Virtual Try-On (`image_generation_service.py`)
- **Multimodal Image Try-On**: Connected to Google Gemini API (`gemini-2.5-flash-image` / `gemini-1.5-flash`) for AI virtual try-on.
- **Image-to-Image Conditioning**: Combines the user's base64 body photo with selected garment PNG cutouts to synthesize photorealistic full-body AI model try-on photos.
- **Dual Mode Switcher**: Seamlessly toggle between **`📸 2D Canvas Overlay`** (instant interactive canvas) and **`✨ Gemini AI Model Try-On`** (photorealistic AI photo generation).

---

### 🛍️ 4. Wardrobe Gallery & Outfit Builder
- **Slot-Based Outfit Builder**: Floating interactive bar on the Wardrobe page allowing users to select 1 item per category slot (`Top`, `Bottom`, `Shoes`, `Outerwear`) and visualize the full outfit with one click.
- **Resilient Image Serving**: Dynamic static file handler (`/ml/outputs/{filename:path}`) searching across candidate directories to guarantee image cutouts load cleanly without 404s.
- **Database Safety Guards**: Robust exception handling skipping malformed MongoDB documents so gallery rendering never fails.

---

## 🚀 Getting Started

### 1. Environment Setup

Create `.env` in the **repository root** (`wardrobe-app/.env`):

```env
# MongoDB Database
MONGODB_URI=mongodb+srv://...
MONGODB_DB_NAME=wardrobe_db
UPLOAD_DIR=uploads

# AI Stylist Chatbot (OpenRouter)
LLM_PROVIDER=openrouter
LLM_MODEL=meta-llama/llama-3.1-8b-instruct:free
OPENROUTER_API_KEY=your_openrouter_api_key

# Gemini AI Virtual Try-On
GEMINI_API_KEY=your_google_gemini_api_key
```

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

---

### 2. Backend Installation & Server Run

Open PowerShell Terminal 1:

```powershell
# Navigate to backend directory
cd backend

# Create & activate virtual environment (optional)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r ..\requirements.txt

# Run FastAPI server on port 8000
python -m uvicorn app.main:app --reload --port 8000
```

- **Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

### 3. Frontend Installation & Dev Server Run

Open PowerShell Terminal 2:

```powershell
# Navigate to frontend directory
cd frontend

# Install packages
npm install

# Start Vite development server
npm run dev
```

- **Web Application UI**: [http://localhost:5173](http://localhost:5173)

---

## 📡 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/upload/` | Upload clothing image → segment cutouts, classify, save to MongoDB |
| `GET` | `/wardrobe/` | List all digital wardrobe items |
| `GET` | `/wardrobe/{id}` | Retrieve single wardrobe item details |
| `DELETE` | `/wardrobe/{id}` | Delete item from digital wardrobe |
| `POST` | `/chat` | Send prompt to AI Stylist → get outfit recommendation + item cards |
| `POST` | `/visualization` | Generate 2D overlay positions or Gemini AI virtual try-on |
| `GET` | `/health` | Health check endpoint |

---

### Request / Response Examples

#### `POST /chat`
```json
// Request
{
  "message": "What matches my blue jeans?",
  "user_id": "default_user"
}

// Response
{
  "reply": "Great choice! Here is a stylish match for your denim/blue pieces: Baby Blue shirt, Charcoal denim shorts, and Taupe sneakers.",
  "recommended_items": [
    {
      "id": "66ad1234...",
      "label": "Baby Blue Shirt",
      "category": "shirt",
      "slot": "top",
      "color": "baby blue",
      "type": "shirt"
    }
  ],
  "source": "llm"
}
```

#### `POST /visualization`
```json
// Request
{
  "item_ids": ["66ad1234...", "66ad5678..."],
  "mode": "overlay",
  "user_body_photo_url": "data:image/jpeg;base64,..."
}

// Response
{
  "mode": "overlay",
  "items": [
    {
      "id": "66ad1234...",
      "category": "top",
      "type": "shirt",
      "image_url": "http://localhost:8000/ml/outputs/item_0.png",
      "position": { "x": 50, "y": 30, "width": 70, "height": 30 },
      "z_index": 3
    }
  ],
  "ai_image_url": null
}
```

---

## 📂 Project Structure

```text
wardrobe-app/
├── ml/                                 # Computer Vision & ML Pipeline (Segmentation + Classification)
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI app entrypoint, CORS, static routes
│   │   ├── ml_loader.py                # Lazy ML model loader
│   │   ├── database/                   # MongoDB connection & Pydantic schemas
│   │   ├── routes/
│   │   │   ├── upload.py               # POST /upload/
│   │   │   ├── wardrobe.py             # GET, DELETE /wardrobe/
│   │   │   ├── chatbot.py              # POST /chat
│   │   │   └── visualization.py        # POST /visualization
│   │   └── services/
│   │       ├── chatbot_service.py      # LLM Chatbot Service & Fallback Outfit Picker
│   │       ├── visualization_service.py# 2D Canvas Layout Generator & Body Photo Transformer
│   │       └── image_generation_service.py # Gemini Multimodal Virtual Try-On Service
│   └── tests/                          # Backend Unit Tests (unittest)
├── frontend/
│   ├── src/
│   │   ├── api/                        # API client functions (chatbotApi, stylistApi, wardrobeApi)
│   │   ├── components/                 # ChatbotDock, ChatOutfitSuggestions, UserBodyPhotoUpload
│   │   ├── pages/                      # WardrobePage, StylistPage, OutfitVisualizationPage, HomePage
│   │   └── utils/                      # outfitSlots.js (slot mapping utilities)
│   └── .env
└── README.md
```

---

## 🧪 Automated Unit Tests

Run all backend unit tests from the repository root:

```powershell
python -m unittest discover -s backend/tests -p "test_*.py" -v
```

To run individual test suites:

```powershell
# Chatbot test suite
python -m unittest backend.tests.test_chatbot_service -v

# Visualization test suite
python -m unittest backend.tests.test_visualization_service -v

# Image generation test suite
python -m unittest backend.tests.test_image_generation_service -v
```
