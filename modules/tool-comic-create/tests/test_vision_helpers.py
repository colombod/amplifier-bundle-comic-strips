"""Tests for vision helper improvements.

Covers:
  Fix 1: Module-level vision model constants
  Fix 2: _detect_mime module-level helper
  Fix 3: Structured JSON response parsing with keyword fallback

Why TestVisionBackend (not MagicMock) for the parsing tests:
  _call_vision_api's job is (1) read & encode images, (2) call backend.review(),
  (3) parse the text response.  By injecting specific response strings via
  TestVisionBackend we test step (3) deterministically without any real API
  calls and without hiding the review() interface behind a MagicMock.

  SDK-specific model routing tests (Anthropic/OpenAI/Gemini) live in
  test_vision_backends.py where MagicMock IS appropriate because those tests
  target the SDK adapter layer, not the _call_vision_api parsing logic.
"""

from __future__ import annotations

import pytest


class TestVisionBackend:
    """Real class following VisionBackend protocol — no MagicMock."""

    __test__ = False  # prevent pytest from treating this as a test class

    def __init__(
        self, response: str = '{"passed": true, "feedback": "Looks good."}'
    ) -> None:
        self.response = response
        self.call_count = 0
        self.last_prompt: str | None = None

    async def review(
        self, image_parts: list[dict[str, str]], prompt: str
    ) -> str:
        self.call_count += 1
        self.last_prompt = prompt
        return self.response


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

    backend = TestVisionBackend(
        response='{"passed": true, "feedback": "All checks passed successfully."}'
    )
    tool = ComicCreateTool(service=service, vision_backend=backend)
    result = await tool._call_vision_api([str(img_path)], "Check quality")

    assert result["passed"] is True
    assert result["feedback"] == "All checks passed successfully."


@pytest.mark.asyncio(loop_scope="function")
async def test_call_vision_api_parses_json_passed_false(service, tmp_path) -> None:
    """JSON response with passed=false is parsed and returned as passed=False."""
    from amplifier_module_comic_create import ComicCreateTool

    img_path = tmp_path / "test.png"
    img_path.write_bytes(_PNG)

    backend = TestVisionBackend(
        response='{"passed": false, "feedback": "Character proportions are off."}'
    )
    tool = ComicCreateTool(service=service, vision_backend=backend)
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
    backend = TestVisionBackend(
        response='{"passed": true, "feedback": "The characters do not fail to match the style."}'
    )
    tool = ComicCreateTool(service=service, vision_backend=backend)
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

    backend = TestVisionBackend(
        response="This image does not pass quality review."
    )
    tool = ComicCreateTool(service=service, vision_backend=backend)
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
    backend = TestVisionBackend(
        response='Here is my assessment: {"passed": false, "feedback": "Too dark overall."} End of review.'
    )
    tool = ComicCreateTool(service=service, vision_backend=backend)
    result = await tool._call_vision_api([str(img_path)], "Check quality")

    assert result["passed"] is False
    assert result["feedback"] == "Too dark overall."
