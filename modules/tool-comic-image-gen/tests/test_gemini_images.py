"""Tests for the Gemini image generation backend — aspect ratio support."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from google.api_core import exceptions as google_exceptions  # pyright: ignore[reportMissingImports]

from amplifier_module_comic_image_gen.providers.gemini_images import GeminiImageBackend

from .conftest import TINY_PNG_BYTES, make_gemini_provider, make_gemini_imagen_provider


@pytest.mark.asyncio(loop_scope="function")
async def test_gemini_backend_generates_image(tmp_path: Path) -> None:
    provider = make_gemini_provider()
    backend = GeminiImageBackend(provider)

    output_path = tmp_path / "panel_01.png"
    result = await backend.generate(
        prompt="A manga-style warrior",
        output_path=output_path,
        size="square",
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
async def test_gemini_backend_accepts_aspect_ratios(tmp_path: Path) -> None:
    """Gemini backend accepts all three aspect ratio strings without error."""
    for ratio in ("landscape", "portrait", "square"):
        provider = make_gemini_provider()
        backend = GeminiImageBackend(provider)

        output_path = tmp_path / f"panel_{ratio}.png"
        result = await backend.generate(
            prompt=f"An image with {ratio} aspect ratio",
            output_path=output_path,
            size=ratio,
        )

        assert result["success"] is True, f"Failed for size={ratio}"


@pytest.mark.asyncio(loop_scope="function")
async def test_gemini_backend_finds_image_part_among_text(tmp_path: Path) -> None:
    provider = make_gemini_provider()
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
    provider = make_gemini_provider()

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
    provider = make_gemini_provider()
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


def test_extract_image_raises_on_unexpected_data_type() -> None:
    """_extract_image should raise TypeError for non-bytes/non-str data."""
    backend = GeminiImageBackend.__new__(GeminiImageBackend)

    # Build a response where inline_data.data is an integer — not bytes or str
    part = MagicMock()
    part.inline_data.data = 42  # unexpected type

    candidate = MagicMock()
    candidate.content.parts = [part]

    response = MagicMock()
    response.candidates = [candidate]

    with pytest.raises(TypeError, match="Unexpected inline_data.data type"):
        backend._extract_image(response)


@pytest.mark.asyncio(loop_scope="function")
async def test_gemini_backend_accepts_reference_images(tmp_path: Path) -> None:
    """Gemini backend sends multimodal content with reference image parts."""
    # Create a tiny reference image file
    ref_image = tmp_path / "character_ref.png"
    ref_image.write_bytes(TINY_PNG_BYTES)

    provider = make_gemini_provider()
    backend = GeminiImageBackend(provider)

    output_path = tmp_path / "panel_ref.png"
    result = await backend.generate(
        prompt="A warrior in consistent style",
        output_path=output_path,
        reference_images=[str(ref_image)],
    )

    assert result["success"] is True

    # Verify generate_content was called with multimodal content (more than 1 part)
    call_kwargs = provider.client.aio.models.generate_content.call_args.kwargs
    contents = call_kwargs["contents"]
    # Contents should have parts: reference image part(s) + text prompt part
    # Access .parts if it's a typed object, or ["parts"] if dict
    if hasattr(contents, "parts"):
        parts = contents.parts
    else:
        parts = contents["parts"]
    assert len(parts) > 1, (
        "Expected multimodal content with reference image parts + text prompt"
    )


@pytest.mark.asyncio(loop_scope="function")
async def test_gemini_backend_reference_images_default_none(tmp_path: Path) -> None:
    """Gemini backend works normally when reference_images is not provided."""
    provider = make_gemini_provider()
    backend = GeminiImageBackend(provider)

    output_path = tmp_path / "panel_no_ref.png"
    result = await backend.generate(
        prompt="A regular image",
        output_path=output_path,
    )

    assert result["success"] is True
    assert output_path.exists()


# ── Imagen 4 / default-model tests (Task 2.2) ──────────────────────────


def test_gemini_default_model_is_flash_image() -> None:
    """Default model parameter should be 'gemini-2.5-flash-image'."""
    import inspect

    sig = inspect.signature(GeminiImageBackend.generate)
    default = sig.parameters["model"].default
    assert default == "gemini-2.5-flash-image", (
        f"Expected default model 'gemini-2.5-flash-image', got '{default}'"
    )


@pytest.mark.asyncio(loop_scope="function")
async def test_imagen_model_uses_generate_images(tmp_path: Path) -> None:
    """Imagen models should call generateImages, not generateContent."""
    provider = make_gemini_imagen_provider()
    backend = GeminiImageBackend(provider)

    output_path = tmp_path / "imagen_panel.png"
    result = await backend.generate(
        prompt="A comic panel with a hero",
        output_path=output_path,
        model="imagen-4.0-generate-preview-06-06",
    )

    assert result["success"] is True
    assert output_path.read_bytes() == TINY_PNG_BYTES
    provider.client.aio.models.generate_images.assert_awaited_once()
    provider.client.aio.models.generate_content.assert_not_awaited()


@pytest.mark.asyncio(loop_scope="function")
async def test_imagen_model_ignores_reference_images(tmp_path: Path) -> None:
    """Imagen models should silently ignore reference_images (text-to-image only)."""
    ref_image = tmp_path / "ref.png"
    ref_image.write_bytes(TINY_PNG_BYTES)

    provider = make_gemini_imagen_provider()
    backend = GeminiImageBackend(provider)

    output_path = tmp_path / "imagen_ref_ignored.png"
    result = await backend.generate(
        prompt="A warrior",
        output_path=output_path,
        model="imagen-4.0-generate-preview-06-06",
        reference_images=[str(ref_image)],
    )

    assert result["success"] is True
    # Verify generate_images was called with just prompt, no reference data
    call_kwargs = provider.client.aio.models.generate_images.call_args.kwargs
    assert "contents" not in call_kwargs  # no multimodal contents
    provider.client.aio.models.generate_images.assert_awaited_once()


@pytest.mark.asyncio(loop_scope="function")
@pytest.mark.parametrize(
    "model_id",
    [
        "imagen-4.0-generate-preview-06-06",
        "imagen-4.0-ultra-generate-preview-06-06",
        "imagen-4.0-flash-preview-05-20",
    ],
)
async def test_all_imagen_model_ids_route_to_generate_images(
    tmp_path: Path, model_id: str
) -> None:
    """All three Imagen model IDs should route to generateImages."""
    provider = make_gemini_imagen_provider()
    backend = GeminiImageBackend(provider)

    output_path = tmp_path / f"panel_{model_id}.png"
    result = await backend.generate(
        prompt="A test image",
        output_path=output_path,
        model=model_id,
    )

    assert result["success"] is True
    provider.client.aio.models.generate_images.assert_awaited_once()
    provider.client.aio.models.generate_content.assert_not_awaited()


@pytest.mark.asyncio(loop_scope="function")
async def test_non_imagen_model_still_uses_generate_content(tmp_path: Path) -> None:
    """Non-Imagen Gemini models should still use generateContent path."""
    provider = make_gemini_provider()
    backend = GeminiImageBackend(provider)

    output_path = tmp_path / "panel_gemini.png"
    result = await backend.generate(
        prompt="A regular Gemini image",
        output_path=output_path,
        model="gemini-2.5-flash-image",
    )

    assert result["success"] is True
    provider.client.aio.models.generate_content.assert_awaited_once()


# ── Exponential backoff / retry tests (Task A2) ────────────────────────────


@pytest.mark.asyncio(loop_scope="function")
async def test_gemini_retries_on_resource_exhausted_then_succeeds(
    tmp_path: Path,
) -> None:
    """ResourceExhausted triggers retry; succeeds on 3rd attempt, sleep called twice."""
    provider = make_gemini_provider()

    # Build a successful response for the 3rd attempt
    success_response = provider.client.aio.models.generate_content.return_value

    # First two calls raise ResourceExhausted, third succeeds
    provider.client.aio.models.generate_content = AsyncMock(
        side_effect=[
            google_exceptions.ResourceExhausted("rate limit"),
            google_exceptions.ResourceExhausted("rate limit"),
            success_response,
        ]
    )

    backend = GeminiImageBackend(provider)
    output_path = tmp_path / "retry_success.png"

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = await backend.generate(
            prompt="A retried image",
            output_path=output_path,
        )

    assert result["success"] is True
    assert mock_sleep.call_count == 2, (
        f"Expected sleep called twice for 2 retries, got {mock_sleep.call_count}"
    )
    assert provider.client.aio.models.generate_content.call_count == 3


@pytest.mark.asyncio(loop_scope="function")
async def test_gemini_fails_immediately_on_unauthenticated(tmp_path: Path) -> None:
    """Unauthenticated (non-retryable) error fails on first attempt with no sleep."""
    provider = make_gemini_provider()
    provider.client.aio.models.generate_content = AsyncMock(
        side_effect=google_exceptions.Unauthenticated("invalid credentials"),
    )

    backend = GeminiImageBackend(provider)
    output_path = tmp_path / "auth_fail.png"

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = await backend.generate(
            prompt="An image that fails auth",
            output_path=output_path,
        )

    assert result["success"] is False
    assert mock_sleep.call_count == 0, (
        f"Expected no sleep for non-retryable error, got {mock_sleep.call_count}"
    )
    assert provider.client.aio.models.generate_content.call_count == 1


@pytest.mark.asyncio(loop_scope="function")
async def test_gemini_fails_after_max_retries(tmp_path: Path) -> None:
    """ResourceExhausted on all 3 attempts returns failure result."""
    provider = make_gemini_provider()
    provider.client.aio.models.generate_content = AsyncMock(
        side_effect=google_exceptions.ResourceExhausted("quota exhausted"),
    )

    backend = GeminiImageBackend(provider)
    output_path = tmp_path / "max_retries_fail.png"

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = await backend.generate(
            prompt="An image that always fails",
            output_path=output_path,
        )

    assert result["success"] is False
    assert provider.client.aio.models.generate_content.call_count == 3, (
        f"Expected 3 attempts (_MAX_ATTEMPTS), got "
        f"{provider.client.aio.models.generate_content.call_count}"
    )
    assert mock_sleep.call_count == 2, (
        f"Expected sleep called twice (after attempt 1 and 2), got {mock_sleep.call_count}"
    )


# --- Task A3: asyncio.to_thread for reference image reads ---


@pytest.mark.asyncio(loop_scope="function")
async def test_gemini_reads_reference_images_via_to_thread(tmp_path: Path) -> None:
    """asyncio.to_thread is used for non-blocking file reads in _build_content_config."""
    ref_image = tmp_path / "ref.png"
    ref_image.write_bytes(TINY_PNG_BYTES)

    provider = make_gemini_provider()
    backend = GeminiImageBackend(provider)

    output_path = tmp_path / "panel_thread.png"
    with patch(
        "amplifier_module_comic_image_gen.providers.gemini_images.asyncio.to_thread",
        wraps=asyncio.to_thread,
    ) as mock_to_thread:
        result = await backend.generate(
            prompt="A warrior in consistent style",
            output_path=output_path,
            reference_images=[str(ref_image)],
        )

    assert result["success"] is True
    assert mock_to_thread.called is True
    assert callable(mock_to_thread.call_args_list[0].args[0])
