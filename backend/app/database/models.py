"""
Pydantic data models for the wardrobe platform.

Matches the Phase 3 MongoDB schema defined in target_architecture_roadmap.md.
Old fields (source_image, segmentation_path, area_ratio, confidence_scores)
are kept as Optional so that existing upload.py code continues to work.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


# ---------------------------------------------------------------------------
# Sub-models (nested documents in MongoDB schema)
# ---------------------------------------------------------------------------

class GarmentSource(BaseModel):
    """Phase 3: source section – original image location."""
    image_url: Optional[str] = None
    storage_path: Optional[str] = None  # e.g. "wardrobe-originals/{user_id}/{upload_id}.jpg"


class GarmentAttributes(BaseModel):
    """Phase 3: garment section – ML-classified attributes."""
    category:  Optional[str] = None   # "top" | "bottom" | "shoes" | "outerwear"
    type:      Optional[str] = None   # "oxford shirt" | "trousers" …
    color:     Optional[str] = None
    style:     Optional[str] = None   # "formal" | "casual" …
    season:    Optional[str] = None   # "summer" | "winter" | "all-season"
    pattern:   Optional[str] = None   # "solid" | "striped" …
    material:  Optional[str] = None
    tags:      List[str]     = []


class GarmentSegmentation(BaseModel):
    """Phase 3: segmentation section – SAM-2 output references."""
    mask_url:   Optional[str]         = None  # Supabase URL to binary mask
    cutout_url: Optional[str]         = None  # Supabase URL to transparent cutout
    bbox:       Optional[List[float]] = None  # [x1, y1, x2, y2]


class GarmentEmbedding(BaseModel):
    """Phase 3: embedding section – CLIP vector reference."""
    model:     str           = "fashion-clip-v1"
    dimension: int           = 512
    vector_id: Optional[str] = None  # Qdrant point ID (same as MongoDB _id str)


class GarmentConfidence(BaseModel):
    """Phase 3: confidence section – pipeline quality scores."""
    segmentation_score:  Optional[float] = None
    classification_score: Optional[float] = None


# ---------------------------------------------------------------------------
# Primary document model
# ---------------------------------------------------------------------------

class WardrobeItemCreate(BaseModel):
    """
    Used when inserting a new wardrobe item into MongoDB.
    All fields are optional so partial ingestion results can be stored.
    """
    user_id: str

    # Phase 3 nested structure
    source:       GarmentSource      = Field(default_factory=GarmentSource)
    garment:      GarmentAttributes  = Field(default_factory=GarmentAttributes)
    segmentation: GarmentSegmentation = Field(default_factory=GarmentSegmentation)
    embedding:    GarmentEmbedding   = Field(default_factory=GarmentEmbedding)
    confidence:   GarmentConfidence  = Field(default_factory=GarmentConfidence)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # ------------------------------------------------------------------
    # Legacy flat fields – kept so old upload.py code still compiles.
    # New code should use the nested sub-models above.
    # ------------------------------------------------------------------
    source_image:       Optional[str]   = None
    image_url:          Optional[str]   = None
    segmentation_path:  Optional[str]   = None
    area_ratio:         Optional[float] = None
    confidence_scores:  Dict[str, Any]  = {}
    uploaded_at:        Optional[datetime] = None


class WardrobeItemOut(BaseModel):
    """
    Returned to API clients. Uses the flat legacy layout so existing frontend
    code does not break; Phase 12 frontend refactor will align with Phase 3 structure.
    """
    id: str

    # Flat fields (backward-compatible)
    user_id:    Optional[str]   = None
    category:   Optional[str]   = None
    type:       Optional[str]   = None
    style:      Optional[str]   = None
    season:     Optional[str]   = None
    pattern:    Optional[str]   = None
    color:      Optional[str]   = None
    tags:       List[str]       = []
    confidence_scores: Dict[str, Any] = {}
    source_image:      Optional[str]  = None
    image_url:         Optional[str]  = None
    segmentation_path: Optional[str]  = None
    area_ratio:        Optional[float] = None
    uploaded_at:       Optional[datetime] = None

    # Phase 3 nested fields (optional; populated by new ingestion pipeline)
    source:       Optional[GarmentSource]       = None
    garment:      Optional[GarmentAttributes]   = None
    segmentation: Optional[GarmentSegmentation] = None
    embedding:    Optional[GarmentEmbedding]    = None
    confidence:   Optional[GarmentConfidence]   = None
    created_at:   Optional[datetime]            = None
    updated_at:   Optional[datetime]            = None


# ---------------------------------------------------------------------------
# Ingestion Job models (Phase 5)
# ---------------------------------------------------------------------------

class IngestionJobStatus(BaseModel):
    """Returned immediately by POST /ingest – client polls GET /ingest/{job_id}."""
    job_id:       str
    status:       str   = "queued"   # queued | processing | done | failed
    user_id:      str
    original_path: Optional[str] = None
    items_found:  int   = 0
    created_at:   datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# User Body Profile (Phase 18 – defined here for completeness)
# ---------------------------------------------------------------------------

class UserProfile(BaseModel):
    user_id:       str
    email:         Optional[str] = None
    body_photo_url: Optional[str] = None
    preferences:   Dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Saved Outfit (Phase 19)
# ---------------------------------------------------------------------------

class SavedOutfit(BaseModel):
    user_id:              str
    name:                 Optional[str]   = None
    items:                List[str]       = []   # list of wardrobe_item _ids
    generated_image_url:  Optional[str]  = None
    created_at:           datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Chat models (Phase 20)
# ---------------------------------------------------------------------------

class ChatSession(BaseModel):
    user_id:    str
    title:      Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatMessage(BaseModel):
    session_id:          str
    role:                str   # "user" | "assistant"
    message:             str
    retrieved_items:     List[str]       = []
    recommended_outfit:  Dict[str, Any]  = {}
    timestamp:           datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Generic error response
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    detail: str