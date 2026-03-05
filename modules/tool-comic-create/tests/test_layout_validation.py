"""Tests for layout validation — list_layouts action and assemble_comic rejection.

Covers Phase 1 of the tool enforcement plan: agents must get loud, helpful
errors when they use invalid layout IDs, and must be able to discover valid
layouts programmatically.
"""

from __future__ import annotations

import json

import pytest

from amplifier_module_comic_create import ComicCreateTool


# ---------------------------------------------------------------------------
# list_layouts action
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_list_layouts_returns_grouped_primary(service) -> None:
    """list_layouts must return primary layouts grouped by panel count."""
    tool = ComicCreateTool(service=service)
    result = await tool.execute({"action": "list_layouts"})
    assert result.success is True
    data = json.loads(result.output)
    primary = data["primary_layouts"]
    # String keys from JSON — check at least 1 through 6
    for count in ("1", "2", "3", "4", "5", "6"):
        assert count in primary, f"Missing {count}-panel group"


@pytest.mark.asyncio(loop_scope="function")
async def test_list_layouts_includes_hint(service) -> None:
    """Response should include a usage hint for agents."""
    tool = ComicCreateTool(service=service)
    result = await tool.execute({"action": "list_layouts"})
    data = json.loads(result.output)
    assert "hint" in data


# ---------------------------------------------------------------------------
# assemble_comic layout validation gate
# ---------------------------------------------------------------------------


def _make_layout_with_pages(*layout_ids: str) -> dict:
    """Build a minimal layout object with the given page layout IDs."""
    return {
        "title": "Test Comic",
        "pages": [
            {
                "layout": lid,
                "panels": [{"uri": f"comic://test/panel-{i}"}],
            }
            for i, lid in enumerate(layout_ids)
        ],
    }


@pytest.mark.asyncio(loop_scope="function")
async def test_assemble_rejects_invalid_layout_ids(service) -> None:
    """assemble_comic must reject layouts with invalid IDs before doing any work."""
    tool = ComicCreateTool(service=service)
    layout = _make_layout_with_pages("naruto_wide_3", "2p-split")
    result = await tool.execute(
        {
            "action": "assemble_comic",
            "project": "test",
            "issue": "001",
            "output_path": "/tmp/test.html",
            "layout": layout,
        }
    )
    assert result.success is False
    error = json.loads(result.output)
    assert "naruto_wide_3" in error["invalid_layout_ids"]
    assert "suggestions" in error
    # Suggestions should include 3-panel primary layouts
    assert any(s.startswith("3p-") for s in error["suggestions"]["naruto_wide_3"])
    assert "hint" in error


@pytest.mark.asyncio(loop_scope="function")
async def test_assemble_accepts_valid_layout_ids(service) -> None:
    """assemble_comic must pass validation when all layout IDs are valid.

    We expect downstream failure (missing image URIs) but NOT a layout
    validation error — proving the gate passed.
    """
    tool = ComicCreateTool(service=service)
    layout = _make_layout_with_pages("2p-split", "3p-top-wide")
    result = await tool.execute(
        {
            "action": "assemble_comic",
            "project": "test",
            "issue": "001",
            "output_path": "/tmp/test.html",
            "layout": layout,
        }
    )
    # If it fails, it should NOT be a layout validation error
    if not result.success:
        output = result.output
        if isinstance(output, str):
            assert "invalid_layout_ids" not in output.lower()


@pytest.mark.asyncio(loop_scope="function")
async def test_assemble_rejects_multiple_invalid_ids(service) -> None:
    """All invalid layout IDs must be reported in a single error."""
    tool = ComicCreateTool(service=service)
    layout = _make_layout_with_pages("bogus_1", "fake_layout", "2p-split")
    result = await tool.execute(
        {
            "action": "assemble_comic",
            "project": "test",
            "issue": "001",
            "output_path": "/tmp/test.html",
            "layout": layout,
        }
    )
    assert result.success is False
    error = json.loads(result.output)
    assert "bogus_1" in error["invalid_layout_ids"]
    assert "fake_layout" in error["invalid_layout_ids"]
    assert len(error["invalid_layout_ids"]) == 2


# ---------------------------------------------------------------------------
# validate_storyboard action
# ---------------------------------------------------------------------------


def _make_page_layouts(*layout_ids: str) -> list[dict]:
    """Build a minimal page_layouts array with the given layout IDs."""
    return [
        {"page": i + 1, "layout": lid, "panel_count": 3}
        for i, lid in enumerate(layout_ids)
    ]


@pytest.mark.asyncio(loop_scope="function")
async def test_validate_storyboard_passes_valid_layouts(service) -> None:
    """validate_storyboard must pass when all layout IDs are valid."""
    tool = ComicCreateTool(service=service)
    result = await tool.execute(
        {
            "action": "validate_storyboard",
            "page_layouts": _make_page_layouts("2p-split", "3p-top-wide", "4p-grid"),
        }
    )
    assert result.success is True
    data = json.loads(result.output)
    assert data["validation"] == "PASSED"
    assert data["page_count"] == 3


@pytest.mark.asyncio(loop_scope="function")
async def test_validate_storyboard_rejects_invalid_layouts(service) -> None:
    """validate_storyboard must reject invalid layout IDs with suggestions."""
    tool = ComicCreateTool(service=service)
    result = await tool.execute(
        {
            "action": "validate_storyboard",
            "page_layouts": _make_page_layouts("naruto_wide_3", "2p-split"),
        }
    )
    assert result.success is False
    error = json.loads(result.output)
    assert error["validation"] == "FAILED"
    assert "naruto_wide_3" in error["invalid_layout_ids"]
    assert "suggestions" in error
    assert any(s.startswith("3p-") for s in error["suggestions"]["naruto_wide_3"])


@pytest.mark.asyncio(loop_scope="function")
async def test_validate_storyboard_missing_page_layouts(service) -> None:
    """validate_storyboard must error when page_layouts is missing."""
    tool = ComicCreateTool(service=service)
    result = await tool.execute({"action": "validate_storyboard"})
    assert result.success is False
    assert "page_layouts" in result.output.lower()


@pytest.mark.asyncio(loop_scope="function")
async def test_validate_storyboard_reports_valid_ids_used(service) -> None:
    """On failure, response must include the valid IDs that passed."""
    tool = ComicCreateTool(service=service)
    result = await tool.execute(
        {
            "action": "validate_storyboard",
            "page_layouts": _make_page_layouts("bad_layout", "2p-split", "4p-grid"),
        }
    )
    assert result.success is False
    error = json.loads(result.output)
    assert "2p-split" in error["valid_ids_used"]
    assert "4p-grid" in error["valid_ids_used"]
