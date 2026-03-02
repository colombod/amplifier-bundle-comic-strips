"""Tests for comic_create(action='review_asset').

Uses TestVisionBackend — a real class following the VisionBackend protocol —
instead of MagicMock provider chains.  This catches interface mismatches
immediately (wrong method name, bad signature) rather than hiding them behind
a mock that accepts anything.

SDK-specific adapter tests (Anthropic/OpenAI/Gemini model routing, correct
client method calls) live in test_vision_backends.py where MagicMock IS
appropriate because we are explicitly testing the SDK adapter layer.
"""

from __future__ import annotations

import json

import pytest

from amplifier_module_comic_create import ComicCreateTool


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

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


async def _setup_with_panel(service, tmp_path):
    """Create project, issue, and a stored panel asset."""
    await service.create_issue("test-proj", "Issue 1")

    ref_path = tmp_path / "panel_01.png"
    ref_path.write_bytes(_PNG)

    await service.store_asset(
        "test-proj",
        "issue-001",
        "panel",
        "panel_01",
        source_path=str(ref_path),
    )
    return "test-proj", "issue-001"


@pytest.mark.asyncio(loop_scope="function")
async def test_review_asset_returns_text_feedback(service, tmp_path) -> None:
    pid, iid = await _setup_with_panel(service, tmp_path)
    feedback_text = "Character proportions are consistent. Framing is correct."
    tool = ComicCreateTool(
        service=service,
        vision_backend=TestVisionBackend(
            response=f'{{"passed": true, "feedback": "{feedback_text}"}}'
        ),
    )

    result = await tool.execute(
        {
            "action": "review_asset",
            "uri": f"comic://{pid}/issues/{iid}/panels/panel_01",
            "prompt": "Check character consistency and framing",
        }
    )

    assert result.success is True
    data = json.loads(result.output)
    assert data["uri"] == f"comic://{pid}/issues/{iid}/panels/panel_01"
    assert "passed" in data
    assert "feedback" in data
    # Verify no base64 in the result
    assert "base64" not in result.output.lower()


@pytest.mark.asyncio(loop_scope="function")
async def test_review_asset_missing_uri(service) -> None:
    tool = ComicCreateTool(service=service)
    result = await tool.execute(
        {
            "action": "review_asset",
            "prompt": "Check quality",
            # missing: uri
        }
    )
    assert result.success is False
    assert "uri" in result.output.lower()


# ---------------------------------------------------------------------------
# Vision backend wiring tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_vision_backend_stored_on_instance(service) -> None:
    """ComicCreateTool accepts and stores a vision_backend kwarg."""
    backend = TestVisionBackend()
    tool = ComicCreateTool(service=service, vision_backend=backend)
    assert tool._vision_backend is backend


@pytest.mark.asyncio(loop_scope="function")
async def test_call_vision_api_no_backend_auto_passes(service) -> None:
    """_call_vision_api auto-passes with descriptive feedback when no backend."""
    tool = ComicCreateTool(service=service, vision_backend=None)
    result = await tool._call_vision_api(["/any/path.png"], "check quality")
    assert result["passed"] is True
    assert "auto" in result["feedback"].lower()


@pytest.mark.asyncio(loop_scope="function")
async def test_call_vision_api_with_test_backend(service, tmp_path) -> None:
    """_call_vision_api reads image bytes and delegates to the backend."""
    img_path = tmp_path / "test.png"
    img_path.write_bytes(_PNG)

    backend = TestVisionBackend(
        response='{"passed": true, "feedback": "PASS: The image quality is good."}'
    )
    tool = ComicCreateTool(service=service, vision_backend=backend)
    result = await tool._call_vision_api([str(img_path)], "Check image quality")

    assert "passed" in result
    assert "feedback" in result
    assert result["passed"] is True
    assert backend.call_count == 1


@pytest.mark.asyncio(loop_scope="function")
async def test_review_asset_calls_vision_backend_no_base64(service, tmp_path) -> None:
    """Full review_asset flow: backend is called, tool result has no base64."""
    pid, iid = await _setup_with_panel(service, tmp_path)

    backend = TestVisionBackend(
        response='{"passed": true, "feedback": "PASS: Looks great."}'
    )
    tool = ComicCreateTool(service=service, vision_backend=backend)
    result = await tool.execute(
        {
            "action": "review_asset",
            "uri": f"comic://{pid}/issues/{iid}/panels/panel_01",
            "prompt": "Check quality",
        }
    )

    assert result.success is True
    # Binary image bytes must never reach the tool output
    assert "base64" not in result.output.lower()
    assert "data:image" not in result.output.lower()
    # The backend must have been called (not the stub)
    assert backend.call_count == 1


@pytest.mark.asyncio(loop_scope="function")
async def test_call_vision_api_backend_failure_auto_passes(service, tmp_path) -> None:
    """If the vision backend raises, _call_vision_api auto-passes gracefully."""
    img_path = tmp_path / "test.png"
    img_path.write_bytes(_PNG)

    class _FailingBackend:
        async def review(self, image_parts, prompt):
            raise RuntimeError("API down")

    tool = ComicCreateTool(service=service, vision_backend=_FailingBackend())
    result = await tool._call_vision_api([str(img_path)], "Check quality")

    assert result["passed"] is True
    assert "auto" in result["feedback"].lower()


@pytest.mark.asyncio(loop_scope="function")
async def test_review_asset_reports_skipped_refs(service, tmp_path) -> None:
    """S-2: Unresolvable reference URIs appear in 'skipped_refs' in the response."""
    await _setup_with_panel(service, tmp_path)

    bad_uri = "comic://nonexistent-proj/issues/issue-001/panels/ghost_panel"
    tool = ComicCreateTool(
        service=service,
        vision_backend=TestVisionBackend(
            response='{"passed": true, "feedback": "Looks fine."}'
        ),
    )
    result = await tool.execute(
        {
            "action": "review_asset",
            "uri": "comic://test-proj/issues/issue-001/panels/panel_01",
            "prompt": "Check consistency",
            "reference_uris": [bad_uri],
        }
    )

    assert result.success is True
    data = json.loads(result.output)
    assert "skipped_refs" in data
    assert bad_uri in data["skipped_refs"]
