"""
Tests for the FASHN virtual try-on adapter.

The adapter posts base64 images to a Modal endpoint and expects `output_b64`
back. These tests cover the contract without touching the network — the real
Modal round trip is verified manually, since it needs a live GPU container.
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.visualization.ootd_vton import OOTDiffusionAdapter
from app.services.visualization.schemas import VirtualTryOnRequest

PERSON = "http://example.com/person.jpg"
TOP = "http://example.com/top.png"
BOTTOM = "http://example.com/bottom.png"

FAKE_B64 = "aGVsbG8="


def _response(status_code=200, payload=None):
    """A stand-in for httpx.Response carrying just what the adapter reads."""
    res = AsyncMock()
    res.status_code = status_code
    res.raise_for_status = lambda: None
    res.json = lambda: payload or {}
    res.text = ""
    return res


@pytest.mark.asyncio
async def test_missing_garment_is_rejected_before_calling_modal():
    response = await OOTDiffusionAdapter().generate(
        VirtualTryOnRequest(person_image_url=PERSON)
    )
    assert response.success is False
    assert "At least one garment URL must be provided" in response.error_message


@pytest.mark.asyncio
async def test_successful_generation_returns_a_data_uri():
    with patch("app.services.visualization.ootd_vton.settings") as cfg, \
         patch("app.services.visualization_service.VisualizationService._to_base64",
               new=AsyncMock(return_value=FAKE_B64)), \
         patch("httpx.AsyncClient.post",
               new=AsyncMock(return_value=_response(payload={"success": True, "output_b64": FAKE_B64}))):
        cfg.ootd_provider = "modal"
        cfg.modal_ootd_endpoint = "https://modal.test/vton"
        cfg.hf_token = "hf_test"

        response = await OOTDiffusionAdapter().generate(
            VirtualTryOnRequest(person_image_url=PERSON, top_garment_url=TOP)
        )

    assert response.success is True
    assert response.ai_image_url == f"data:image/png;base64,{FAKE_B64}"
    assert response.provider == "FASHN modal"


@pytest.mark.asyncio
async def test_every_supplied_garment_is_sent_to_modal():
    post = AsyncMock(return_value=_response(payload={"success": True, "output_b64": FAKE_B64}))

    with patch("app.services.visualization.ootd_vton.settings") as cfg, \
         patch("app.services.visualization_service.VisualizationService._to_base64",
               new=AsyncMock(return_value=FAKE_B64)), \
         patch("httpx.AsyncClient.post", new=post):
        cfg.ootd_provider = "modal"
        cfg.modal_ootd_endpoint = "https://modal.test/vton"
        cfg.hf_token = "hf_test"

        await OOTDiffusionAdapter().generate(
            VirtualTryOnRequest(person_image_url=PERSON, top_garment_url=TOP, bottom_garment_url=BOTTOM)
        )

    sent = post.await_args.kwargs["json"]
    assert sent["person_image_b64"] == FAKE_B64
    assert sent["top_garment_b64"] == FAKE_B64
    assert sent["bottom_garment_b64"] == FAKE_B64
    assert "dress_garment_b64" not in sent


@pytest.mark.asyncio
async def test_modal_failure_flag_is_surfaced():
    with patch("app.services.visualization.ootd_vton.settings") as cfg, \
         patch("app.services.visualization_service.VisualizationService._to_base64",
               new=AsyncMock(return_value=FAKE_B64)), \
         patch("httpx.AsyncClient.post",
               new=AsyncMock(return_value=_response(payload={"success": False, "error": "OOM on A10G"}))):
        cfg.ootd_provider = "modal"
        cfg.modal_ootd_endpoint = "https://modal.test/vton"
        cfg.hf_token = "hf_test"

        response = await OOTDiffusionAdapter().generate(
            VirtualTryOnRequest(person_image_url=PERSON, top_garment_url=TOP)
        )

    assert response.success is False
    assert "OOM on A10G" in response.error_message


@pytest.mark.asyncio
async def test_empty_output_is_treated_as_failure():
    with patch("app.services.visualization.ootd_vton.settings") as cfg, \
         patch("app.services.visualization_service.VisualizationService._to_base64",
               new=AsyncMock(return_value=FAKE_B64)), \
         patch("httpx.AsyncClient.post",
               new=AsyncMock(return_value=_response(payload={"success": True, "output_b64": ""}))):
        cfg.ootd_provider = "modal"
        cfg.modal_ootd_endpoint = "https://modal.test/vton"
        cfg.hf_token = "hf_test"

        response = await OOTDiffusionAdapter().generate(
            VirtualTryOnRequest(person_image_url=PERSON, top_garment_url=TOP)
        )

    assert response.success is False
    assert "Empty B64" in response.error_message


@pytest.mark.asyncio
async def test_unconfigured_endpoint_fails_cleanly():
    with patch("app.services.visualization.ootd_vton.settings") as cfg:
        cfg.ootd_provider = "modal"
        cfg.modal_ootd_endpoint = ""

        response = await OOTDiffusionAdapter().generate(
            VirtualTryOnRequest(person_image_url=PERSON, top_garment_url=TOP)
        )

    assert response.success is False
    assert "MODAL_OOTD_ENDPOINT not set" in response.error_message


@pytest.mark.asyncio
async def test_timeout_reports_cold_start_guidance():
    import httpx

    with patch("app.services.visualization.ootd_vton.settings") as cfg, \
         patch("app.services.visualization_service.VisualizationService._to_base64",
               new=AsyncMock(return_value=FAKE_B64)), \
         patch("httpx.AsyncClient.post",
               new=AsyncMock(side_effect=httpx.ReadTimeout("timed out"))):
        cfg.ootd_provider = "modal"
        cfg.modal_ootd_endpoint = "https://modal.test/vton"
        cfg.hf_token = "hf_test"

        response = await OOTDiffusionAdapter().generate(
            VirtualTryOnRequest(person_image_url=PERSON, top_garment_url=TOP)
        )

    assert response.success is False
    assert "cold start" in response.error_message.lower()
