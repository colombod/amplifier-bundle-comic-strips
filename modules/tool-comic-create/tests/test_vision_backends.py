"""Tests for concrete VisionBackend implementations.

Each backend wraps one SDK — AnthropicVisionBackend, OpenAIVisionBackend,
GeminiVisionBackend.  MagicMock is appropriate here because we are testing
the *SDK adapter layer* in isolation: the only contract is that each backend
calls the correct SDK method with correctly-shaped arguments and returns the
text string from the response.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


# ---------------------------------------------------------------------------
# AnthropicVisionBackend
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_anthropic_backend_calls_messages_create() -> None:
    """AnthropicVisionBackend.review() calls client.messages.create with correct args."""
    from amplifier_module_comic_create.vision_backends import AnthropicVisionBackend

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Looks great.")]

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    backend = AnthropicVisionBackend(client=mock_client, model="claude-opus-4-5")
    image_parts = [{"data": "abc123", "media_type": "image/png"}]
    result = await backend.review(image_parts, "Check quality.")

    assert result == "Looks great."
    mock_client.messages.create.assert_called_once()
    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-opus-4-5"
    assert call_kwargs["max_tokens"] == 1024
    # Should have one message with role=user
    msgs = call_kwargs["messages"]
    assert len(msgs) == 1
    assert msgs[0]["role"] == "user"
    # Content should have image + text
    content = msgs[0]["content"]
    assert any(p.get("type") == "image" for p in content)
    assert any(p.get("type") == "text" for p in content)


@pytest.mark.asyncio(loop_scope="function")
async def test_anthropic_backend_uses_custom_model() -> None:
    """AnthropicVisionBackend uses the model passed to __init__."""
    from amplifier_module_comic_create.vision_backends import AnthropicVisionBackend

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="ok")]

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    backend = AnthropicVisionBackend(client=mock_client, model="claude-custom-model")
    await backend.review([{"data": "x", "media_type": "image/png"}], "prompt")

    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-custom-model"


# ---------------------------------------------------------------------------
# OpenAIVisionBackend
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_openai_backend_calls_chat_completions() -> None:
    """OpenAIVisionBackend.review() calls client.chat.completions.create correctly."""
    from amplifier_module_comic_create.vision_backends import OpenAIVisionBackend

    mock_choice = MagicMock()
    mock_choice.message.content = "Image passes review."
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    backend = OpenAIVisionBackend(client=mock_client, model="gpt-4o")
    image_parts = [{"data": "abc123", "media_type": "image/png"}]
    result = await backend.review(image_parts, "Check quality.")

    assert result == "Image passes review."
    mock_client.chat.completions.create.assert_called_once()
    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "gpt-4o"
    assert call_kwargs["max_tokens"] == 1024
    msgs = call_kwargs["messages"]
    assert len(msgs) == 1
    assert msgs[0]["role"] == "user"
    # Content should contain image_url part and text part
    content = msgs[0]["content"]
    assert any(p.get("type") == "image_url" for p in content)
    assert any(p.get("type") == "text" for p in content)


@pytest.mark.asyncio(loop_scope="function")
async def test_openai_backend_uses_custom_model() -> None:
    """OpenAIVisionBackend uses the model passed to __init__."""
    from amplifier_module_comic_create.vision_backends import OpenAIVisionBackend

    mock_choice = MagicMock()
    mock_choice.message.content = "ok"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    backend = OpenAIVisionBackend(client=mock_client, model="gpt-4o-mini")
    await backend.review([{"data": "x", "media_type": "image/png"}], "prompt")

    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "gpt-4o-mini"


# ---------------------------------------------------------------------------
# GeminiVisionBackend
# ---------------------------------------------------------------------------

# Valid base64 — "AAAA" decodes to b"\x00\x00\x00" (3 null bytes), which is
# fine for creating a Part from bytes in the SDK.
_VALID_B64 = "AAAA"


@pytest.mark.asyncio(loop_scope="function")
async def test_gemini_backend_calls_generate_content() -> None:
    """GeminiVisionBackend.review() calls client.aio.models.generate_content correctly."""
    from amplifier_module_comic_create.vision_backends import GeminiVisionBackend

    mock_response = MagicMock()
    mock_response.text = "Image quality is acceptable."

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    backend = GeminiVisionBackend(client=mock_client, model="gemini-2.0-flash")
    image_parts = [{"data": _VALID_B64, "media_type": "image/png"}]
    result = await backend.review(image_parts, "Check quality.")

    assert result == "Image quality is acceptable."
    mock_client.aio.models.generate_content.assert_called_once()
    call_kwargs = mock_client.aio.models.generate_content.call_args.kwargs
    assert call_kwargs["model"] == "gemini-2.0-flash"


@pytest.mark.asyncio(loop_scope="function")
async def test_gemini_backend_uses_custom_model() -> None:
    """GeminiVisionBackend uses the model passed to __init__."""
    from amplifier_module_comic_create.vision_backends import GeminiVisionBackend

    mock_response = MagicMock()
    mock_response.text = "ok"

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    backend = GeminiVisionBackend(client=mock_client, model="gemini-1.5-pro")
    await backend.review([{"data": _VALID_B64, "media_type": "image/png"}], "prompt")

    call_kwargs = mock_client.aio.models.generate_content.call_args.kwargs
    assert call_kwargs["model"] == "gemini-1.5-pro"


# ---------------------------------------------------------------------------
# ComicCreateTool wiring — vision_backend param
# ---------------------------------------------------------------------------


def test_comic_create_tool_accepts_vision_backend_param() -> None:
    """ComicCreateTool.__init__ accepts vision_backend and stores it as _vision_backend."""
    from amplifier_module_comic_create import ComicCreateTool

    mock_service = MagicMock()

    class _FakeBackend:
        async def review(self, image_parts, prompt):
            return '{"passed": true, "feedback": "ok"}'

    backend = _FakeBackend()
    tool = ComicCreateTool(service=mock_service, vision_backend=backend)
    assert tool._vision_backend is backend


@pytest.mark.asyncio(loop_scope="function")
async def test_call_vision_api_delegates_to_vision_backend(tmp_path) -> None:
    """_call_vision_api calls backend.review() and parses its JSON response."""
    from amplifier_module_comic_create import ComicCreateTool
    from amplifier_module_comic_create.vision_backends import AnthropicVisionBackend

    # Write a minimal PNG
    _PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    img_path = tmp_path / "test.png"
    img_path.write_bytes(_PNG)

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"passed": true, "feedback": "All good."}')]
    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    backend = AnthropicVisionBackend(client=mock_client, model="claude-opus-4-5")
    tool = ComicCreateTool(service=MagicMock(), vision_backend=backend)

    result = await tool._call_vision_api([str(img_path)], "Check quality")
    assert result["passed"] is True
    assert result["feedback"] == "All good."
