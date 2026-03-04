"""Tests: new coordinator-based provider API for vision.

These tests describe and verify the TARGET state after the refactor:
  1. ComicCreateTool.__init__ accepts `coordinator` (not `vision_backend`)
  2. _call_vision_api takes pre-prepared image_parts dicts (ZERO file I/O)
  3. _find_vision_provider queries coordinator.get("providers") for vision caps
  4. _review_asset is the orchestrator that reads bytes and prepares image_parts

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


# ---------------------------------------------------------------------------
# TEST 1: ComicCreateTool accepts coordinator= parameter
# ---------------------------------------------------------------------------


def test_tool_accepts_coordinator_param(service) -> None:
    """ComicCreateTool.__init__ accepts coordinator kwarg and stores as _coordinator."""
    coordinator = FakeCoordinator()
    tool = ComicCreateTool(service=service, coordinator=coordinator)
    assert tool._coordinator is coordinator


def test_tool_coordinator_defaults_to_none(service) -> None:
    """coordinator defaults to None when not provided."""
    tool = ComicCreateTool(service=service)
    assert tool._coordinator is None


# ---------------------------------------------------------------------------
# TEST 2: _call_vision_api takes pre-prepared image_parts (ZERO file I/O)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_call_vision_api_takes_prepared_image_parts(
    service,
) -> None:
    """_call_vision_api receives pre-prepared image_parts dicts (no file paths)."""
    provider = FakeVisionProvider(response_text='{"passed": true, "feedback": "All good."}')
    coordinator = FakeCoordinator(vision_provider=provider)
    tool = ComicCreateTool(service=service, coordinator=coordinator)

    b64_data = base64.b64encode(_PNG).decode("ascii")
    image_parts = [{"type": "base64", "media_type": "image/png", "data": b64_data}]

    result = await tool._call_vision_api(image_parts, "Check quality")

    assert result["passed"] is True
    assert result["feedback"] == "All good."
    assert provider.call_count == 1


@pytest.mark.asyncio(loop_scope="function")
async def test_call_vision_api_no_coordinator_auto_passes(service) -> None:
    """_call_vision_api auto-passes when coordinator is None."""
    tool = ComicCreateTool(service=service, coordinator=None)

    b64_data = base64.b64encode(_PNG).decode("ascii")
    image_parts = [{"type": "base64", "media_type": "image/png", "data": b64_data}]

    result = await tool._call_vision_api(image_parts, "Check quality")

    assert result["passed"] is True
    assert "auto" in result["feedback"].lower()


@pytest.mark.asyncio(loop_scope="function")
async def test_call_vision_api_no_vision_provider_auto_passes(service) -> None:
    """_call_vision_api auto-passes when coordinator has no vision-capable provider."""
    coordinator = FakeCoordinator()  # no provider
    tool = ComicCreateTool(service=service, coordinator=coordinator)

    b64_data = base64.b64encode(_PNG).decode("ascii")
    image_parts = [{"type": "base64", "media_type": "image/png", "data": b64_data}]

    result = await tool._call_vision_api(image_parts, "Check quality")

    assert result["passed"] is True
    assert "auto" in result["feedback"].lower()


# ---------------------------------------------------------------------------
# TEST 3: _find_vision_provider method exists
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_find_vision_provider_returns_provider_and_model(service) -> None:
    """_find_vision_provider returns (provider, model) from coordinator."""
    provider = FakeVisionProvider()
    coordinator = FakeCoordinator(vision_provider=provider)
    tool = ComicCreateTool(service=service, coordinator=coordinator)

    found_provider, model = await tool._find_vision_provider()

    assert found_provider is provider
    assert model == "fake-vision-model"


@pytest.mark.asyncio(loop_scope="function")
async def test_find_vision_provider_returns_none_none_when_no_coordinator(service) -> None:
    """_find_vision_provider returns (None, None) when coordinator is None."""
    tool = ComicCreateTool(service=service, coordinator=None)
    found_provider, model = await tool._find_vision_provider()
    assert found_provider is None
    assert model is None


# ---------------------------------------------------------------------------
# TEST 4: _review_asset orchestrates — reads bytes, prepares image_parts,
# passes to _call_vision_api (which now receives prepared dicts)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_review_asset_passes_prepared_image_parts_to_provider(
    service, tmp_path
) -> None:
    """_review_asset reads file, base64-encodes, passes prepared dicts to provider."""
    await service.create_issue("test-proj", "Issue 1")
    ref_path = tmp_path / "panel_01.png"
    ref_path.write_bytes(_PNG)
    await service.store_asset(
        "test-proj", "issue-001", "panel", "panel_01", source_path=str(ref_path)
    )

    provider = FakeVisionProvider(response_text='{"passed": true, "feedback": "Good."}')
    coordinator = FakeCoordinator(vision_provider=provider)
    tool = ComicCreateTool(service=service, coordinator=coordinator)

    result = await tool.execute(
        {
            "action": "review_asset",
            "uri": "comic://test-proj/issues/issue-001/panels/panel_01",
            "prompt": "Check quality",
        }
    )

    assert result.success is True
    # Provider must have been called
    assert provider.call_count == 1
    # The request should contain ImageBlock objects (via provider.complete())
    request = provider.last_request
    assert request is not None
    # Content should contain image and text blocks
    content = request.messages[0].content
    assert len(content) >= 2  # at least one image + one text


@pytest.mark.asyncio(loop_scope="function")
async def test_review_asset_with_coordinator_none_auto_passes(
    service, tmp_path
) -> None:
    """review_asset auto-passes (success=True) when coordinator=None."""
    await service.create_issue("test-proj", "Issue 1")
    ref_path = tmp_path / "panel_01.png"
    ref_path.write_bytes(_PNG)
    await service.store_asset(
        "test-proj", "issue-001", "panel", "panel_01", source_path=str(ref_path)
    )

    tool = ComicCreateTool(service=service, coordinator=None)
    result = await tool.execute(
        {
            "action": "review_asset",
            "uri": "comic://test-proj/issues/issue-001/panels/panel_01",
            "prompt": "Check quality",
        }
    )

    assert result.success is True
    data = json.loads(result.output)
    assert data["passed"] is True
    assert "auto" in data["feedback"].lower()


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


def test_fake_vision_provider_matches_provider_protocol() -> None:
    """If Provider protocol changes, this test fails immediately.

    FakeVisionProvider uses real amplifier_core Pydantic types.
    isinstance() checks structural compatibility at runtime.
    """
    from amplifier_core import Provider

    provider = FakeVisionProvider()
    assert isinstance(provider, Provider), (
        "FakeVisionProvider does not satisfy the real Provider protocol. "
        "Update FakeVisionProvider to match the current protocol definition."
    )
