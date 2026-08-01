from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class WardrobeItemBase(BaseModel):
    category: Optional[str] = None
    color: Optional[str] = None
    image_path: str

class WardrobeItemCreate(WardrobeItemBase):
    pass

class WardrobeItemOut(WardrobeItemBase):
    id: str
    uploaded_at: datetime

class ErrorResponse(BaseModel):
    detail: str