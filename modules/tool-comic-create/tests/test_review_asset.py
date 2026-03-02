"""Tests for comic_create(action='review_asset')."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from amplifier_module_comic_create import ComicCreateTool

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
    tool = ComicCreateTool(service=service)

    # Mock the vision API call that review_asset makes internally
    mock_feedback = "Character proportions are consistent. Framing is correct."
    with patch.object(
        tool,
        "_call_vision_api",
        new_callable=AsyncMock,
        return_value={"passed": True, "feedback": mock_feedback},
    ):
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
# New tests: wired vision provider
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_vision_provider_stored_on_instance(service) -> None:
    """ComicCreateTool accepts and stores a vision_provider kwarg."""
    mock_provider = MagicMock()
    tool = ComicCreateTool(service=service, vision_provider=mock_provider)
    assert tool._vision_provider is mock_provider


@pytest.mark.asyncio(loop_scope="function")
async def test_call_vision_api_no_provider_auto_passes(service) -> None:
    """_call_vision_api auto-passes with descriptive feedback when no provider."""
    tool = ComicCreateTool(service=service, vision_provider=None)
    result = await tool._call_vision_api(["/any/path.png"], "check quality")
    assert result["passed"] is True
    assert "auto" in result["feedback"].lower()


@pytest.mark.asyncio(loop_scope="function")
async def test_call_vision_api_with_anthropic_provider(service, tmp_path) -> None:
    """_call_vision_api reads image bytes and calls Anthropic messages.create."""
    img_path = tmp_path / "test.png"
    img_path.write_bytes(_PNG)

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="PASS: The image quality is good.")]

    mock_client = MagicMock()
    mock_client.messages = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    mock_provider = MagicMock()
    mock_provider.name = "anthropic"
    mock_provider.client = mock_client

    tool = ComicCreateTool(service=service, vision_provider=mock_provider)
    result = await tool._call_vision_api([str(img_path)], "Check image quality")

    assert "passed" in result
    assert "feedback" in result
    assert "PASS" in result["feedback"]
    mock_client.messages.create.assert_called_once()


@pytest.mark.asyncio(loop_scope="function")
async def test_review_asset_calls_vision_provider_no_base64(service, tmp_path) -> None:
    """Full review_asset flow: vision provider is called, tool result has no base64."""
    pid, iid = await _setup_with_panel(service, tmp_path)

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="PASS: Looks great.")]

    mock_client = MagicMock()
    mock_client.messages = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    mock_provider = MagicMock()
    mock_provider.name = "anthropic"
    mock_provider.client = mock_client

    tool = ComicCreateTool(service=service, vision_provider=mock_provider)
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
    # The vision provider client must have been called (not the stub)
    mock_client.messages.create.assert_called_once()


@pytest.mark.asyncio(loop_scope="function")
async def test_call_vision_api_provider_failure_auto_passes(service, tmp_path) -> None:
    """If the vision provider call raises, _call_vision_api auto-passes gracefully."""
    img_path = tmp_path / "test.png"
    img_path.write_bytes(_PNG)

    mock_client = MagicMock()
    mock_client.messages = MagicMock()
    mock_client.messages.create = AsyncMock(side_effect=RuntimeError("API down"))

    mock_provider = MagicMock()
    mock_provider.name = "anthropic"
    mock_provider.client = mock_client

    tool = ComicCreateTool(service=service, vision_provider=mock_provider)
    result = await tool._call_vision_api([str(img_path)], "Check quality")

    assert result["passed"] is True
    assert "auto" in result["feedback"].lower()


@pytest.mark.asyncio(loop_scope="function")
async def test_review_asset_reports_skipped_refs(service, tmp_path) -> None:
    """S-2: Unresolvable reference URIs appear in 'skipped_refs' in the response."""
    await _setup_with_panel(service, tmp_path)
    tool = ComicCreateTool(service=service)

    bad_uri = "comic://nonexistent-proj/issues/issue-001/panels/ghost_panel"
    mock_feedback = "Looks fine."
    with patch.object(
        tool,
        "_call_vision_api",
        new_callable=AsyncMock,
        return_value={"passed": True, "feedback": mock_feedback},
    ):
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
