"""Tests for the Gemini image generation backend."""

from __future__ import annotations

import base64
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from amplifier_comic_image_gen.providers.gemini_images import GeminiImageBackend

# 1x1 red PNG as raw bytes
TINY_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
)


def _make_mock_provider() -> MagicMock:
    """Create a mock provider mimicking the Amplifier Google/Gemini provider."""
    provider = MagicMock()
    provider.name = "provider-google"

    # Build response: candidates[0].content.parts = [text_part, image_part]
    text_part = MagicMock()
    text_part.inline_data = None
    text_part.text = "Here is the generated image."

    image_part = MagicMock()
    image_part.inline_data.data = TINY_PNG_BYTES
    image_part.inline_data.mime_type = "image/png"
    image_part.text = None

    candidate = MagicMock()
    candidate.content.parts = [text_part, image_part]

    response = MagicMock()
    response.candidates = [candidate]

    provider.client.aio.models.generate_content = AsyncMock(return_value=response)
    return provider


@pytest.mark.asyncio(loop_scope="function")
async def test_gemini_backend_generates_image(tmp_path: Path) -> None:
    provider = _make_mock_provider()
    backend = GeminiImageBackend(provider)

    output_path = tmp_path / "panel_01.png"
    result = await backend.generate(
        prompt="A manga-style warrior",
        output_path=output_path,
        size="1024x1024",
    )

    # Verify result dict
    assert result["success"] is True
    assert result["provider_used"] == "provider-google"
    assert result["path"] == str(output_path)
    assert output_path.exists()
    assert output_path.read_bytes() == TINY_PNG_BYTES

    # Verify generate_content was awaited once
    provider.client.aio.models.generate_content.assert_awaited_once()


@pytest.mark.asyncio(loop_scope="function")
async def test_gemini_backend_finds_image_part_among_text(tmp_path: Path) -> None:
    provider = _make_mock_provider()
    backend = GeminiImageBackend(provider)

    output_path = tmp_path / "panel_02.png"
    result = await backend.generate(
        prompt="A sunset scene",
        output_path=output_path,
    )

    assert result["success"] is True
    assert output_path.read_bytes() == TINY_PNG_BYTES


@pytest.mark.asyncio(loop_scope="function")
async def test_gemini_backend_handles_no_image_in_response(tmp_path: Path) -> None:
    provider = _make_mock_provider()

    # Override response to have only text parts (no inline_data)
    text_only_part = MagicMock()
    text_only_part.inline_data = None
    text_only_part.text = "Sorry, I cannot generate that image."

    candidate = MagicMock()
    candidate.content.parts = [text_only_part]

    response = MagicMock()
    response.candidates = [candidate]
    provider.client.aio.models.generate_content = AsyncMock(return_value=response)

    backend = GeminiImageBackend(provider)

    output_path = tmp_path / "panel_03.png"
    result = await backend.generate(
        prompt="Something problematic",
        output_path=output_path,
    )

    assert result["success"] is False
    assert "no image" in result["error"].lower()
    assert not output_path.exists()


@pytest.mark.asyncio(loop_scope="function")
async def test_gemini_backend_handles_api_error(tmp_path: Path) -> None:
    provider = _make_mock_provider()
    provider.client.aio.models.generate_content = AsyncMock(
        side_effect=Exception("Quota exceeded"),
    )
    backend = GeminiImageBackend(provider)

    output_path = tmp_path / "panel_04.png"
    result = await backend.generate(
        prompt="A dragon in space",
        output_path=output_path,
    )

    assert result["success"] is False
    assert "Quota exceeded" in result["error"]
