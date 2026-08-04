"""FastAPI route for the wardrobe 2D/IDM-VTON outfit visualization."""

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user
from app.core.security import UserContext
from app.services.visualization_service import VisualizationService

router = APIRouter(prefix="/visualization", tags=["visualization"])


class VisualizationRequest(BaseModel):
    item_ids: list[str] = Field(..., min_length=1, max_length=4)
    mode: str = Field(default="overlay")
    user_body_photo_url: str | None = Field(default=None)


class VisualizationResponse(BaseModel):
    mode: str
    items: list[dict[str, Any]]
    ai_image_url: str | None = None


@router.post("", response_model=VisualizationResponse)
async def visualize_outfit(
    request: VisualizationRequest,
    current_user: UserContext = Depends(get_current_user),
) -> VisualizationResponse:
    """Return 2D overlay layout or IDM-VTON try-on for the selected garment items."""
    result = await VisualizationService().build_response(
        request.item_ids,
        mode=request.mode,
        user_body_photo_url=request.user_body_photo_url,
    )
    return VisualizationResponse(**result)