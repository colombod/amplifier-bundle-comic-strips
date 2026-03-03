"""Tests for comic_create(action='review_asset').

Uses FakeVisionProvider — a strict test double built on real amplifier_core types
— instead of MagicMock chains or custom backend shims.  This catches interface
mismatches immediately (wrong method name, bad signature) rather than hiding
them behind a mock that accepts anything.

amplifier_core is installed as a dev dependency so the full
_call_vision_api → provider.complete() path is exercised with the real types.
"""

from __future__ import annotations

import base64
import json

import pytest

from amplifier_module_comic_create import ComicCreateTool
from tests.conftest import FakeCoordinator, FakeVisionProvider

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


# ---------------------------------------------------------------------------
# Auto-pass scenarios (no provider needed)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_review_asset_auto_passes_no_coordinator(service, tmp_path) -> None:
    """review_asset succeeds and auto-passes when coordinator=None."""
    pid, iid = await _setup_with_panel(service, tmp_path)
    tool = ComicCreateTool(service=service, coordinator=None)

    result = await tool.execute(
        {
            "action": "review_asset",
            "uri": f"comic://{pid}/issues/{iid}/panels/panel_01",
            "prompt": "Check quality",
        }
    )

    assert result.success is True
    data = json.loads(result.output)
    assert data["passed"] is True
    assert "auto" in data["feedback"].lower()


@pytest.mark.asyncio(loop_scope="function")
async def test_review_asset_auto_passes_no_vision_provider(service, tmp_path) -> None:
    """review_asset auto-passes when coordinator has no vision-capable provider."""
    pid, iid = await _setup_with_panel(service, tmp_path)
    coordinator = FakeCoordinator()  # no vision provider
    tool = ComicCreateTool(service=service, coordinator=coordinator)

    result = await tool.execute(
        {
            "action": "review_asset",
            "uri": f"comic://{pid}/issues/{iid}/panels/panel_01",
            "prompt": "Check quality",
        }
    )

    assert result.success is True
    data = json.loads(result.output)
    assert data["passed"] is True


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
# Full path: provider is called with prepared image data
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_review_asset_calls_provider_with_image_parts(
    service, tmp_path
) -> None:
    """review_asset reads image, base64-encodes, passes prepared parts to provider."""
    pid, iid = await _setup_with_panel(service, tmp_path)

    provider = FakeVisionProvider(
        response_text='{"passed": true, "feedback": "Looks great."}'
    )
    coordinator = FakeCoordinator(vision_provider=provider)
    tool = ComicCreateTool(service=service, coordinator=coordinator)

    result = await tool.execute(
        {
            "action": "review_asset",
            "uri": f"comic://{pid}/issues/{iid}/panels/panel_01",
            "prompt": "Check quality",
        }
    )

    assert result.success is True
    assert provider.call_count == 1
    # No base64 in the tool result
    assert "base64" not in result.output.lower()
    assert "data:image" not in result.output.lower()


@pytest.mark.asyncio(loop_scope="function")
async def test_review_asset_request_has_image_and_text_blocks(
    service, tmp_path
) -> None:
    """The request passed to provider.complete() has image blocks + a text block."""
    pid, iid = await _setup_with_panel(service, tmp_path)

    provider = FakeVisionProvider(
        response_text='{"passed": true, "feedback": "Good framing."}'
    )
    coordinator = FakeCoordinator(vision_provider=provider)
    tool = ComicCreateTool(service=service, coordinator=coordinator)

    await tool.execute(
        {
            "action": "review_asset",
            "uri": f"comic://{pid}/issues/{iid}/panels/panel_01",
            "prompt": "Check framing",
        }
    )

    request = provider.last_request
    assert request is not None
    content = request.messages[0].content
    # Should have at least one image block and one text block
    types_seen = {getattr(block, "type", None) for block in content}
    assert "image" in types_seen
    assert "text" in types_seen


@pytest.mark.asyncio(loop_scope="function")
async def test_review_asset_image_parts_contain_base64_data(
    service, tmp_path
) -> None:
    """The image block source contains base64-encoded data (not file path)."""
    pid, iid = await _setup_with_panel(service, tmp_path)

    provider = FakeVisionProvider(
        response_text='{"passed": true, "feedback": "Good."}'
    )
    coordinator = FakeCoordinator(vision_provider=provider)
    tool = ComicCreateTool(service=service, coordinator=coordinator)

    await tool.execute(
        {
            "action": "review_asset",
            "uri": f"comic://{pid}/issues/{iid}/panels/panel_01",
            "prompt": "Check quality",
        }
    )

    request = provider.last_request
    content = request.messages[0].content
    image_blocks = [b for b in content if getattr(b, "type", None) == "image"]
    assert len(image_blocks) == 1

    source = image_blocks[0].source
    assert source["type"] == "base64"
    assert source["media_type"] == "image/png"
    # Verify the data is valid base64 for our PNG
    decoded = base64.b64decode(source["data"])
    assert decoded[:8] == b"\x89PNG\r\n\x1a\n"


@pytest.mark.asyncio(loop_scope="function")
async def test_review_asset_returns_text_feedback(
    service, tmp_path
) -> None:
    """Full review_asset flow returns structured feedback from provider."""
    pid, iid = await _setup_with_panel(service, tmp_path)
    feedback_text = "Character proportions are consistent. Framing is correct."
    provider = FakeVisionProvider(
        response_text=f'{{"passed": true, "feedback": "{feedback_text}"}}'
    )
    coordinator = FakeCoordinator(vision_provider=provider)
    tool = ComicCreateTool(service=service, coordinator=coordinator)

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
    assert data["passed"] is True
    assert data["feedback"] == feedback_text
    # Verify no base64 in the result
    assert "base64" not in result.output.lower()


# ---------------------------------------------------------------------------
# _call_vision_api direct tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_call_vision_api_no_coordinator_auto_passes(service) -> None:
    """_call_vision_api auto-passes with descriptive feedback when coordinator=None."""
    tool = ComicCreateTool(service=service, coordinator=None)
    b64 = base64.b64encode(_PNG).decode("ascii")
    result = await tool._call_vision_api(
        [{"type": "base64", "media_type": "image/png", "data": b64}],
        "check quality",
    )
    assert result["passed"] is True
    assert "auto" in result["feedback"].lower()


@pytest.mark.asyncio(loop_scope="function")
async def test_call_vision_api_with_provider(service) -> None:
    """_call_vision_api delegates to provider.complete() and parses response."""
    provider = FakeVisionProvider(
        response_text='{"passed": true, "feedback": "PASS: The image quality is good."}'
    )
    coordinator = FakeCoordinator(vision_provider=provider)
    tool = ComicCreateTool(service=service, coordinator=coordinator)

    b64 = base64.b64encode(_PNG).decode("ascii")
    result = await tool._call_vision_api(
        [{"type": "base64", "media_type": "image/png", "data": b64}],
        "Check image quality",
    )

    assert result["passed"] is True
    assert result["feedback"] == "PASS: The image quality is good."
    assert provider.call_count == 1


@pytest.mark.asyncio(loop_scope="function")
async def test_call_vision_api_provider_failure_auto_passes(
    service,
) -> None:
    """If provider.complete() raises, _call_vision_api auto-passes gracefully."""

    class _FailingProvider:
        name = "failing"

        def get_info(self):
            return type("Info", (), {"capabilities": ["vision"], "capability_tags": ["vision"]})()

        async def list_models(self):
            return [type("M", (), {"id": "m", "capabilities": ["vision"], "capability_tags": ["vision"]})()]

        async def complete(self, request):
            raise RuntimeError("API down")

    coordinator = FakeCoordinator(vision_provider=_FailingProvider())
    tool = ComicCreateTool(service=service, coordinator=coordinator)

    b64 = base64.b64encode(_PNG).decode("ascii")
    result = await tool._call_vision_api(
        [{"type": "base64", "media_type": "image/png", "data": b64}],
        "Check quality",
    )

    assert result["passed"] is True
    assert "auto" in result["feedback"].lower()


# ---------------------------------------------------------------------------
# Coordinator stored on instance
# ---------------------------------------------------------------------------


def test_coordinator_stored_on_instance(service) -> None:
    """ComicCreateTool accepts and stores a coordinator kwarg."""
    coordinator = FakeCoordinator()
    tool = ComicCreateTool(service=service, coordinator=coordinator)
    assert tool._coordinator is coordinator


def test_coordinator_defaults_to_none(service) -> None:
    """coordinator defaults to None when not provided."""
    tool = ComicCreateTool(service=service)
    assert tool._coordinator is None


# ---------------------------------------------------------------------------
# Skipped refs
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_review_asset_reports_skipped_refs(service, tmp_path) -> None:
    """S-2: Unresolvable reference URIs appear in 'skipped_refs' in the response."""
    await _setup_with_panel(service, tmp_path)

    bad_uri = "comic://nonexistent-proj/issues/issue-001/panels/ghost_panel"
    coordinator = FakeCoordinator()  # no vision — auto-pass is fine for skipped_refs test
    tool = ComicCreateTool(service=service, coordinator=coordinator)

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
