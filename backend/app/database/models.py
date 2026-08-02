from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class WardrobeItemBase(BaseModel):
    category: Optional[str] = None
    type: Optional[str] = None
    style: Optional[str] = None
    season: Optional[str] = None
    pattern: Optional[str] = None
    color: Optional[str] = None
    tags: list[str] = []
    confidence_scores: dict = {}
    source_image: str
    segmentation_path: str
    area_ratio: Optional[float] = None

class WardrobeItemOut(WardrobeItemBase):
    id: str
    uploaded_at: datetime

class ErrorResponse(BaseModel):
    detail: str