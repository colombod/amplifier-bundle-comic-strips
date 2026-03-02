"""Tests for comic_create(action='review_asset')."""
from __future__ import annotations

import json
from pathlib import Path
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
        "test-proj", "issue-001", "panel", "panel_01",
        source_path=str(ref_path),
    )
    return "test-proj", "issue-001"


@pytest.mark.asyncio(loop_scope="function")
async def test_review_asset_returns_text_feedback(service, tmp_path) -> None:
    pid, iid = await _setup_with_panel(service, tmp_path)
    tool = ComicCreateTool(service=service)

    # Mock the vision API call that review_asset makes internally
    mock_feedback = "Character proportions are consistent. Framing is correct."
    with patch.object(tool, "_call_vision_api", new_callable=AsyncMock,
                      return_value={"passed": True, "feedback": mock_feedback}):
        result = await tool.execute({
            "action": "review_asset",
            "uri": f"comic://{pid}/{iid}/panel/panel_01",
            "prompt": "Check character consistency and framing",
        })

    assert result.success is True
    data = json.loads(result.output)
    assert data["uri"] == f"comic://{pid}/{iid}/panel/panel_01"
    assert "passed" in data
    assert "feedback" in data
    # Verify no base64 in the result
    assert "base64" not in result.output.lower()


@pytest.mark.asyncio(loop_scope="function")
async def test_review_asset_missing_uri(service) -> None:
    tool = ComicCreateTool(service=service)
    result = await tool.execute({
        "action": "review_asset",
        "prompt": "Check quality",
        # missing: uri
    })
    assert result.success is False
    assert "uri" in result.output.lower()
