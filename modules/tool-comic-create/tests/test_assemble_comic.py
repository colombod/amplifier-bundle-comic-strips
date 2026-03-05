"""Tests for comic_create(action='assemble_comic')."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from amplifier_module_comic_create import ComicCreateTool

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


async def _setup_with_assets(service, tmp_path):
    """Create a project with a cover and two panels."""
    await service.create_issue("test-proj", "Issue 1")

    for name in ("panel_01", "panel_02"):
        img = tmp_path / f"{name}.png"
        img.write_bytes(_PNG)
        await service.store_asset(
            "test-proj", "issue-001", "panel", name, source_path=str(img)
        )

    cover_img = tmp_path / "cover.png"
    cover_img.write_bytes(_PNG)
    await service.store_asset(
        "test-proj", "issue-001", "cover", "cover", source_path=str(cover_img)
    )

    return "test-proj", "issue-001"


@pytest.mark.asyncio(loop_scope="function")
async def test_assemble_comic_produces_html(service, tmp_path) -> None:
    pid, iid = await _setup_with_assets(service, tmp_path)
    tool = ComicCreateTool(service=service)

    output_path = str(tmp_path / "final-comic.html")

    layout = {
        "title": "Test Comic",
        "cover": {"uri": f"comic://{pid}/issues/{iid}/covers/cover"},
        "pages": [
            {
                "layout": "2x1",
                "panels": [
                    {
                        "uri": f"comic://{pid}/issues/{iid}/panels/panel_01",
                        "overlays": [],
                    },
                    {
                        "uri": f"comic://{pid}/issues/{iid}/panels/panel_02",
                        "overlays": [],
                    },
                ],
            },
        ],
    }

    result = await tool.execute(
        {
            "action": "assemble_comic",
            "project": pid,
            "issue": iid,
            "output_path": output_path,
            "style_uri": f"comic://{pid}/styles/default",
            "layout": layout,
        }
    )

    assert result.success is True
    data = json.loads(result.output)
    assert data["output_path"] == output_path
    assert data["pages"] >= 1
    assert data["images_embedded"] >= 2

    # Verify the HTML file exists and contains base64
    html = Path(output_path).read_text()
    assert "data:image/png;base64," in html
    assert "<!DOCTYPE html>" in html

    # Verify proper structure: navigation, panels, no comic:// URIs
    assert "nav-prev" in html or "Prev" in html  # prev button
    assert "nav-next" in html or "Next" in html  # next button
    assert "page-dot" in html  # page indicator dots
    assert "ArrowLeft" in html  # keyboard support
    assert "touchstart" in html  # touch swipe support
    assert "panel-grid" in html  # panel grid layout
    assert "grid-template-columns" in html  # grid layout applied
    assert "comic://" not in html  # no raw URIs in output


@pytest.mark.asyncio(loop_scope="function")
async def test_assemble_comic_missing_output_path(service) -> None:
    tool = ComicCreateTool(service=service)
    result = await tool.execute(
        {
            "action": "assemble_comic",
            "project": "p",
            "issue": "i",
            # missing: output_path, layout
        }
    )
    assert result.success is False


@pytest.mark.asyncio(loop_scope="function")
async def test_assemble_comic_does_not_auto_store(service, tmp_path) -> None:
    """S-4: assemble_comic must NOT internally call store_asset for the final comic."""
    from unittest.mock import AsyncMock, patch

    pid, iid = await _setup_with_assets(service, tmp_path)
    tool = ComicCreateTool(service=service)

    output_path = str(tmp_path / "final-comic.html")
    layout = {
        "title": "Test Comic",
        "cover": {"uri": f"comic://{pid}/issues/{iid}/covers/cover"},
        "pages": [
            {
                "layout": "1x1",
                "panels": [
                    {
                        "uri": f"comic://{pid}/issues/{iid}/panels/panel_01",
                        "overlays": [],
                    },
                ],
            },
        ],
    }

    with patch.object(service, "store_asset", new_callable=AsyncMock) as mock_store:
        result = await tool.execute(
            {
                "action": "assemble_comic",
                "project": pid,
                "issue": iid,
                "output_path": output_path,
                "layout": layout,
            }
        )

    assert result.success is True
    # store_asset must not have been called by assemble_comic
    mock_store.assert_not_called()
