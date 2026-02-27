"""Tests for the OpenAI image generation backend."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from amplifier_comic_image_gen.providers.openai_images import OpenAIImageBackend

# 1x1 red PNG encoded as base64
TINY_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC"


def _make_mock_provider() -> MagicMock:
    """Create a mock provider mimicking the Amplifier OpenAI provider."""
    provider = MagicMock()
    provider.name = "provider-openai"

    response = MagicMock()
    response.data = [MagicMock(b64_json=TINY_PNG_B64)]

    provider.client.images.generate = AsyncMock(return_value=response)
    return provider


@pytest.mark.asyncio(loop_scope="function")
async def test_openai_backend_generates_image(tmp_path: Path) -> None:
    provider = _make_mock_provider()
    backend = OpenAIImageBackend(provider)

    output_path = tmp_path / "panel_01.png"
    result = await backend.generate(
        prompt="A superhero flying over a city",
        output_path=output_path,
        size="1024x1024",
    )

    # Verify result dict
    assert result["success"] is True
    assert result["provider_used"] == "provider-openai"
    assert result["path"] == str(output_path)
    assert output_path.exists()

    # Verify SDK was called correctly
    call_kwargs = provider.client.images.generate.call_args.kwargs
    assert call_kwargs["model"] == "gpt-image-1"
    assert call_kwargs["response_format"] == "b64_json"
    assert "superhero" in call_kwargs["prompt"]


@pytest.mark.asyncio(loop_scope="function")
async def test_openai_backend_passes_style_parameter(tmp_path: Path) -> None:
    provider = _make_mock_provider()
    backend = OpenAIImageBackend(provider)

    output_path = tmp_path / "panel_02.png"
    await backend.generate(
        prompt="A sunset over mountains",
        output_path=output_path,
        style="natural",
        size="1792x1024",
    )

    call_kwargs = provider.client.images.generate.call_args.kwargs
    assert call_kwargs["size"] == "1792x1024"


@pytest.mark.asyncio(loop_scope="function")
async def test_openai_backend_handles_api_error(tmp_path: Path) -> None:
    provider = _make_mock_provider()
    provider.client.images.generate = AsyncMock(
        side_effect=Exception("Rate limit exceeded"),
    )
    backend = OpenAIImageBackend(provider)

    output_path = tmp_path / "panel_03.png"
    result = await backend.generate(
        prompt="A dragon breathing fire",
        output_path=output_path,
    )

    assert result["success"] is False
    assert "Rate limit" in result["error"]
    assert not output_path.exists()
