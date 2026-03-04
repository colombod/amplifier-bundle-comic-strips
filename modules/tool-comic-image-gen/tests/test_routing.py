"""Routing integration tests for WP-2: model→backend routing fixes."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from amplifier_module_comic_image_gen import ComicImageGenTool
from amplifier_module_comic_image_gen.model_selector import SelectionResult
from amplifier_module_comic_image_gen.providers.openai_images import OpenAIImageBackend

from .conftest import make_openai_provider, make_gemini_imagen_provider


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_openai_backend(
    *,
    output_path: str,
    provider_name: str = "provider-openai",
) -> MagicMock:
    """Mock backend that reports provider_type='openai' and always succeeds."""
    backend = MagicMock()
    backend.provider.name = provider_name
    backend.provider_type = "openai"
    backend.generate = AsyncMock(
        return_value={
            "success": True,
            "provider_used": provider_name,
            "path": output_path,
            "error": None,
        }
    )
    return backend


def _make_mock_gemini_backend(
    *,
    output_path: str,
    provider_name: str = "provider-google",
) -> MagicMock:
    """Mock backend that reports provider_type='gemini' and always succeeds."""
    backend = MagicMock()
    backend.provider.name = provider_name
    backend.provider_type = "gemini"
    backend.generate = AsyncMock(
        return_value={
            "success": True,
            "provider_used": provider_name,
            "path": output_path,
            "error": None,
        }
    )
    return backend


# ---------------------------------------------------------------------------
# Test 1: explicit Gemini model routes to Gemini backend
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_explicit_gemini_model_routes_to_gemini_backend(
    tmp_path: Path,
) -> None:
    """model='gemini-2.5-flash-image' must route to the Gemini backend, not OpenAI."""
    out = str(tmp_path / "out.png")
    openai_backend = _make_mock_openai_backend(output_path=out)
    gemini_backend = _make_mock_gemini_backend(output_path=out)

    # OpenAI is listed first to confirm it is NOT tried before Gemini
    tool = ComicImageGenTool(backends=[openai_backend, gemini_backend])

    result = await tool.execute(
        {
            "prompt": "A hero panel",
            "output_path": out,
            "model": "gemini-2.5-flash-image",
        }
    )

    assert result.success is True
    gemini_backend.generate.assert_awaited_once()
    openai_backend.generate.assert_not_awaited()


# ---------------------------------------------------------------------------
# Test 2: explicit OpenAI model routes to OpenAI backend
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_explicit_openai_model_routes_to_openai_backend(
    tmp_path: Path,
) -> None:
    """model='gpt-image-1' must route to the OpenAI backend, not Gemini."""
    out = str(tmp_path / "out.png")
    openai_backend = _make_mock_openai_backend(output_path=out)
    gemini_backend = _make_mock_gemini_backend(output_path=out)

    # Gemini is listed first to confirm it is NOT tried before OpenAI
    tool = ComicImageGenTool(backends=[gemini_backend, openai_backend])

    result = await tool.execute(
        {
            "prompt": "A hero panel",
            "output_path": out,
            "model": "gpt-image-1",
        }
    )

    assert result.success is True
    openai_backend.generate.assert_awaited_once()
    gemini_backend.generate.assert_not_awaited()


# ---------------------------------------------------------------------------
# Test 3: requirements-based selection routes to the provider returned by
#          select_model
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_requirements_selection_routes_to_correct_provider(
    tmp_path: Path,
) -> None:
    """When select_model returns provider='google', the Gemini backend goes first."""
    out = str(tmp_path / "out.png")
    openai_backend = _make_mock_openai_backend(output_path=out)
    gemini_backend = _make_mock_gemini_backend(output_path=out)

    # OpenAI first — routing fix must reorder to Gemini
    tool = ComicImageGenTool(backends=[openai_backend, gemini_backend])

    mocked_selection = SelectionResult(
        model_id="gemini-2.5-flash-image",
        provider="google",
        api_surface="gemini-generate-content",
        cost_tier=2,
        rationale="test override",
    )

    with patch(
        "amplifier_module_comic_image_gen.select_model",
        return_value=mocked_selection,
    ):
        result = await tool.execute(
            {
                "prompt": "A hero panel",
                "output_path": out,
                "requirements": {"needs_reference_images": False},
            }
        )

    assert result.success is True
    gemini_backend.generate.assert_awaited_once()
    openai_backend.generate.assert_not_awaited()


# ---------------------------------------------------------------------------
# Test 4: preferred_provider sorts backends
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_preferred_provider_sorts_backends(tmp_path: Path) -> None:
    """preferred_provider='google' causes the Gemini backend to be tried first."""
    out = str(tmp_path / "out.png")
    # The existing preferred_provider sort uses b.provider.name.lower(), so the
    # provider name must contain "google" for the Gemini backend.
    openai_backend = _make_mock_openai_backend(
        output_path=out, provider_name="provider-openai"
    )
    gemini_backend = _make_mock_gemini_backend(
        output_path=out, provider_name="provider-google"
    )

    # OpenAI first in the list — sort must move Gemini to front
    tool = ComicImageGenTool(backends=[openai_backend, gemini_backend])

    result = await tool.execute(
        {
            "prompt": "A hero panel",
            "output_path": out,
            "preferred_provider": "google",
        }
    )

    assert result.success is True
    gemini_backend.generate.assert_awaited_once()
    openai_backend.generate.assert_not_awaited()


# ---------------------------------------------------------------------------
# Tests 5-7: OpenAI _call_generate response_format / output_format behaviour
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_openai_no_response_format_for_unknown_model(tmp_path: Path) -> None:
    """Unknown models must NOT receive response_format or output_format kwargs."""
    provider = make_openai_provider()
    backend = OpenAIImageBackend(provider)

    await backend._call_generate(
        model="some-unknown-model",
        prompt="A panel",
        pixel_size="1024x1024",
        style=None,
    )

    call_kwargs = provider.client.images.generate.call_args.kwargs
    assert "response_format" not in call_kwargs, (
        f"response_format should not be set for unknown models; got {call_kwargs}"
    )
    assert "output_format" not in call_kwargs, (
        f"output_format should not be set for unknown models; got {call_kwargs}"
    )


@pytest.mark.asyncio(loop_scope="function")
async def test_openai_response_format_for_dall_e_3(tmp_path: Path) -> None:
    """dall-e-3 must receive response_format='b64_json', NOT output_format."""
    provider = make_openai_provider()
    backend = OpenAIImageBackend(provider)

    await backend._call_generate(
        model="dall-e-3",
        prompt="A panel",
        pixel_size="1024x1024",
        style=None,
    )

    call_kwargs = provider.client.images.generate.call_args.kwargs
    assert call_kwargs.get("response_format") == "b64_json", (
        f"dall-e-3 should use response_format=b64_json; got {call_kwargs}"
    )
    assert "output_format" not in call_kwargs, (
        f"dall-e-3 must not use output_format; got {call_kwargs}"
    )


@pytest.mark.asyncio(loop_scope="function")
async def test_openai_output_format_for_gpt_image_1(tmp_path: Path) -> None:
    """gpt-image-1 must receive output_format='png', NOT response_format."""
    provider = make_openai_provider()
    backend = OpenAIImageBackend(provider)

    await backend._call_generate(
        model="gpt-image-1",
        prompt="A panel",
        pixel_size="1024x1024",
        style=None,
    )

    call_kwargs = provider.client.images.generate.call_args.kwargs
    assert call_kwargs.get("output_format") == "png", (
        f"gpt-image-1 should use output_format=png; got {call_kwargs}"
    )
    assert "response_format" not in call_kwargs, (
        f"gpt-image-1 must not use response_format; got {call_kwargs}"
    )


# ---------------------------------------------------------------------------
# Tests 8-10: Imagen / Google model hard-routing (no cross-provider fallback)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_imagen_model_does_not_fall_back_to_openai_on_gemini_failure(
    tmp_path: Path,
) -> None:
    """RC1 regression: when Gemini fails for an Imagen model, OpenAI must NOT be called.

    Before the fix, a Gemini failure would fall through to OpenAI with the Imagen
    model ID, producing ``BadRequestError: Unknown parameter: 'response_format'``.
    """
    out = str(tmp_path / "out.png")

    # Gemini backend that always fails
    gemini_backend = MagicMock()
    gemini_backend.provider.name = "provider-google"
    gemini_backend.provider_type = "gemini"
    gemini_backend.generate = AsyncMock(
        return_value={
            "success": False,
            "provider_used": "provider-google",
            "path": out,
            "error": "Gemini unavailable",
        }
    )

    # OpenAI backend that would succeed — must NOT be reached
    openai_backend = _make_mock_openai_backend(output_path=out)

    tool = ComicImageGenTool(backends=[gemini_backend, openai_backend])

    result = await tool.execute(
        {
            "prompt": "A photo-real hero",
            "output_path": out,
            "model": "imagen-4.0-generate-001",
        }
    )

    # The request should fail (Gemini failed) but OpenAI must NOT have been tried
    assert result.success is False
    openai_backend.generate.assert_not_awaited()
    gemini_backend.generate.assert_awaited_once()


@pytest.mark.asyncio(loop_scope="function")
async def test_imagen_model_with_no_gemini_backend_returns_descriptive_error(
    tmp_path: Path,
) -> None:
    """RC1 regression: requesting an Imagen model when only OpenAI is available must
    return a clear error, NOT silently route to OpenAI.
    """
    out = str(tmp_path / "out.png")

    # Only OpenAI backend is available
    openai_backend = _make_mock_openai_backend(output_path=out)
    tool = ComicImageGenTool(backends=[openai_backend])

    result = await tool.execute(
        {
            "prompt": "A photo-real hero",
            "output_path": out,
            "model": "imagen-4.0-generate-001",
        }
    )

    assert result.success is False
    # Error message must mention the model and the required backend
    assert "imagen-4.0-generate-001" in result.output
    assert "gemini" in result.output.lower()
    # OpenAI must never have been called
    openai_backend.generate.assert_not_awaited()


@pytest.mark.asyncio(loop_scope="function")
async def test_explicit_imagen_model_routes_to_gemini_and_succeeds(
    tmp_path: Path,
) -> None:
    """Explicit Imagen model routes to Gemini backend (happy path)."""
    from amplifier_module_comic_image_gen.providers.gemini_images import (
        GeminiImageBackend,
    )

    out = str(tmp_path / "out.png")
    provider = make_gemini_imagen_provider()
    gemini_backend = GeminiImageBackend(provider)

    openai_backend = _make_mock_openai_backend(output_path=out)

    # OpenAI listed first — routing must pick Gemini
    tool = ComicImageGenTool(backends=[openai_backend, gemini_backend])

    result = await tool.execute(
        {
            "prompt": "A photorealistic hero",
            "output_path": out,
            "model": "imagen-4.0-generate-001",
        }
    )

    assert result.success is True, f"Expected success; got: {result.output}"
    openai_backend.generate.assert_not_awaited()
    provider.client.aio.models.generate_images.assert_awaited_once()


# ---------------------------------------------------------------------------
# Test 11: _call_edit dead-code response_format guard
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_call_edit_does_not_add_response_format_for_edit_capable_model(
    tmp_path: Path,
) -> None:
    """RC3: _call_edit must NOT set response_format for edit-capable models.

    The dead-code guard previously used ``model not in _EDIT_CAPABLE_MODELS``
    which, if ever reached, would have added response_format for any unknown
    model (including Imagen).  The fix uses _DALLE_RESPONSE_FORMAT_MODELS.
    """
    from amplifier_module_comic_image_gen.providers.openai_images import (
        OpenAIImageBackend,
        _EDIT_CAPABLE_MODELS,
    )

    provider = make_openai_provider()
    backend = OpenAIImageBackend(provider)

    # Pick any edit-capable model (gpt-image-1 is the canonical case)
    model = "gpt-image-1"
    assert model in _EDIT_CAPABLE_MODELS  # sanity check

    await backend._call_edit(
        model=model,
        prompt="A hero",
        pixel_size="1024x1024",
        reference_images=[],
    )

    call_kwargs = provider.client.images.edit.call_args.kwargs
    assert "response_format" not in call_kwargs, (
        f"_call_edit must not set response_format for {model}; got {call_kwargs}"
    )
