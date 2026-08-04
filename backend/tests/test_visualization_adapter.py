import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from app.services.visualization.schemas import VirtualTryOnRequest
from app.services.visualization.ootd_vton import OOTDiffusionAdapter

@pytest.mark.asyncio
async def test_ootd_adapter_missing_garment():
    """Test that the adapter catches missing garments before calling Modal."""
    adapter = OOTDiffusionAdapter()
    
    request = VirtualTryOnRequest(
        person_image_url="http://example.com/person.jpg"
        # No garments provided
    )
    
    response = await adapter.generate(request)
    assert response.success is False
    assert "At least one garment URL must be provided" in response.error_message
    assert response.provider == "OOTDiffusion"

@pytest.mark.asyncio
async def test_ootd_adapter_mock_generation():
    """Test that the adapter successfully processes a valid multi-garment payload."""
    adapter = OOTDiffusionAdapter()
    
    request = VirtualTryOnRequest(
        person_image_url="http://example.com/person.jpg",
        top_garment_url="http://example.com/top.jpg",
        bottom_garment_url="http://example.com/bottom.jpg"
    )
    
    # By default, since MODAL_API_TOKEN is not set in this test environment,
    # the adapter will trigger the mock return logic.
    response = await adapter.generate(request)
    assert response.success is True
    assert response.ai_image_url == "https://mock-modal-output.com/mock-vton.png"
    assert response.provider == "OOTDiffusion (Mock)"

@pytest.mark.asyncio
async def test_ootd_adapter_http_call():
    """Test the httpx logic when Modal URL is configured."""
    adapter = OOTDiffusionAdapter()
    
    request = VirtualTryOnRequest(
        person_image_url="http://example.com/person.jpg",
        top_garment_url="http://example.com/top.jpg"
    )
    
    with patch("os.getenv", side_effect=lambda k, d="": "https://real-modal.com/generate" if k == "MODAL_OOTD_ENDPOINT" else d):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = AsyncMock()
            mock_post.return_value.raise_for_status = lambda: None
            mock_post.return_value.json = lambda: {"output_url": "https://modal-generated.png"}
            
            response = await adapter.generate(request)
            assert response.success is True
            assert response.ai_image_url == "https://modal-generated.png"
            assert response.provider == "OOTDiffusion"
