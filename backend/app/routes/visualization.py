"""FastAPI route for the wardrobe 2D outfit visualization MVP (WMVP-20)."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

try:
    from app.services.visualization_service import VisualizationService  # type: ignore[import]
except ImportError:
    from backend.app.services.visualization_service import VisualizationService  # type: ignore[import]

router = APIRouter(prefix="/visualization", tags=["visualization"])


class VisualizationRequest(BaseModel):
    item_ids: list[str] = Field(..., min_length=1, max_length=4)
    mode: str = Field(default="overlay")
    # Required when mode="ai"; the URL/path of the user's uploaded body photo.
    user_body_photo_url: str | None = Field(default=None)
    # Post-MVP: add user_id here for authorization once auth middleware is in place.


class VisualizationResponse(BaseModel):
    mode: str
    items: list[dict[str, Any]]
    ai_image_url: str | None = None


@router.post("", response_model=VisualizationResponse)
async def visualize_outfit(request: VisualizationRequest) -> VisualizationResponse:
    """Return 2D overlay layout or Gemini AI try-on for the selected garment items."""
    result = await VisualizationService().build_response(
        request.item_ids,
        mode=request.mode,
        user_body_photo_url=request.user_body_photo_url,
    )
    return VisualizationResponse(**result)