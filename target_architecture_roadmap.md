# System Architecture & Implementation Roadmap

This document outlines the target architecture, database schemas, API flows, frontend structure, visualization pipelines, and phased implementation roadmap for the AI Wardrobe & Stylist Platform.

---

## 1. System Architecture Overview

```
                                  ┌───────────────────────┐
                                  │       FRONTEND        │
                                  │     React + Vite      │
                                  │                       │
                                  │ Dashboard             │
                                  │ Wardrobe              │
                                  │ AI Stylist            │
                                  │ Outfit Studio         │
                                  │ Profile               │
                                  └───────────┬───────────┘
                                              │
                                     Supabase Auth JWT
                                              │
                                              ▼
                                  ┌───────────────────────┐
                                  │       FASTAPI         │
                                  │      API SERVER       │
                                  └───────────┬───────────┘
                                              │
                 ┌────────────────────────────┼────────────────────────────┐
                 │                            │                            │
                 ▼                            ▼                            ▼
          Authentication               Wardrobe API                 Stylist API
                 │                            │                            │
                 │                            │                            │
                 ▼                            ▼                            ▼
          Supabase Auth                  MongoDB                     Retrieval
                                                                       │
                                                                       ▼
                                                                    Qdrant
                                                                       │
                                                                       ▼
                                                                  Groq LLM
                                                                       │
                                                                       ▼
                                                               Structured Outfit
                                                                       │
                                                                       ▼
                                                              Visualization API
                                                                       │
                                                                       ▼
                                                         ┌──────────────────────┐
                                                         │ Visualization Worker │
                                                         │                      │
                                                         │ IDM-VTON             │
                                                         │ Multi-Garment Model  │
                                                         └──────────────────────┘
```

---

## 2. Ingestion & Asynchronous Pipeline

### Ingestion Data Flow

```
                    User Upload
                         │
                         ▼
                  Supabase Storage
                         │
                         ▼
                  Ingestion Pipeline
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
        Segmentation            Metadata/Classify
          SAM2                     Model
             │                       │
             └───────────┬───────────┘
                         ▼
                  Individual Items
                         │
                         ▼
                    CLIP/Fashion
                     Embedding
                         │
                         ▼
                      Qdrant
                         │
                         ▼
                     MongoDB
```

### Asynchronous Queue Layer (Target State)

```
                         RabbitMQ
                            │
        ┌───────────────────┼────────────────────┐
        │                   │                    │
        ▼                   ▼                    ▼
 ingestion-worker    embedding-worker    visualization-worker
        │                   │                    │
        ▼                   ▼                    ▼
   SAM2/Classify          CLIP             VTON model
```

---

## 3. Implementation Phasing

### Phase 0: Architecture Cleanup & Baseline

**Goal:** Standardize file structure and eliminate duplicate packages to make the existing system predictable.

1. **Remove Duplicated ML Package Structure:**
   - Eliminate `backend/ml/`.
   - Consolidate all Machine Learning logic into a single root `ml/` directory:
     ```text
     ml/
     ├── pipeline.py
     ├── segmentation/
     └── classification/
     ```
   - Update `backend/app/ml_loader.py` to import directly from root `ml.pipeline`.

2. **Standardized Configuration Management:**
   - Centralize configuration management inside `backend/app/core/config.py` and `backend/app/core/security.py`.
   - Replace all scattered `os.getenv(...)` calls with a typed `Settings` object.

```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Supabase Configuration
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # MongoDB Configuration
    mongodb_uri: str
    mongodb_db_name: str

    # Qdrant Vector DB
    qdrant_url: str
    qdrant_api_key: str
    qdrant_collection: str = "wardrobe_items"

    # Groq LLM Infrastructure
    groq_api_key: str
    groq_model: str = "llama3-70b-8192"

    # Storage Buckets
    supabase_bucket: str = "wardrobe"

    # Backend Settings
    backend_base_url: str

    class Config:
        env_file = ".env"

settings = Settings()
```

---

### Phase 1: Managed Infrastructure Setup

Migrate infrastructure to dedicated services with clear separation of concerns:

| Infrastructure Service | Purpose | Key Parameters |
| :--- | :--- | :--- |
| **Supabase** | Authentication & Object Storage | `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` |
| **MongoDB** | Application State & Item Metadata | `MONGODB_URI`, `MONGODB_DB_NAME` |
| **Qdrant** | Vector Search & Similarity | `QDRANT_URL`, `QDRANT_API_KEY` |
| **Groq API** | LLM Stylist Inference Engine | `GROQ_API_KEY`, `GROQ_MODEL` |

#### Data Abstraction Architecture
The application components interface strictly with high-level services (e.g., `LLMService`, `VectorService`) rather than direct third-party SDK calls within route handlers.

---

### Phase 2: Authentication & Multi-Tenancy

Deprecate mock authentication and local storage auth in favor of verified Supabase JWT authentication.

```
Register/Login
   │
   ▼
Supabase Auth
   │
   ▼
JWT / Session Token Issued
   │
   ▼
Frontend Attached Header: `Authorization: Bearer <JWT>`
   │
   ▼
FastAPI Middleware
   │
   ▼
Validate Supabase JWT Signature & Expiry
   │
   ▼
Extract `user_id` -> Inject into `current_user.id` Context
```

* **Security Mandate:** All endpoints require authenticated `current_user.id` injection. Fallbacks such as `user_id = "default_user"` are strictly prohibited to enforce user isolation at the database level.

---

### Phase 3: Redesigned Data Model

#### MongoDB Schema (`wardrobe_items` collection)

```json
{
  "_id": "ObjectId('60c72b2f9b1d8b001f8e4e1a')",
  "user_id": "usr_987654321",
  "source": {
    "image_url": "https://<supabase-url>/storage/v1/object/public/wardrobe-originals/usr_987654321/up_12345.jpg",
    "storage_path": "wardrobe-originals/usr_987654321/up_12345.jpg"
  },
  "garment": {
    "category": "top",
    "type": "oxford shirt",
    "color": "white",
    "style": "formal",
    "season": "all-season",
    "pattern": "solid",
    "material": "cotton",
    "tags": ["business", "classic", "button-down"]
  },
  "segmentation": {
    "mask_url": "https://<supabase-url>/storage/v1/object/public/wardrobe-cutouts/usr_987654321/item_001_mask.png",
    "cutout_url": "https://<supabase-url>/storage/v1/object/public/wardrobe-cutouts/usr_987654321/item_001.png",
    "bbox": [120, 45, 450, 600]
  },
  "embedding": {
    "model": "fashion-clip-v1",
    "dimension": 512,
    "vector_id": "item_001"
  },
  "confidence": {
    "segmentation_score": 0.96,
    "classification_score": 0.92
  },
  "created_at": "2026-08-03T21:00:00Z",
  "updated_at": "2026-08-03T21:00:00Z"
}
```

#### Qdrant Vector Payload Schema

Vectors are stored exclusively inside Qdrant alongside search payload attributes:

```json
{
  "id": "item_001",
  "vector": [0.023, -0.041, 0.112, "..."],
  "payload": {
    "user_id": "usr_987654321",
    "category": "top",
    "type": "oxford shirt",
    "color": "white",
    "style": "formal",
    "season": "all-season"
  }
}
```

---

### Phase 4: Object Storage Architecture

Supabase Storage is organized into four distinct buckets structured by `{user_id}` for clean isolation:

```text
wardrobe-originals/
  └── {user_id}/
      └── {upload_id}.jpg

wardrobe-cutouts/
  └── {user_id}/
      └── {item_id}.png

body-photos/
  └── {user_id}/
      └── body.jpg

visualizations/
  └── {user_id}/
      └── {job_id}.png
```

---

### Phase 5: Multi-Garment Ingestion Pipeline

```
UPLOAD (Image with Multiple Garments)
   │
   ▼
Store Original Image -> `wardrobe-originals/{user_id}/{upload_id}.jpg`
   │
   ▼
Image Validation (Blur / Format / Dimensions Check)
   │
   ▼
Garment Detection & SAM2 Segmentation
   │
   ├── Segment Item 1 (e.g., White Shirt)
   ├── Segment Item 2 (e.g., Black Trousers)
   └── Segment Item N (e.g., Brown Shoes)
          │
          ▼
      Attribute Classification Engine
          │
          ▼
      Feature Extraction (Color, Style, Season, Material)
          │
          ▼
      Save Crop to `wardrobe-cutouts/{user_id}/{item_id}.png`
          │
          ▼
      Generate CLIP Embedding
          │
          ▼
      Index Vector & Payload in Qdrant Collection
          │
          ▼
      Write Metadata & References to MongoDB
```

---

### Phase 6: Abstracted Embedding Layer

To evaluate embedding models (e.g., standard OpenAI CLIP, FashionCLIP, SigLIP), the platform utilizes an abstract base interface:

```text
backend/app/services/embedding/
├── base.py
├── clip_service.py
└── model_registry.py
```

```python
# backend/app/services/embedding/base.py
from abc import ABC, abstractmethod
from typing import List
from PIL import Image

class BaseEmbeddingService(ABC):

    @abstractmethod
    def embed_image(self, image: Image.Image) -> List[float]:
        pass

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        pass
```

---

### Phase 7: Qdrant Vector Integration

```text
backend/app/services/vector/
├── qdrant_service.py
└── collections.py
```

Vector points are saved with exact references to the primary MongoDB `_id` and filtered directly on the indexed `user_id` attribute.

---

### Phase 8 & 9: Semantic RAG Retrieval Pipeline

Replaces raw context dump (`frontend` -> `all wardrobe items` -> `LLM`) with vector pre-filtering and structured retrieval.

#### Retrieval Flow

```
User Input Query ("What should I wear for a formal summer dinner?")
   │
   ▼
Query Processor
   │
   ▼
Text Embedding Engine (Generates Query Vector)
   │
   ▼
Qdrant Hybrid Search Execution
   ├─ HARD FILTER: user_id == current_user.id AND season == "summer"
   └─ SEMANTIC SEARCH: Vector Cosine Distance against query vector
   │
   ▼
Top-K Relevant Items Retrieved (e.g., Top 8 items)
   │
   ▼
Pass Filtered Context to Groq LLM
   │
   ▼
Structured JSON Response Generation
```

---

### Phase 10: Groq Stylist Service

```text
backend/app/services/stylist/
├── stylist_service.py
├── prompt_builder.py
├── schemas.py
└── retrieval.py
```

#### Structured LLM Payload (Pydantic Schema)

```python
from pydantic import BaseModel
from typing import Optional

class OutfitRecommendation(BaseModel):
    top_id: Optional[str] = None
    bottom_id: Optional[str] = None
    outerwear_id: Optional[str] = None
    shoes_id: Optional[str] = None

class StylistResponse(BaseModel):
    message: str
    outfit: OutfitRecommendation
```

#### Stylist Output Requirement

The Groq LLM is strictly constrained to standard JSON schema output selecting candidate IDs sourced exclusively from the retrieved Qdrant context:

```json
{
  "message": "For a formal summer dinner, I recommend pairing your crisp white Oxford shirt with lightweight black trousers and dark brown shoes.",
  "outfit": {
    "top": "item_001",
    "bottom": "item_002",
    "outerwear": null,
    "shoes": "item_003"
  }
}
```

---

### Phase 11: Outfit Engine Validation Layer

An intermediate validation engine is placed between Qdrant vector retrieval and Groq LLM processing to enforce physical garment slot logic and prevent invalid combinations (e.g., `shirt + shirt + shirt`).

```
Qdrant Vector DB
   │
   ▼
Candidate Items
   │
   ▼
Outfit Engine (Slot Categorization & Mapping)
   │
   ▼
Groq LLM Prompt Context
   │
   ▼
Validated Outfit Output
```

#### Slot Categorization Logic
* **`shirt` / `sweater` / `t-shirt`** $ightarrow$ `top`
* **`pants` / `trousers` / `shorts`** $ightarrow$ `bottom`
* **`shoes` / `boots` / `sneakers`** $ightarrow$ `shoes`
* **`jacket` / `coat` / `blazer`** $ightarrow$ `outerwear`

---

### Phase 12: Frontend Redesign Structure

#### File System Hierarchy

```text
frontend/src/
│
├── app/
│   ├── routes/
│   └── providers/
│
├── components/
│   ├── ui/
│   ├── wardrobe/
│   ├── outfit/
│   ├── stylist/
│   └── visualization/
│
├── pages/
│   ├── Landing/
│   ├── Auth/
│   ├── Dashboard/
│   ├── Wardrobe/
│   ├── Stylist/
│   ├── OutfitStudio/
│   └── Profile/
│
├── api/
│   ├── auth.js
│   ├── wardrobe.js
│   ├── stylist.js
│   └── visualization.js
│
├── hooks/
├── context/
├── lib/
├── utils/
└── styles/
```

#### Application Navigation Flow

```text
Landing Page
   ├── Hero Section
   ├── AI Stylist Demonstration
   ├── Digital Wardrobe Concept
   ├── How It Works Breakdown
   └── Login / Register CTAs
        │
        ▼
Dashboard
   ├── Personalized Greeting ("Good evening, Abdul")
   ├── Quick Prompt Entry ("What are you wearing today?")
   ├── Categorized Wardrobe Highlights ([ shirts ] [ pants ] [ shoes ] [ jackets ])
   └── Daily Outfit Recommendation Card -> [ Try On ]
```

---

### Phase 13: Wardrobe Interface UI

The central hub for item management, search, and manual selection.

```text
MY WARDROBE

[ Search wardrobe...                                ]

[ All ] [ Tops ] [ Bottoms ] [ Shoes ] [ Outerwear ]

┌─────────┐ ┌─────────┐ ┌─────────┐
│         │ │         │ │         │
│  Shirt  │ │  Shirt  │ │  Pants  │
│         │ │         │ │         │
└─────────┘ └─────────┘ └─────────┘

                         [ + Add Items ]
```

* Selecting items directly transitions context into the **Outfit Studio**.

---

### Phase 14: Outfit Studio

Visual studio workspace supporting single-item, multi-item, and full-outfit assembly.

```text
                OUTFIT STUDIO

      ┌──────────────────────────────┐
      │                              │
      │        PERSON CANVAS         │
      │                              │
      │      Complete Outfit         │
      │                              │
      └──────────────────────────────┘

  [ Shirt ]  [ Pants ]  [ Shoes ]  [ Jacket ]

             [ AI TRY-ON ]
```

---

### Phase 15: Visualization R&D Benchmarking

Visualization models are benchmarked across criteria rather than chosen based on static samples:

| Evaluation Metric | Description / Unit |
| :--- | :--- |
| **Single Garment Fidelity** | Visual similarity score |
| **Multi-Garment Support** | Boolean (Yes/No) + Capacity Count |
| **Layering Quality** | Visual overlap correctness |
| **Garment Identity Preservation** | Perceptual similarity score |
| **Person Identity Preservation** | Facial/Feature preservation score |
| **Body Preservation** | Body shape score |
| **Inference Latency** | Time in seconds |
| **VRAM Footprint** | Memory consumption (GB) |
| **Target Resolution** | Output dimensions (Pixels) |
| **Model Footprint** | Checkpoint disk size (GB) |
| **Local Inference Capability** | Boolean (Yes/No) |
| **License Type** | Commercial usability |
| **External API Dependencies** | Infrastructure dependencies (`None` / `Preferred`) |
| **Integration Complexity** | Scale (`Low` / `Medium` / `High`) |

---

### Phase 16: Visualization Abstraction Layer

Decouple API routes from underlying virtual try-on models:

```text
backend/app/services/visualization/
│
├── base.py
├── idm_vton.py
├── multi_garment.py
├── router.py
└── schemas.py
```

```python
# backend/app/services/visualization/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class TryOnModel(ABC):

    @abstractmethod
    async def generate(
        self,
        person_image_url: str,
        garment_urls: List[str]
    ) -> Dict[str, Any]:
        pass
```

```text
                    Visualization Engine
                           │
             ┌─────────────┴─────────────┐
             │                           │
       Single Garment               Multi-Garment
             │                           │
         IDM-VTON                 Selected Model
```

---

### Phase 17: Dual Preview Rendering Pipeline (2D Overlay + AI VTON)

Combines immediate client-side feedback with asynchronous realistic generation:

```text
Visualization Pipeline
│
├── Instant Preview Layer
│     └── 2D Canvas Overlay (~Instant Feedback)
│
└── AI Try-On Generation
      ├── Single Garment Pipeline  -> IDM-VTON
      └── Multi Garment Pipeline   -> Multi-Garment Model
```

---

### Phase 18: User Body Profile Model

#### MongoDB User Schema Extension

```json
{
  "_id": "usr_987654321",
  "email": "user@example.com",
  "body_photo_url": "https://<supabase-url>/storage/v1/object/public/body-photos/usr_987654321/primary.jpg",
  "preferences": {
    "fit": "regular",
    "primary_style": "casual"
  }
}
```

#### Supabase Body Storage Path
`body-photos/{user_id}/primary.jpg`

---

### Phase 19: Saved Outfits Persistence

#### MongoDB Schema (`outfits` collection)

```json
{
  "_id": "outfit_12345",
  "user_id": "usr_987654321",
  "name": "Formal Summer Dinner",
  "items": [
    "item_001",
    "item_002",
    "item_003"
  ],
  "generated_image_url": "https://<supabase-url>/storage/v1/object/public/visualizations/usr_987654321/job_999.png",
  "created_at": "2026-08-03T21:00:00Z"
}
```

---

### Phase 20: Persistent Stylist Chat History

#### MongoDB Collections (`chat_sessions` & `chat_messages`)

```json
// chat_sessions
{
  "_id": "session_abc",
  "user_id": "usr_987654321",
  "title": "Formal Dinner Styling",
  "created_at": "2026-08-03T21:00:00Z"
}

// chat_messages
{
  "_id": "msg_001",
  "session_id": "session_abc",
  "role": "assistant",
  "message": "Here is a formal combination for your dinner.",
  "retrieved_items": ["item_001", "item_002"],
  "recommended_outfit": {
    "top": "item_001",
    "bottom": "item_002"
  },
  "timestamp": "2026-08-03T21:00:05Z"
}
```

---

### Phase 21 & 22: Asynchronous Task Processing with RabbitMQ & Celery

#### Task Queues
1. `wardrobe.ingest`: Handles raw image segmentation and metadata extraction.
2. `embedding.generate`: Calculates vector embeddings for images and metadata.
3. `visualization.generate`: Executes GPU-intensive Virtual Try-On workflows.

#### Worker Directory Layout

```text
workers/
│
├── celery_app.py
│
├── tasks/
│   ├── ingestion.py
│   ├── embeddings.py
│   └── visualization.py
│
└── services/
```

---

### Phase 23: Job-Based Asynchronous Visualization Architecture

```text
Client                         FastAPI                       RabbitMQ/Celery                   GPU Worker
  │                              │                                  │                              │
  │─── POST /visualizations ────>│                                  │                              │
  │                              │─── Create Job (Status: Queued) ─>│                              │
  │<── Return Job ID (202) ──────│                                  │                              │
  │                              │                                  │─── Process Generation ──────>│
  │                              │                                  │                              │
  │─── GET /visualizations/{id}─>│                                  │                              │
  │<── Return Job Status ────────│                                  │                              │
```

---

### Phase 24: Final Backend Project Structure

```text
backend/
│
├── app/
│   │
│   ├── main.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── logging.py
│   │
│   ├── database/
│   │   ├── mongodb.py
│   │   ├── models.py
│   │   └── indexes.py
│   │
│   ├── auth/
│   │   ├── dependencies.py
│   │   └── schemas.py
│   │
│   ├── routes/
│   │   ├── auth.py
│   │   ├── wardrobe.py
│   │   ├── stylist.py
│   │   ├── outfits.py
│   │   ├── visualization.py
│   │   └── users.py
│   │
│   ├── services/
│   │   │
│   │   ├── wardrobe/
│   │   │   ├── service.py
│   │   │   └── ingestion.py
│   │   │
│   │   ├── embeddings/
│   │   │   ├── base.py
│   │   │   ├── clip.py
│   │   │   └── registry.py
│   │   │
│   │   ├── retrieval/
│   │   │   └── qdrant.py
│   │   │
│   │   ├── stylist/
│   │   │   ├── service.py
│   │   │   ├── prompts.py
│   │   │   └── schemas.py
│   │   │
│   │   ├── visualization/
│   │   │   ├── base.py
│   │   │   ├── idm_vton.py
│   │   │   ├── multi_garment.py
│   │   │   └── service.py
│   │   │
│   │   └── storage/
│   │       └── supabase.py
│   │
│   └── schemas/
│       ├── wardrobe.py
│       ├── outfit.py
│       ├── chat.py
│       └── visualization.py
│
├── workers/
│   ├── celery_app.py
│   └── tasks/
│       ├── ingestion.py
│       ├── embeddings.py
│       └── visualization.py
│
└── tests/
```

---

### Phase 25: ML Service Directory Structure

```text
ml/
│
├── segmentation/
│   ├── model.py
│   ├── inference.py
│   └── utils.py
│
├── classification/
│   ├── model.py
│   └── inference.py
│
├── embeddings/
│   ├── clip.py
│   └── benchmark.py
│
├── visualization/
│   ├── idm_vton/
│   ├── multi_garment/
│   └── benchmark.py
│
└── pipeline.py
```

---

### Phase 26: Environment Configuration Schema

```env
# =========================
# SUPABASE
# =========================
SUPABASE_URL=https://your-supabase-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

SUPABASE_BUCKET_WARDROBE=wardrobe-originals
SUPABASE_BUCKET_BODY=body-photos
SUPABASE_BUCKET_GENERATED=visualizations


# =========================
# MONGODB
# =========================
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net
MONGODB_DB_NAME=wardrobe_db


# =========================
# QDRANT
# =========================
QDRANT_URL=https://your-qdrant-cluster.qdrant.tech
QDRANT_API_KEY=your-qdrant-api-key
QDRANT_COLLECTION=wardrobe_embeddings


# =========================
# GROQ
# =========================
GROQ_API_KEY=gsk_your_groq_api_key
GROQ_MODEL=llama3-70b-8192


# =========================
# BACKEND
# =========================
BACKEND_BASE_URL=http://localhost:8000


# =========================
# CELERY & QUEUES
# =========================
RABBITMQ_URL=amqp://guest:guest@localhost:5672//
REDIS_URL=redis://localhost:6379/0
```

---

### Phase 27: Versioned REST API Specification

| Endpoint | Method | Response / Payload Summary |
| :--- | :--- | :--- |
| `/api/v1/uploads` | `POST` | Upload original image $ightarrow$ returns `{"upload_id": "...", "status": "processing"}` |
| `/api/v1/wardrobe` | `GET` | Retrieves authenticated user's indexed wardrobe items |
| `/api/v1/wardrobe/search` | `POST` | Executes semantic + metadata query against Qdrant |
| `/api/v1/stylist/chat` | `POST` | Interacts with RAG-enabled Groq Stylist |
| `/api/v1/outfits` | `POST` | Saves/retrieves explicit user outfit selections |
| `/api/v1/visualizations` | `POST` | Submits VTON generation job $ightarrow$ returns `{"job_id": "...", "status": "queued"}` |
| `/api/v1/visualizations/{job_id}`| `GET` | Polls status or retrieves final generated image URL |

---

### Phase 28: Testing Strategy

1. **Unit Testing:**
   - JWT Auth verification logic.
   - MongoDB Data Repositories & Qdrant Queries.
   - Outfit validation slot constraints.
   - Dynamic prompt generation templates.

2. **ML Pipeline Testing:**
   - Segmentation mask quality & accuracy.
   - Classification precision.
   - Vector embedding consistency across models.
   - VTON generation stability.

3. **Integration Testing:**
   - Image Ingestion Flow: `Upload` $ightarrow$ `Segmentation` $ightarrow$ `MongoDB` $ightarrow$ `Qdrant`.
   - Stylist RAG Pipeline: `Chat Query` $ightarrow$ `Qdrant Search` $ightarrow$ `Groq LLM` $ightarrow$ `Validated Outfit`.

4. **End-to-End E2E Validation:**
   - Complete User Cycle: `Register` $ightarrow$ `Upload Items` $ightarrow$ `Query AI Stylist` $ightarrow$ `Outfit Studio Preview` $ightarrow$ `Generate VTON` $ightarrow$ `Save Outfit`.

---

## 4. Strict Execution Sequence Matrix

Follow this sequential sequence to complete the implementation:

| Step | Module | Output / Milestone Target |
| :---: | :--- | :--- |
| **0** | Codebase Cleanup | Single `ml/` root directory and baseline architecture |
| **1** | Core Configuration | Typed `config.py` using single source of truth `.env` |
| **2** | Supabase Auth Integration | End-to-end Supabase JWT token verification middleware |
| **3** | Multi-Tenancy Injection | Mandatory `user_id` context injection on all backend routes |
| **4** | MongoDB Schema Upgrade | Document models matching revised `wardrobe_items` format |
| **5** | Storage Bucket Layout | Structured isolated buckets (`wardrobe-originals`, `wardrobe-cutouts`, etc.) |
| **6** | Ingestion Engine | Pipeline handling Segmentation (SAM2), Cutouts, and Metadata classification |
| **7** | Embedding Layer | Abstracted vector embedding service supporting CLIP/FashionCLIP |
| **8** | Qdrant Setup | Collection initialization and payload schema implementation |
| **9** | Vector Retrieval Logic | Strict user-isolated semantic search routines |
| **10**| Groq AI Stylist | Structured JSON RAG styling endpoint |
| **11**| Outfit Engine Validation | Garment slot validation matrix enforcing top/bottom/shoes integrity |
| **12**| Frontend UI Redesign | App router reorganization (`/pages`, `/components`, `/api`) |
| **13**| Wardrobe Workspace UI | Item cataloging, search UI, and filtering components |
| **14**| Outfit Studio Workspace | Interactive item composition workspace canvas |
| **15**| VTON R&D Benchmarking | Comparative evaluation matrix execution for VTON models |
| **16**| VTON Abstraction Layer | Plug-and-play `TryOnModel` interface implementation |
| **17**| Dual Preview Renderer | 2D immediate overlay canvas coupled with AI try-on triggers |
| **18**| Saved Outfits Logic | Persistence routines for created/generated outfits |
| **19**| Stylist Context Sessions | Persistent chat thread state in MongoDB |
| **20**| RabbitMQ Queue Setup | Message broker infrastructure setup |
| **21**| Celery ML Workers | Background execution workers for ML pipelines |
| **22**| Async Job Tracker | Non-blocking job polling endpoint architecture for VTON |
| **23**| Comprehensive Testing | Complete E2E, integration, and unit test execution |
| **24**| Production Deployment | Automated deployment pipeline execution |
