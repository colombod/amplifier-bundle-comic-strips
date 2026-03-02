"""Tests for the OpenAI image generation backend."""

from __future__ import annotations

import asyncio
import openai  # pyright: ignore[reportMissingImports]
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from amplifier_module_comic_image_gen.providers.openai_images import (
    ASPECT_RATIO_MAP,
    OpenAIImageBackend,
)

from .conftest import TINY_PNG_BYTES, make_openai_provider


def test_aspect_ratio_map_has_three_entries() -> None:
    assert len(ASPECT_RATIO_MAP) == 3


def test_aspect_ratio_map_values() -> None:
    assert ASPECT_RATIO_MAP["landscape"] == "1536x1024"
    assert ASPECT_RATIO_MAP["portrait"] == "1024x1536"
    assert ASPECT_RATIO_MAP["square"] == "1024x1024"


@pytest.mark.asyncio(loop_scope="function")
async def test_openai_backend_generates_image(tmp_path: Path) -> None:
    provider = make_openai_provider()
    backend = OpenAIImageBackend(provider)

    output_path = tmp_path / "panel_01.png"
    result = await backend.generate(
        prompt="A superhero flying over a city",
        output_path=output_path,
        size="landscape",
    )

    # Verify result dict
    assert result["success"] is True
    assert result["error"] is None
    assert result["provider_used"] == "provider-openai"
    assert result["path"] == str(output_path)
    assert output_path.exists()
    assert output_path.read_bytes() == TINY_PNG_BYTES

    # Verify SDK received mapped pixel dimensions
    call_kwargs = provider.client.images.generate.call_args.kwargs
    assert call_kwargs["size"] == "1536x1024"
    assert call_kwargs["model"] == "gpt-image-1"
    # gpt-image-1 is an edit-capable model that uses output_format, not response_format
    assert call_kwargs["output_format"] == "png"
    assert "superhero" in call_kwargs["prompt"]


@pytest.mark.asyncio(loop_scope="function")
async def test_openai_backend_square_aspect(tmp_path: Path) -> None:
    provider = make_openai_provider()
    backend = OpenAIImageBackend(provider)

    output_path = tmp_path / "panel_square.png"
    result = await backend.generate(
        prompt="A square image",
        output_path=output_path,
        size="square",
    )

    assert result["success"] is True
    call_kwargs = provider.client.images.generate.call_args.kwargs
    assert call_kwargs["size"] == "1024x1024"


@pytest.mark.asyncio(loop_scope="function")
async def test_openai_backend_portrait_aspect(tmp_path: Path) -> None:
    provider = make_openai_provider()
    backend = OpenAIImageBackend(provider)

    output_path = tmp_path / "panel_portrait.png"
    result = await backend.generate(
        prompt="A portrait image",
        output_path=output_path,
        size="portrait",
    )

    assert result["success"] is True
    call_kwargs = provider.client.images.generate.call_args.kwargs
    assert call_kwargs["size"] == "1024x1536"


@pytest.mark.asyncio(loop_scope="function")
async def test_openai_backend_defaults_to_square(tmp_path: Path) -> None:
    provider = make_openai_provider()
    backend = OpenAIImageBackend(provider)

    output_path = tmp_path / "panel_default.png"
    result = await backend.generate(
        prompt="An image with unknown size",
        output_path=output_path,
        size="unknown_ratio",
    )

    assert result["success"] is True
    call_kwargs = provider.client.images.generate.call_args.kwargs
    assert call_kwargs["size"] == "1024x1024"


@pytest.mark.asyncio(loop_scope="function")
async def test_openai_backend_omits_style_for_gpt_image_1(tmp_path: Path) -> None:
    provider = make_openai_provider()
    backend = OpenAIImageBackend(provider)

    output_path = tmp_path / "panel_02.png"
    result = await backend.generate(
        prompt="A sunset over mountains",
        output_path=output_path,
        style="natural",
        size="landscape",
    )

    assert result["success"] is True
    assert result["error"] is None

    call_kwargs = provider.client.images.generate.call_args.kwargs
    assert call_kwargs["size"] == "1536x1024"
    # style is only passed for dall-e-3, not gpt-image-1 (default model)
    assert "style" not in call_kwargs


@pytest.mark.asyncio(loop_scope="function")
async def test_openai_backend_passes_style_for_dall_e_3(tmp_path: Path) -> None:
    provider = make_openai_provider()
    backend = OpenAIImageBackend(provider)

    output_path = tmp_path / "panel_styled.png"
    result = await backend.generate(
        prompt="A sunset over mountains",
        output_path=output_path,
        style="natural",
        model="dall-e-3",
        size="landscape",
    )

    assert result["success"] is True
    assert result["error"] is None

    call_kwargs = provider.client.images.generate.call_args.kwargs
    assert call_kwargs["model"] == "dall-e-3"
    assert call_kwargs["style"] == "natural"
    assert call_kwargs["size"] == "1536x1024"


@pytest.mark.asyncio(loop_scope="function")
async def test_openai_backend_handles_api_error(tmp_path: Path) -> None:
    provider = make_openai_provider()
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


@pytest.mark.asyncio(loop_scope="function")
async def test_openai_backend_accepts_reference_images(tmp_path: Path) -> None:
    """OpenAI backend accepts reference_images parameter without error."""
    # Create a tiny reference image file
    ref_image = tmp_path / "character_ref.png"
    ref_image.write_bytes(TINY_PNG_BYTES)

    provider = make_openai_provider()
    backend = OpenAIImageBackend(provider)

    output_path = tmp_path / "panel_ref.png"
    result = await backend.generate(
        prompt="A superhero in consistent style",
        output_path=output_path,
        reference_images=[str(ref_image)],
    )

    assert result["success"] is True
    assert output_path.exists()


@pytest.mark.asyncio(loop_scope="function")
async def test_openai_backend_reference_images_default_none(tmp_path: Path) -> None:
    """OpenAI backend works normally when reference_images is not provided."""
    provider = make_openai_provider()
    backend = OpenAIImageBackend(provider)

    output_path = tmp_path / "panel_no_ref.png"
    result = await backend.generate(
        prompt="A regular image",
        output_path=output_path,
    )

    assert result["success"] is True
    assert output_path.exists()


# --- Task 2.1: images.edit routing tests ---


@pytest.mark.asyncio(loop_scope="function")
async def test_edit_endpoint_called_with_refs(tmp_path: Path) -> None:
    """images.edit is called when reference_images are provided with gpt-image-1."""
    ref_image = tmp_path / "ref.png"
    ref_image.write_bytes(TINY_PNG_BYTES)

    provider = make_openai_provider()
    backend = OpenAIImageBackend(provider)

    output_path = tmp_path / "panel_edit.png"
    result = await backend.generate(
        prompt="A hero in consistent style",
        output_path=output_path,
        reference_images=[str(ref_image)],
        model="gpt-image-1",
    )

    assert result["success"] is True
    provider.client.images.edit.assert_called_once()
    provider.client.images.generate.assert_not_called()


@pytest.mark.asyncio(loop_scope="function")
async def test_generate_endpoint_called_without_refs(tmp_path: Path) -> None:
    """images.generate is called when no reference_images are provided."""
    provider = make_openai_provider()
    backend = OpenAIImageBackend(provider)

    output_path = tmp_path / "panel_gen.png"
    result = await backend.generate(
        prompt="A hero flying",
        output_path=output_path,
        model="gpt-image-1",
    )

    assert result["success"] is True
    provider.client.images.generate.assert_called_once()
    provider.client.images.edit.assert_not_called()


@pytest.mark.asyncio(loop_scope="function")
async def test_edit_passes_image_file_bytes(tmp_path: Path) -> None:
    """Reference images are passed as (filename, bytes, mime_type) tuples for proper MIME handling."""
    ref_image = tmp_path / "character.png"
    ref_image.write_bytes(TINY_PNG_BYTES)

    provider = make_openai_provider()
    backend = OpenAIImageBackend(provider)

    output_path = tmp_path / "panel_bytes.png"
    await backend.generate(
        prompt="A character",
        output_path=output_path,
        reference_images=[str(ref_image)],
        model="gpt-image-1",
    )

    call_kwargs = provider.client.images.edit.call_args.kwargs
    assert "image" in call_kwargs
    # Each image is a (filename, bytes, content_type) tuple so the API receives
    # a proper MIME type in the multipart upload — raw bytes alone would cause
    # the server to treat the file as application/octet-stream and reject it.
    assert len(call_kwargs["image"]) == 1
    filename, img_bytes, mime = call_kwargs["image"][0]
    assert img_bytes == TINY_PNG_BYTES
    assert mime == "image/png"
    assert filename == "image.png"


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.parametrize(
    "model",
    ["gpt-image-1.5", "gpt-image-1", "gpt-image-1-mini", "dall-e-2"],
)
async def test_all_edit_capable_models_use_edit(tmp_path: Path, model: str) -> None:
    """All gpt-image-1.5/1/1-mini and dall-e-2 models route to images.edit with refs."""
    ref_image = tmp_path / "ref.png"
    ref_image.write_bytes(TINY_PNG_BYTES)

    provider = make_openai_provider()
    backend = OpenAIImageBackend(provider)

    output_path = tmp_path / f"panel_{model}.png"
    result = await backend.generate(
        prompt="A hero",
        output_path=output_path,
        reference_images=[str(ref_image)],
        model=model,
    )

    assert result["success"] is True
    provider.client.images.edit.assert_called_once()
    edit_kwargs = provider.client.images.edit.call_args.kwargs
    assert edit_kwargs["model"] == model


@pytest.mark.asyncio(loop_scope="function")
async def test_dall_e_3_falls_back_to_generate_with_refs(tmp_path: Path) -> None:
    """dall-e-3 falls back to images.generate even when refs are provided."""
    ref_image = tmp_path / "ref.png"
    ref_image.write_bytes(TINY_PNG_BYTES)

    provider = make_openai_provider()
    backend = OpenAIImageBackend(provider)

    output_path = tmp_path / "panel_dalle3.png"
    result = await backend.generate(
        prompt="A sunset",
        output_path=output_path,
        reference_images=[str(ref_image)],
        model="dall-e-3",
    )

    assert result["success"] is True
    provider.client.images.generate.assert_called_once()
    provider.client.images.edit.assert_not_called()


# --- Task A1: Exponential backoff with jitter tests ---


@pytest.mark.asyncio(loop_scope="function")
async def test_openai_retries_on_rate_limit_then_succeeds(tmp_path: Path) -> None:
    """429 RateLimitError triggers retry; succeeds on 3rd attempt; sleep called twice."""
    provider = make_openai_provider()

    # Build a RateLimitError (openai.APIStatusError subclass)
    rate_limit_err = openai.RateLimitError(
        message="429 Too Many Requests",
        response=MagicMock(),
        body=None,
    )

    # Capture the success response before overriding the mock
    success_response = provider.client.images.generate.return_value
    provider.client.images.generate = AsyncMock(
        side_effect=[rate_limit_err, rate_limit_err, success_response]
    )

    backend = OpenAIImageBackend(provider)
    output_path = tmp_path / "panel_retry.png"

    with patch(
        "amplifier_module_comic_image_gen.providers.openai_images.asyncio.sleep",
        new_callable=AsyncMock,
    ) as mock_sleep:
        result = await backend.generate(
            prompt="A hero",
            output_path=output_path,
        )

    assert result["success"] is True
    assert mock_sleep.call_count == 2
    # Verify backoff formula: delay = 2**attempt + uniform(0, 1)
    delay_0 = mock_sleep.call_args_list[0].args[0]
    delay_1 = mock_sleep.call_args_list[1].args[0]
    assert 1.0 <= delay_0 < 2.0, f"attempt 0 delay {delay_0!r} not in [1.0, 2.0)"
    assert 2.0 <= delay_1 < 3.0, f"attempt 1 delay {delay_1!r} not in [2.0, 3.0)"


@pytest.mark.asyncio(loop_scope="function")
async def test_openai_fails_immediately_on_auth_error(tmp_path: Path) -> None:
    """401 AuthenticationError fails on first attempt without any sleep."""
    provider = make_openai_provider()

    auth_err = openai.AuthenticationError(
        message="401 Unauthorized",
        response=MagicMock(),
        body=None,
    )
    provider.client.images.generate = AsyncMock(side_effect=auth_err)

    backend = OpenAIImageBackend(provider)
    output_path = tmp_path / "panel_auth.png"

    with patch(
        "amplifier_module_comic_image_gen.providers.openai_images.asyncio.sleep",
        new_callable=AsyncMock,
    ) as mock_sleep:
        result = await backend.generate(
            prompt="A hero",
            output_path=output_path,
        )

    assert result["success"] is False
    assert mock_sleep.call_count == 0
    assert provider.client.images.generate.call_count == 1


@pytest.mark.asyncio(loop_scope="function")
async def test_openai_fails_after_max_retries(tmp_path: Path) -> None:
    """429 RateLimitError on all 3 attempts returns failure after 2 sleeps."""
    provider = make_openai_provider()

    rate_limit_err = openai.RateLimitError(
        message="429 Too Many Requests",
        response=MagicMock(),
        body=None,
    )
    # Always raise RateLimitError
    provider.client.images.generate = AsyncMock(side_effect=rate_limit_err)

    backend = OpenAIImageBackend(provider)
    output_path = tmp_path / "panel_exhausted.png"

    with patch(
        "amplifier_module_comic_image_gen.providers.openai_images.asyncio.sleep",
        new_callable=AsyncMock,
    ) as mock_sleep:
        result = await backend.generate(
            prompt="A hero",
            output_path=output_path,
        )

    assert result["success"] is False
    # sleep after attempt 0 and 1; NOT after the final attempt 2
    assert mock_sleep.call_count == 2
    # Verify backoff formula: delay = 2**attempt + uniform(0, 1)
    delay_0 = mock_sleep.call_args_list[0].args[0]
    delay_1 = mock_sleep.call_args_list[1].args[0]
    assert 1.0 <= delay_0 < 2.0, f"attempt 0 delay {delay_0!r} not in [1.0, 2.0)"
    assert 2.0 <= delay_1 < 3.0, f"attempt 1 delay {delay_1!r} not in [2.0, 3.0)"


# --- Task A3: asyncio.to_thread for reference image reads ---


@pytest.mark.asyncio(loop_scope="function")
async def test_edit_reads_reference_images_via_to_thread(tmp_path: Path) -> None:
    """asyncio.to_thread is used for non-blocking file reads in _call_edit."""
    ref_image = tmp_path / "ref.png"
    ref_image.write_bytes(TINY_PNG_BYTES)

    provider = make_openai_provider()
    backend = OpenAIImageBackend(provider)

    output_path = tmp_path / "panel_thread.png"
    with patch(
        "amplifier_module_comic_image_gen.providers.openai_images.asyncio.to_thread",
        wraps=asyncio.to_thread,
    ) as mock_to_thread:
        result = await backend.generate(
            prompt="A hero in consistent style",
            output_path=output_path,
            reference_images=[str(ref_image)],
            model="gpt-image-1",
        )

    assert result["success"] is True
    assert mock_to_thread.called is True
    assert callable(mock_to_thread.call_args_list[0].args[0])
