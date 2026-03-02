"""Tests for vision helper improvements.

Covers:
  Fix 1: Module-level vision model constants + configurable via vision_models dict
  Fix 2: _detect_mime module-level helper
  Fix 3: Structured JSON response parsing with keyword fallback
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Fix 1: Vision model constants
# ---------------------------------------------------------------------------


def test_vision_model_constants_exist() -> None:
    """Module exports the three vision model constants."""
    import amplifier_module_comic_create as m

    assert hasattr(m, "_VISION_MODEL_ANTHROPIC"), "Missing _VISION_MODEL_ANTHROPIC"
    assert hasattr(m, "_VISION_MODEL_OPENAI"), "Missing _VISION_MODEL_OPENAI"
    assert hasattr(m, "_VISION_MODEL_GOOGLE"), "Missing _VISION_MODEL_GOOGLE"


def test_vision_model_constant_default_values() -> None:
    """Default model names match known stable model strings."""
    import amplifier_module_comic_create as m

    assert m._VISION_MODEL_ANTHROPIC == "claude-opus-4-5"
    assert m._VISION_MODEL_OPENAI == "gpt-4o"
    assert m._VISION_MODEL_GOOGLE == "gemini-2.0-flash"


def test_comic_create_tool_accepts_vision_models_kwarg() -> None:
    """ComicCreateTool.__init__ accepts an optional vision_models dict."""
    from amplifier_module_comic_create import ComicCreateTool

    service = MagicMock()
    custom_models = {
        "anthropic": "claude-custom-model",
        "openai": "gpt-4o-mini",
        "google": "gemini-1.5-pro",
    }
    tool = ComicCreateTool(service=service, vision_models=custom_models)
    assert tool._vision_models == custom_models


def test_comic_create_tool_vision_models_defaults_to_constants() -> None:
    """When vision_models is not supplied, tool defaults to the module constants."""
    import amplifier_module_comic_create as m
    from amplifier_module_comic_create import ComicCreateTool

    service = MagicMock()
    tool = ComicCreateTool(service=service)
    assert tool._vision_models["anthropic"] == m._VISION_MODEL_ANTHROPIC
    assert tool._vision_models["openai"] == m._VISION_MODEL_OPENAI
    assert tool._vision_models["google"] == m._VISION_MODEL_GOOGLE


@pytest.mark.asyncio(loop_scope="function")
async def test_invoke_vision_anthropic_uses_vision_models_dict(service) -> None:
    """_invoke_vision_provider passes model from _vision_models to Anthropic API."""
    from amplifier_module_comic_create import ComicCreateTool

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Looks great.")]
    mock_client = MagicMock()
    mock_client.messages = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    mock_provider = MagicMock()
    mock_provider.name = "anthropic"
    mock_provider.client = mock_client

    custom_models = {
        "anthropic": "claude-custom-model",
        "openai": "gpt-4o",
        "google": "gemini-2.0-flash",
    }
    tool = ComicCreateTool(
        service=service, vision_provider=mock_provider, vision_models=custom_models
    )

    image_parts = [{"data": "abc123", "media_type": "image/png"}]
    await tool._invoke_vision_provider(image_parts, "Check this.")

    call_kwargs = mock_client.messages.create.call_args
    assert call_kwargs.kwargs["model"] == "claude-custom-model"


@pytest.mark.asyncio(loop_scope="function")
async def test_invoke_vision_openai_uses_vision_models_dict(service) -> None:
    """_invoke_vision_provider passes model from _vision_models to OpenAI API."""
    from amplifier_module_comic_create import ComicCreateTool

    mock_choice = MagicMock()
    mock_choice.message.content = "Looks great."
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat = MagicMock()
    mock_client.chat.completions = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    mock_provider = MagicMock()
    mock_provider.name = "openai"
    mock_provider.client = mock_client

    custom_models = {
        "anthropic": "claude-opus-4-5",
        "openai": "gpt-4o-mini",
        "google": "gemini-2.0-flash",
    }
    tool = ComicCreateTool(
        service=service, vision_provider=mock_provider, vision_models=custom_models
    )

    image_parts = [{"data": "abc123", "media_type": "image/png"}]
    await tool._invoke_vision_provider(image_parts, "Check this.")

    call_kwargs = mock_client.chat.completions.create.call_args
    assert call_kwargs.kwargs["model"] == "gpt-4o-mini"


# ---------------------------------------------------------------------------
# Fix 2: _detect_mime helper
# ---------------------------------------------------------------------------


def test_detect_mime_function_exists() -> None:
    """Module exports _detect_mime as a callable."""
    import amplifier_module_comic_create as m

    assert hasattr(m, "_detect_mime"), "Missing _detect_mime"
    assert callable(m._detect_mime)


def test_detect_mime_png() -> None:
    from amplifier_module_comic_create import _detect_mime

    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    assert _detect_mime(png_bytes) == "image/png"


def test_detect_mime_jpeg() -> None:
    from amplifier_module_comic_create import _detect_mime

    jpeg_bytes = b"\xff\xd8\xff" + b"\x00" * 100
    assert _detect_mime(jpeg_bytes) == "image/jpeg"


def test_detect_mime_webp() -> None:
    from amplifier_module_comic_create import _detect_mime

    webp_bytes = b"RIFF" + b"\x00" * 4 + b"WEBP" + b"\x00" * 100
    assert _detect_mime(webp_bytes) == "image/webp"


def test_detect_mime_unknown_falls_back_to_png() -> None:
    from amplifier_module_comic_create import _detect_mime

    unknown_bytes = b"\x00\x01\x02\x03" + b"\x00" * 100
    assert _detect_mime(unknown_bytes) == "image/png"


# ---------------------------------------------------------------------------
# Fix 3: Structured JSON output parsing
# ---------------------------------------------------------------------------

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


@pytest.mark.asyncio(loop_scope="function")
async def test_call_vision_api_parses_json_passed_true(service, tmp_path) -> None:
    """JSON response with passed=true is parsed and returned as passed=True."""
    from amplifier_module_comic_create import ComicCreateTool

    img_path = tmp_path / "test.png"
    img_path.write_bytes(_PNG)

    json_response = '{"passed": true, "feedback": "All checks passed successfully."}'
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json_response)]
    mock_client = MagicMock()
    mock_client.messages = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    mock_provider = MagicMock()
    mock_provider.name = "anthropic"
    mock_provider.client = mock_client

    tool = ComicCreateTool(service=service, vision_provider=mock_provider)
    result = await tool._call_vision_api([str(img_path)], "Check quality")

    assert result["passed"] is True
    assert result["feedback"] == "All checks passed successfully."


@pytest.mark.asyncio(loop_scope="function")
async def test_call_vision_api_parses_json_passed_false(service, tmp_path) -> None:
    """JSON response with passed=false is parsed and returned as passed=False."""
    from amplifier_module_comic_create import ComicCreateTool

    img_path = tmp_path / "test.png"
    img_path.write_bytes(_PNG)

    json_response = '{"passed": false, "feedback": "Character proportions are off."}'
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json_response)]
    mock_client = MagicMock()
    mock_client.messages = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    mock_provider = MagicMock()
    mock_provider.name = "anthropic"
    mock_provider.client = mock_client

    tool = ComicCreateTool(service=service, vision_provider=mock_provider)
    result = await tool._call_vision_api([str(img_path)], "Check quality")

    assert result["passed"] is False
    assert result["feedback"] == "Character proportions are off."


@pytest.mark.asyncio(loop_scope="function")
async def test_call_vision_api_json_avoids_false_positive(service, tmp_path) -> None:
    """JSON parsing avoids false-positive: 'do not fail' with passed=true stays True."""
    from amplifier_module_comic_create import ComicCreateTool

    img_path = tmp_path / "test.png"
    img_path.write_bytes(_PNG)

    # This text WOULD trigger keyword detection ("fail") but JSON explicitly says passed=true
    json_response = (
        '{"passed": true, "feedback": "The characters do not fail to match the style."}'
    )
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json_response)]
    mock_client = MagicMock()
    mock_client.messages = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    mock_provider = MagicMock()
    mock_provider.name = "anthropic"
    mock_provider.client = mock_client

    tool = ComicCreateTool(service=service, vision_provider=mock_provider)
    result = await tool._call_vision_api([str(img_path)], "Check quality")

    # JSON says true — keyword "fail" must NOT override this
    assert result["passed"] is True


@pytest.mark.asyncio(loop_scope="function")
async def test_call_vision_api_falls_back_to_keyword_when_no_json(
    service, tmp_path
) -> None:
    """When response has no JSON, keyword detection is used as fallback."""
    from amplifier_module_comic_create import ComicCreateTool

    img_path = tmp_path / "test.png"
    img_path.write_bytes(_PNG)

    plain_response = "This image does not pass quality review."
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=plain_response)]
    mock_client = MagicMock()
    mock_client.messages = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    mock_provider = MagicMock()
    mock_provider.name = "anthropic"
    mock_provider.client = mock_client

    tool = ComicCreateTool(service=service, vision_provider=mock_provider)
    result = await tool._call_vision_api([str(img_path)], "Check quality")

    # "not pass" keyword → failed=True → passed=False
    assert result["passed"] is False


@pytest.mark.asyncio(loop_scope="function")
async def test_call_vision_api_json_in_prose_wrapper(service, tmp_path) -> None:
    """JSON embedded in prose (before/after text) is extracted and parsed."""
    from amplifier_module_comic_create import ComicCreateTool

    img_path = tmp_path / "test.png"
    img_path.write_bytes(_PNG)

    # Model may wrap JSON in prose — we should still extract it
    prose_response = 'Here is my assessment: {"passed": false, "feedback": "Too dark overall."} End of review.'
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=prose_response)]
    mock_client = MagicMock()
    mock_client.messages = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    mock_provider = MagicMock()
    mock_provider.name = "anthropic"
    mock_provider.client = mock_client

    tool = ComicCreateTool(service=service, vision_provider=mock_provider)
    result = await tool._call_vision_api([str(img_path)], "Check quality")

    assert result["passed"] is False
    assert result["feedback"] == "Too dark overall."
