"""Tests for vision helper functions in comic_create.

Covers:
  - _detect_mime module-level helper (pure function — no fixtures needed)
  - Structured JSON response parsing with keyword fallback via _call_vision_api
  - _call_vision_api passes pre-prepared image_parts (ZERO file I/O)

Why FakeVisionProvider (not a custom backend shim) for the parsing tests:
  _call_vision_api's job is (1) find a vision provider via coordinator,
  (2) build a request with pre-prepared image_parts, (3) call provider.complete(),
  (4) parse the text response.  By injecting specific response strings via
  FakeVisionProvider we test step (4) deterministically without any real API
  calls and with real amplifier_core types catching protocol mismatches.

  amplifier_core is installed as a dev dependency so the full
  _call_vision_api → provider.complete() path uses the real types directly.
"""

from __future__ import annotations

import base64

import pytest

from tests.conftest import FakeCoordinator, FakeVisionProvider

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


# ---------------------------------------------------------------------------
# _detect_mime helper
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
# JSON response parsing via _call_vision_api
# ---------------------------------------------------------------------------


def _prepared_parts() -> list[dict[str, str]]:
    """Return pre-prepared image_parts for testing _call_vision_api directly."""
    b64 = base64.b64encode(_PNG).decode("ascii")
    return [{"type": "base64", "media_type": "image/png", "data": b64}]


@pytest.mark.asyncio(loop_scope="function")
async def test_call_vision_api_parses_json_passed_true(
    service
) -> None:
    """JSON response with passed=true is parsed and returned as passed=True."""
    from amplifier_module_comic_create import ComicCreateTool

    provider = FakeVisionProvider(
        response_text='{"passed": true, "feedback": "All checks passed successfully."}'
    )
    tool = ComicCreateTool(
        service=service,
        coordinator=FakeCoordinator(vision_provider=provider),
    )
    result = await tool._call_vision_api(_prepared_parts(), "Check quality")

    assert result["passed"] is True
    assert result["feedback"] == "All checks passed successfully."


@pytest.mark.asyncio(loop_scope="function")
async def test_call_vision_api_parses_json_passed_false(
    service
) -> None:
    """JSON response with passed=false is parsed and returned as passed=False."""
    from amplifier_module_comic_create import ComicCreateTool

    provider = FakeVisionProvider(
        response_text='{"passed": false, "feedback": "Character proportions are off."}'
    )
    tool = ComicCreateTool(
        service=service,
        coordinator=FakeCoordinator(vision_provider=provider),
    )
    result = await tool._call_vision_api(_prepared_parts(), "Check quality")

    assert result["passed"] is False
    assert result["feedback"] == "Character proportions are off."


@pytest.mark.asyncio(loop_scope="function")
async def test_call_vision_api_json_avoids_false_positive(
    service
) -> None:
    """JSON parsing avoids false-positive: 'do not fail' with passed=true stays True."""
    from amplifier_module_comic_create import ComicCreateTool

    # This text WOULD trigger keyword detection ("fail") but JSON explicitly says passed=true
    provider = FakeVisionProvider(
        response_text='{"passed": true, "feedback": "The characters do not fail to match the style."}'
    )
    tool = ComicCreateTool(
        service=service,
        coordinator=FakeCoordinator(vision_provider=provider),
    )
    result = await tool._call_vision_api(_prepared_parts(), "Check quality")

    # JSON says true — keyword "fail" must NOT override this
    assert result["passed"] is True


@pytest.mark.asyncio(loop_scope="function")
async def test_call_vision_api_falls_back_to_keyword_when_no_json(
    service
) -> None:
    """When response has no JSON, keyword detection is used as fallback."""
    from amplifier_module_comic_create import ComicCreateTool

    provider = FakeVisionProvider(
        response_text="This image does not pass quality review."
    )
    tool = ComicCreateTool(
        service=service,
        coordinator=FakeCoordinator(vision_provider=provider),
    )
    result = await tool._call_vision_api(_prepared_parts(), "Check quality")

    # "not pass" keyword → failed=True → passed=False
    assert result["passed"] is False


@pytest.mark.asyncio(loop_scope="function")
async def test_call_vision_api_json_in_prose_wrapper(
    service
) -> None:
    """JSON embedded in prose (before/after text) is extracted and parsed."""
    from amplifier_module_comic_create import ComicCreateTool

    # Model may wrap JSON in prose — we should still extract it
    provider = FakeVisionProvider(
        response_text='Here is my assessment: {"passed": false, "feedback": "Too dark overall."} End of review.'
    )
    tool = ComicCreateTool(
        service=service,
        coordinator=FakeCoordinator(vision_provider=provider),
    )
    result = await tool._call_vision_api(_prepared_parts(), "Check quality")

    assert result["passed"] is False
    assert result["feedback"] == "Too dark overall."


@pytest.mark.asyncio(loop_scope="function")
async def test_call_vision_api_takes_pre_prepared_parts_no_file_io(
    service
) -> None:
    """_call_vision_api accepts pre-prepared image_parts dicts — ZERO file I/O."""
    from amplifier_module_comic_create import ComicCreateTool

    provider = FakeVisionProvider(
        response_text='{"passed": true, "feedback": "Clean."}'
    )
    tool = ComicCreateTool(
        service=service,
        coordinator=FakeCoordinator(vision_provider=provider),
    )

    # Pass pre-prepared dicts directly — no file path involved
    b64 = base64.b64encode(_PNG).decode("ascii")
    image_parts = [{"type": "base64", "media_type": "image/png", "data": b64}]

    result = await tool._call_vision_api(image_parts, "Check quality")

    assert result["passed"] is True
    assert provider.call_count == 1
