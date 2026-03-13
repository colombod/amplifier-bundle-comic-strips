"""Tests for comic_asset(action='preview')."""
from __future__ import annotations

import json
import pytest

from amplifier_module_comic_assets import ComicAssetTool, ComicProjectTool

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


@pytest.mark.asyncio(loop_scope="function")
async def test_preview_returns_path_and_hint(service, tmp_path) -> None:
    # Setup
    proj_tool = ComicProjectTool(service)
    await proj_tool.execute({"action": "create_issue", "project": "test_proj", "title": "I1"})

    png_path = tmp_path / "panel.png"
    png_path.write_bytes(_PNG)
    await service.store_asset("test_proj", "issue-001", "panel", "panel_01", source_path=str(png_path))

    tool = ComicAssetTool(service)
    result = await tool.execute({
        "action": "preview",
        "project": "test_proj",
        "issue": "issue-001",
        "type": "panel",
        "name": "panel_01",
    })

    assert result.success is True
    data = json.loads(result.output)
    assert "path" in data
    assert "hint" in data
    assert "uri" in data
    assert data["type"] == "image/png"
    # Hint should contain an opener command
    assert "open" in data["hint"] or "xdg-open" in data["hint"]


@pytest.mark.asyncio(loop_scope="function")
async def test_preview_hint_is_platform_appropriate(service, tmp_path) -> None:
    """Preview hint matches the platform: 'open' on macOS, 'xdg-open' on Linux."""
    proj_tool = ComicProjectTool(service)
    await proj_tool.execute({"action": "create_issue", "project": "test_proj", "title": "I1"})

    png_path = tmp_path / "panel.png"
    png_path.write_bytes(_PNG)
    await service.store_asset("test_proj", "issue-001", "panel", "panel_01", source_path=str(png_path))

    tool = ComicAssetTool(service)
    result = await tool.execute({
        "action": "preview",
        "project": "test_proj",
        "issue": "issue-001",
        "type": "panel",
        "name": "panel_01",
    })

    assert result.success is True
    data = json.loads(result.output)
    import platform
    if platform.system() == "Darwin":
        assert data["hint"] == "open"
    else:
        assert data["hint"] == "xdg-open"
