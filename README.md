# 👗 Wardrobe AI — Personal AI Stylist & Virtual Wardrobe Manager

> **An intelligent, full-stack wardrobe management platform** powered by computer vision, vector search, and a tool-calling LLM agent — turning your physical closet into a searchable, styleable, digital wardrobe.

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Environment Variables](#-environment-variables)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [ML Pipeline Setup](#ml-pipeline-setup)
  - [Modal (Serverless VTON) Setup](#modal-serverless-vton-setup)
- [Running the Project](#-running-the-project)
- [API Reference](#-api-reference)
- [How It Works — Deep Dive](#-how-it-works--deep-dive)
- [Testing](#-testing)
- [Contributing](#-contributing)

---

## 🌟 Overview

Wardrobe AI lets users digitize their entire wardrobe by uploading photos of their clothing. The platform automatically **segments** each garment from the background, **classifies** it (category, type, color, style, season, pattern), generates a **CLIP embedding** for semantic search, and stores everything in a vector database.

Users can then:
- **Chat with an AI Stylist** that recommends outfits from their own wardrobe, aware of the current weather at their location.
- **Try on outfits virtually** using the FASHN model hosted on Modal serverless GPU.
- **Visualize** their closet in a 2D overlay on a mannequin canvas.
- **Upload full outfits** via the Studio — the system segments each individual garment and stores them separately with relevant tags.
- **Save and browse** complete looks, with chat-session history persisted per user.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🤖 **AI Stylist (RAG Agent)** | Tool-calling LLM agent (OpenRouter / Groq) that retrieves items from Qdrant using FashionCLIP embeddings, checks live weather, and returns up to 3 complete outfit options |
| 🌤️ **Weather-Aware Recommendations** | Integrates Open-Meteo to derive deterministic dress-code constraints (temperature band, precipitation rules, wind) injected into the agent's context |
| 🪡 **Smart Garment Ingestion** | Uploads run through a full ML pipeline: segmentation (SAM2 + CLIPSeg), garment classification (CLIP zero-shot), color extraction (KMeans clustering), and FashionCLIP embedding generation |
| 📸 **Studio / Outfit Upload** | Users upload a full-outfit photo; each garment is segmented and stored independently with tags (category, type, color, style, season, pattern) |
| 👗 **Virtual Try-On (VTON)** | FASHN model hosted on Modal serverless GPU — user uploads a model photo, selects a garment, and receives a photorealistic try-on result |
| 🗂️ **2D Wardrobe Visualization** | Canvas-based overlay that layers transparent garment cutouts onto a mannequin silhouette for a full-outfit preview |
| 💾 **Saved Looks** | Complete outfit combinations saved and browsable per user, linked to chat sessions |
| 📊 **Activity Feed** | Chronological log of wardrobe events (adds, try-ons, style requests) |
| 🔐 **Auth** | Supabase-based JWT authentication with user-scoped data isolation |
| 🚀 **Async Ingestion Jobs** | `/ingest` endpoint processes uploads asynchronously with job-status polling, ideal for heavy ML workloads |
| 📈 **Benchmarking** | Built-in benchmark endpoint for measuring embedding/retrieval performance |

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                                │
│                    Next.js 16 Frontend (React 19)                   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTP / REST
┌──────────────────────────────▼──────────────────────────────────────┐
│                    FastAPI Backend (Python 3.11+)                   │
│                                                                     │
│  ┌─────────────┐  ┌───────────────┐  ┌────────────────────────┐   │
│  │  /upload    │  │  /chat        │  │  /visualization        │   │
│  │  /ingest    │  │  /sessions    │  │  /vton                 │   │
│  │  /wardrobe  │  │  /profile     │  │  /saved_looks          │   │
│  └──────┬──────┘  └───────┬───────┘  └────────────────────────┘   │
│         │                 │                                         │
│  ┌──────▼──────────────────▼────────────────────────────────────┐  │
│  │                       SERVICES LAYER                        │  │
│  │                                                              │  │
│  │  ML Pipeline          Stylist Agent        Weather Service   │  │
│  │  ┌──────────┐         ┌─────────────┐      ┌─────────────┐  │  │
│  │  │CLIPSeg + │         │ Tool-Calling│      │ Open-Meteo  │  │  │
│  │  │SAM2 (seg)│         │ LLM Agent   │      │ Geocode API │  │  │
│  │  │FashionCLIP│        │ (OpenRouter │      │ IP Fallback │  │  │
│  │  │ (embed)  │         │ / Groq)     │      └─────────────┘  │  │
│  │  │ KMeans   │         │             │                        │  │
│  │  │ (color)  │         │ Tool: search│                        │  │
│  │  └──────────┘         │ Tool: weather                        │  │
│  │                       └─────────────┘                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
└──────────┬──────────────────┬──────────────────┬──────────────────-┘
           │                  │                   │
   ┌───────▼──────┐  ┌───────▼──────┐   ┌────────▼───────┐
   │   MongoDB    │  │    Qdrant    │   │   Supabase     │
   │ (wardrobe,   │  │ (FashionCLIP │   │ (Auth + Image  │
   │  chat, users)│  │  vectors)    │   │  Storage)      │
   └──────────────┘  └──────────────┘   └────────────────┘
                                                │
                                       ┌────────▼────────┐
                                       │  Modal.com GPU  │
                                       │ FASHN VTON      │
                                       │ (Virtual Try-On)│
                                       └─────────────────┘
```

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| **FastAPI** | Async REST API framework |
| **Python 3.11+** | Core language |
| **Motor** (async PyMongo) | MongoDB async driver |
| **Qdrant** | Vector database for semantic wardrobe search |
| **Supabase** | Auth (JWT) + cloud image storage |

### ML / AI
| Technology | Purpose |
|---|---|
| **SAM2** | Segment Anything Model v2 — high-quality mask generation |
| **CLIPSeg** | CLIP-based text-guided segmentation for garment isolation |
| **FashionCLIP** | Multi-modal clothing embeddings (512-dim) |
| **OpenCLIP / CLIP** | Zero-shot garment classification |
| **KMeans Clustering** | Dominant color extraction (saturation-weighted) |
| **FASHN** | Photorealistic Virtual Try-On model, served via Modal serverless GPU |
| **Transformers / PyTorch** | Model inference runtime |

### Frontend
| Technology | Purpose |
|---|---|
| **Next.js 16** | React framework with App Router |
| **React 19** | UI components |
| **TypeScript** | Type safety |
| **TailwindCSS** | Styling |
| **Framer Motion** | Animations |
| **Supabase JS** | Client-side auth & storage |

### Infrastructure
| Service | Purpose |
|---|---|
| **MongoDB Atlas** | Primary document database |
| **Qdrant Cloud** | Managed vector database |
| **Supabase** | Auth + file storage |
| **Modal.com** | Serverless GPU for Virtual Try-On |
| **Open-Meteo** | Free weather & geocoding API |
| **OpenRouter / Groq** | LLM providers (GPT-3.5, LLaMA 3) |

---

## 📁 Project Structure

```
wardrobe-app/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, router registration, startup
│   │   ├── ml_loader.py             # ML model warm-up on startup
│   │   ├── auth/                    # Supabase JWT dependency injection
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic settings (reads .env)
│   │   │   └── security.py          # UserContext model
│   │   ├── database/
│   │   │   ├── mongodb.py           # Motor client + collection handles
│   │   │   └── models.py            # Pydantic DB schemas (Phase 3 nested)
│   │   ├── routes/
│   │   │   ├── upload.py            # POST /upload — sync ML + Qdrant ingest
│   │   │   ├── ingest.py            # POST /ingest — async job-based ingest
│   │   │   ├── wardrobe.py          # GET/PATCH/DELETE /wardrobe
│   │   │   ├── chatbot.py           # POST /chat — stylist agent endpoint
│   │   │   ├── visualization.py     # Wardrobe 2D canvas
│   │   │   ├── saved_looks.py       # Saved outfit management
│   │   │   ├── profile.py           # User profile CRUD
│   │   │   ├── activity.py          # Activity feed
│   │   │   └── benchmark.py         # Performance benchmarking
│   │   └── services/
│   │       ├── agent/
│   │       │   ├── agent_service.py # Tool-calling LLM agent orchestrator
│   │       │   └── tools.py         # Tool definitions: search_wardrobe, get_weather
│   │       ├── embedding/           # FashionCLIP embedding service + registry
│   │       ├── retrieval/           # Qdrant similarity search
│   │       ├── stylist/             # Outfit scoring and schema
│   │       ├── vector/              # Qdrant upsert/query wrappers
│   │       ├── visualization/       # 2D mannequin overlay service
│   │       ├── storage/             # Supabase upload helpers
│   │       ├── image_generation_service.py  # VTON service (Modal)
│   │       ├── visualization_service.py     # Outfit canvas renderer
│   │       └── weather/
│   │           └── weather_service.py       # Open-Meteo + dress-code derivation
│   ├── scripts/                     # DB utility scripts
│   ├── tests/                       # pytest test suite
│   └── clear_db.py                  # Dev utility: wipe MongoDB + Qdrant
├── frontend/
│   ├── app/                         # Next.js App Router pages
│   ├── components/                  # Reusable React components
│   ├── context/                     # React context (auth, wardrobe state)
│   ├── hooks/                       # Custom React hooks
│   ├── lib/                         # API client, utility functions
│   ├── types/                       # TypeScript type definitions
│   └── public/                      # Static assets
├── ml/
│   ├── pipeline.py                  # End-to-end ML pipeline runner
│   ├── segmentation/                # CLIPSeg + SAM2 segmentation module
│   └── classification/              # CLIP zero-shot classification
├── modal_infrastructure/           # Modal deployment scripts for VTON
├── docs/                            # Additional documentation
├── .env                             # Environment variables (see below)
├── requirements.txt                 # Python dependencies
└── pytest.ini                       # Test configuration
```

---

## 🔑 Environment Variables

Create a `.env` file in `wardrobe-app/` (root of the monorepo) with the following:

```env
# ── LLM Provider ────────────────────────────────────────────────────
# Choose one: groq | openrouter | openai
LLM_PROVIDER=openrouter
LLM_MODEL=openai/gpt-3.5-turbo

# Groq (fast, free tier available) — good for llama-3.1-8b-instant
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant

# OpenRouter (access to many models including GPT-4o, Claude, Llama)
OPENROUTER_API_KEY=your_openrouter_api_key

# ── Supabase (Auth + Storage) ────────────────────────────────────────
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# ── MongoDB Atlas ────────────────────────────────────────────────────
MONGODB_URI=mongodb+srv://<user>:<password>@cluster0.xxxx.mongodb.net/
MONGODB_DB_NAME=wardrobe_db

# ── Qdrant (Vector DB) ───────────────────────────────────────────────
QDRANT_URL=https://your-cluster-id.us-east-1-1.aws.cloud.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key

# ── HuggingFace (for SAM2 / CLIPSeg / FashionCLIP model downloads) ──
HF_TOKEN=your_huggingface_token

# ── Virtual Try-On (Modal) ───────────────────────────────────────────
OOTD_PROVIDER=modal
MODAL_OOTD_ENDPOINT=https://your-modal-app-endpoint.modal.run
```

Frontend environment variables go in `frontend/.env.local`:

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🚀 Getting Started

### Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |
| npm / bun | Latest |
| CUDA GPU *(optional)* | For local ML inference |
| Git | Latest |

You will also need accounts for:
- [Supabase](https://supabase.com) — Auth + image storage
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) — Document database
- [Qdrant Cloud](https://cloud.qdrant.io) — Vector database
- [OpenRouter](https://openrouter.ai) or [Groq](https://groq.com) — LLM API
- [Modal](https://modal.com) — Serverless GPU for Virtual Try-On *(optional)*
- [HuggingFace](https://huggingface.co) — Model downloads (SAM2, CLIPSeg, FashionCLIP)

---

### Backend Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd wardrobe-app

# 2. Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. (Optional) Install PyTorch with CUDA for GPU acceleration
#    Visit https://pytorch.org/get-started/locally/ for the correct command.
#    Example for CUDA 12.1:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# 5. Copy and fill in environment variables
cp .env.example .env
# Edit .env with your API keys (see Environment Variables section above)
```

---

### Frontend Setup

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies (uses bun for faster installs, npm works too)
npm install
# or
bun install

# Create frontend environment file
cp .env.example .env.local
# Edit .env.local with your Supabase credentials and backend URL
```

---

### ML Pipeline Setup

The ML pipeline models are downloaded automatically on first use via HuggingFace. Ensure `HF_TOKEN` is set in `.env`.

Models used:
- **CLIPSeg** — `CIDAS/clipseg-rd64-refined` (text-guided segmentation, ~230MB)
- **SAM2** — `facebook/sam2-hiera-tiny` (mask refinement, ~155MB)
- **FashionCLIP** — `patrickjohncyh/fashion-clip` (embeddings, ~600MB)

To pre-download models manually:

```bash
python -c "
from transformers import CLIPSegProcessor, CLIPSegForImageSegmentation
CLIPSegProcessor.from_pretrained('CIDAS/clipseg-rd64-refined')
CLIPSegForImageSegmentation.from_pretrained('CIDAS/clipseg-rd64-refined')
print('CLIPSeg downloaded.')
"
```

---

### Modal (Serverless VTON) Setup

If you want to run Virtual Try-On locally via Modal instead of using a pre-deployed endpoint:

```bash
# Install Modal CLI
pip install modal

# Authenticate
modal token new

# Deploy the VTON endpoint
cd modal_infrastructure
modal deploy app.py

# Copy the generated endpoint URL into .env as MODAL_OOTD_ENDPOINT
```

---

## ▶️ Running the Project

### 1. Start the Backend

```bash
# From the wardrobe-app/ directory, with the venv activated
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`  
Interactive API docs: `http://localhost:8000/docs`  
Health check: `http://localhost:8000/health`

### 2. Start the Frontend

```bash
# In a new terminal, from the frontend/ directory
cd frontend
npm run dev
# or
bun run dev
```

The frontend will be available at: `http://localhost:3000`

### 3. (Development) Clear the Database

To wipe all wardrobe items from MongoDB and Qdrant during development:

```bash
cd backend
python clear_db.py
```

---

## 📡 API Reference

All routes are available at both `/` and `/api/v1/` prefixes.

| Method | Route | Description |
|---|---|---|
| `GET` | `/health` | Service health + Qdrant status |
| `POST` | `/upload/` | Upload a garment image (sync ML pipeline) |
| `POST` | `/ingest` | Upload garment image (async job-based) |
| `GET` | `/ingest/{job_id}` | Poll async ingestion job status |
| `GET` | `/wardrobe` | List all wardrobe items for the user |
| `PATCH` | `/wardrobe/{id}` | Update garment metadata |
| `DELETE` | `/wardrobe/{id}` | Delete a garment |
| `POST` | `/chat` | Send a message to the AI Stylist agent |
| `GET` | `/chat/sessions` | List all chat sessions |
| `GET` | `/chat/sessions/{id}` | Fetch chat history for a session |
| `DELETE` | `/chat/sessions/{id}` | Delete a chat session |
| `GET` | `/visualization` | Get wardrobe canvas data |
| `POST` | `/visualization/vton` | Trigger Virtual Try-On |
| `GET` | `/saved_looks` | List saved outfits |
| `POST` | `/saved_looks` | Save a new outfit |
| `DELETE` | `/saved_looks/{id}` | Delete a saved look |
| `GET` | `/profile` | Get user profile |
| `PATCH` | `/profile` | Update user profile |
| `GET` | `/activity` | Get activity feed |
| `GET` | `/benchmark` | Run embedding benchmark |
| `GET` | `/ml/outputs/{filename}` | Serve ML pipeline output files |

---

## 🔬 How It Works — Deep Dive

### 1. Garment Ingestion Pipeline

When a user uploads an image:

```
Photo → CLIPSeg (text-guided mask) + SAM2 (mask refinement) → Transparent garment cutout
      → FashionCLIP (zero-shot classification) → category, type, style, season, pattern
      → KMeans saturation-weighted clustering → dominant color
      → FashionCLIP embed → 512-dim vector
      → Supabase Storage (original + cutout URLs)
      → MongoDB (garment document with nested schema)
      → Qdrant (vector upsert with garment metadata payload)
```

Each upload can produce **multiple garment documents** if the photo contains several items (e.g., a full outfit).

### 2. AI Stylist — RAG Tool-Calling Agent

The stylist is a **tool-calling LLM agent**, not a simple prompt-with-context:

```
User message
    ↓
Agent receives: user query + conversation history + user profile
    ↓
LLM decides which tools to call:
  • search_wardrobe(query, filters) → FashionCLIP embed query → Qdrant similarity search → top-N items
  • get_weather(city, lat, lon) → Open-Meteo → deterministic DressCode constraints
    ↓
LLM receives tool results + generates outfit recommendations
    ↓
Response: up to 3 complete OutfitOption objects (each with item IDs + styling notes)
    ↓
Saved to MongoDB chat_messages collection with outfits embedded
```

The weather service is specially designed to convert raw conditions into **explicit clothing constraints** (e.g., "MUST prioritise: waterproof jacket; MUST NOT recommend: sandals") rather than raw numbers — ensuring the LLM cannot hallucinate unsuitable recommendations.

### 3. Virtual Try-On (VTON)

```
User photo (model) + Selected garment cutout URL
    → POST to Modal endpoint (FASHN)
    → GPU inference (typically 15–30s)
    → Returns generated try-on image URL
```

The Modal endpoint uses **FASHN**, a high-fidelity virtual try-on model. It is hosted serverlessly on Modal GPU — cold start is handled via pre-warmed containers.

### 4. Vector Search (Semantic Retrieval)

Qdrant stores one 512-dim FashionCLIP vector per garment, filtered by `user_id`. When the stylist searches:
1. The query text (e.g., "cozy winter jacket") is embedded by FashionCLIP.
2. Qdrant performs approximate nearest-neighbour (ANN) search within the user's items.
3. Results are ranked by cosine similarity and returned with metadata.

---

## 🧪 Testing

```bash
# Run the full test suite
cd backend
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_upload.py -v

# Run tests with coverage
pytest --cov=app tests/
```

Test configuration is in `pytest.ini`.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes and write tests
4. Run the test suite: `pytest`
5. Commit your changes: `git commit -m "feat: add your feature"`
6. Push and open a Pull Request

---

## 📄 License

This project was developed as part of a NETSOL Technologies internship program by:

- **Muhammad Umair Ashraf**
- **Mahad Abid**
- **Abdul Rehman Ali**
- **Ayesha Younus**

---

*Built with ❤️ using FastAPI, Next.js, PyTorch, FashionCLIP, Qdrant, and Modal*
