"""Tests that base64/data_uri formats and batch_encode are removed from the tools."""
from __future__ import annotations

import base64
import pytest

from amplifier_module_comic_assets import (
    ComicAssetTool,
    ComicCharacterTool,
    ComicProjectTool,
)

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
_PNG_B64 = base64.b64encode(_PNG).decode("ascii")


@pytest.mark.asyncio(loop_scope="function")
async def test_batch_encode_action_rejected(service) -> None:
    """batch_encode should be an unknown action after removal."""
    # First create a project so any possible execution succeeds (not fails due to missing data)
    proj_tool = ComicProjectTool(service)
    await proj_tool.execute({"action": "create_issue", "project": "test_proj", "title": "I1"})

    tool = ComicAssetTool(service)
    result = await tool.execute({
        "action": "batch_encode",
        "project": "test_proj",
        "issue": "issue-001",
        "type": "panel",
    })
    # Before removal: batch_encode action is valid and returns an empty list (success=True).
    # After removal: "Unknown action 'batch_encode'..." (success=False).
    assert result.success is False
    assert "Unknown action" in result.output


@pytest.mark.asyncio(loop_scope="function")
async def test_format_base64_rejected_on_asset(service) -> None:
    """format=base64 should be rejected after removal."""
    # Create project + store an asset so the get would otherwise succeed
    proj_tool = ComicProjectTool(service)
    await proj_tool.execute({"action": "create_issue", "project": "test_proj", "title": "I1"})
    asset_tool = ComicAssetTool(service)
    await asset_tool.execute({
        "action": "store",
        "project": "test_proj",
        "issue": "issue-001",
        "type": "panel",
        "name": "panel_01",
        "data": _PNG_B64,
    })

    # Before removal: format=base64 is accepted and returns image data (success=True).
    # After removal: rejected with error containing "base64" or "format" (success=False).
    result = await asset_tool.execute({
        "action": "get",
        "project": "test_proj",
        "issue": "issue-001",
        "type": "panel",
        "name": "panel_01",
        "format": "base64",
        "include": "full",
    })
    assert result.success is False
    assert "base64" in result.output.lower() or "format" in result.output.lower()


@pytest.mark.asyncio(loop_scope="function")
async def test_format_data_uri_rejected_on_character(service) -> None:
    """format=data_uri should be rejected after removal."""
    # Create project + store a character so the get would otherwise succeed
    proj_tool = ComicProjectTool(service)
    await proj_tool.execute({"action": "create_issue", "project": "test_proj", "title": "I1"})
    char_tool = ComicCharacterTool(service)
    await char_tool.execute({
        "action": "store",
        "project": "test_proj",
        "issue": "issue-001",
        "name": "Explorer",
        "style": "manga",
        "data": _PNG_B64,
        "role": "hero",
        "character_type": "main",
        "bundle": "foundation",
        "visual_traits": "tall",
        "team_markers": "badge",
        "distinctive_features": "scar",
    })

    # Before removal: format=data_uri is accepted and returns image data (success=True).
    # After removal: rejected with error containing "data_uri" or "format" (success=False).
    result = await char_tool.execute({
        "action": "get",
        "project": "test_proj",
        "name": "Explorer",
        "format": "data_uri",
        "include": "full",
    })
    assert result.success is False
    assert "data_uri" in result.output.lower() or "format" in result.output.lower()
