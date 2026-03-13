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


# ---------------------------------------------------------------------------
# get_layout_slot_count
# ---------------------------------------------------------------------------


class TestGetLayoutSlotCount:
    """Tests for the get_layout_slot_count() helper."""

    def test_primary_1_panel(self) -> None:
        """1p-splash must return 1."""
        from amplifier_module_comic_create.html_renderer import get_layout_slot_count

        assert get_layout_slot_count("1p-splash") == 1

    def test_primary_2_panel(self) -> None:
        """All 6 primary 2-panel layouts must return 2."""
        from amplifier_module_comic_create.html_renderer import get_layout_slot_count

        layouts = [
            "2p-split",
            "2p-top-heavy",
            "2p-bottom-heavy",
            "2p-vertical",
            "2p-left-heavy",
            "2p-right-heavy",
        ]
        for lid in layouts:
            assert get_layout_slot_count(lid) == 2, f"{lid!r} should return 2"

    def test_primary_3_panel(self) -> None:
        """All 9 primary 3-panel layouts must return 3."""
        from amplifier_module_comic_create.html_renderer import get_layout_slot_count

        layouts = [
            "3p-rows",
            "3p-top-wide",
            "3p-bottom-wide",
            "3p-columns",
            "3p-left-dominant",
            "3p-right-dominant",
            "3p-hero-top",
            "3p-hero-bottom",
            "3p-cinematic",
        ]
        for lid in layouts:
            assert get_layout_slot_count(lid) == 3, f"{lid!r} should return 3"

    def test_primary_4_panel(self) -> None:
        """All 4 primary 4-panel layouts must return 4."""
        from amplifier_module_comic_create.html_renderer import get_layout_slot_count

        layouts = [
            "4p-grid",
            "4p-top-strip",
            "4p-bottom-strip",
            "4p-stacked",
        ]
        for lid in layouts:
            assert get_layout_slot_count(lid) == 4, f"{lid!r} should return 4"

    def test_primary_5_panel(self) -> None:
        """All 3 primary 5-panel layouts must return 5."""
        from amplifier_module_comic_create.html_renderer import get_layout_slot_count

        layouts = [
            "5p-classic",
            "5p-hero-grid",
            "5p-stacked",
        ]
        for lid in layouts:
            assert get_layout_slot_count(lid) == 5, f"{lid!r} should return 5"

    def test_primary_6_panel(self) -> None:
        """All 4 primary 6-panel layouts must return 6."""
        from amplifier_module_comic_create.html_renderer import get_layout_slot_count

        layouts = [
            "6p-classic",
            "6p-wide",
            "6p-manga",
            "6p-dense",
        ]
        for lid in layouts:
            assert get_layout_slot_count(lid) == 6, f"{lid!r} should return 6"

    def test_legacy_aliases_spot_check(self) -> None:
        """Spot-check a selection of legacy aliases across all panel counts."""
        from amplifier_module_comic_create.html_renderer import get_layout_slot_count

        cases = {
            "1x1": 1,
            "full-bleed": 1,
            "hero_splash": 1,
            "1x2": 2,
            "manga_dynamic_2": 2,
            "3-row": 3,
            "manga_widescreen": 3,
            "2x2": 4,
            "corner_focus": 4,
            "hero_plus_grid": 5,
            "t_shape": 5,
            "3x2": 6,
            "cinematic_widescreen": 6,
            "stacked_wides": 4,
            "grid_9": 9,
            "classic_9": 9,
        }
        for lid, expected in cases.items():
            assert get_layout_slot_count(lid) == expected, (
                f"{lid!r} should return {expected}"
            )

    def test_every_grid_template_has_count(self) -> None:
        """Every layout in _GRID_TEMPLATES must return a valid integer count >= 1."""
        from amplifier_module_comic_create.html_renderer import (
            _GRID_TEMPLATES,
            get_layout_slot_count,
        )

        for lid in _GRID_TEMPLATES:
            count = get_layout_slot_count(lid)
            assert isinstance(count, int), f"{lid!r} returned non-int: {count!r}"
            assert count >= 1, f"{lid!r} returned count < 1: {count}"

    def test_unknown_layout_raises_value_error(self) -> None:
        """An unknown layout ID must raise ValueError with a descriptive message."""
        from amplifier_module_comic_create.html_renderer import get_layout_slot_count

        with pytest.raises(ValueError, match="unknown"):
            get_layout_slot_count("naruto_wide_99")


# ---------------------------------------------------------------------------
# find_best_layout
# ---------------------------------------------------------------------------


class TestFindBestLayout:
    """Tests for find_best_layout() helper."""

    def test_returns_primary_layout_for_counts_1_to_6(self) -> None:
        """For each panel count 1-6, find_best_layout must return a matching primary layout."""
        from amplifier_module_comic_create.html_renderer import find_best_layout

        for count in range(1, 7):
            result = find_best_layout(count)
            assert result.startswith(f"{count}p-"), (
                f"find_best_layout({count}) returned {result!r}, "
                f"expected a layout starting with '{count}p-'"
            )

    def test_valid_layout_for_9_panels(self) -> None:
        """find_best_layout(9) must return a valid entry in _GRID_TEMPLATES."""
        from amplifier_module_comic_create.html_renderer import (
            _GRID_TEMPLATES,
            find_best_layout,
        )

        result = find_best_layout(9)
        assert result in _GRID_TEMPLATES, (
            f"find_best_layout(9) returned {result!r}, which is not in _GRID_TEMPLATES"
        )

    def test_valid_layout_for_7_panels(self) -> None:
        """find_best_layout(7) must return a valid entry in _GRID_TEMPLATES."""
        from amplifier_module_comic_create.html_renderer import (
            _GRID_TEMPLATES,
            find_best_layout,
        )

        result = find_best_layout(7)
        assert result in _GRID_TEMPLATES, (
            f"find_best_layout(7) returned {result!r}, which is not in _GRID_TEMPLATES"
        )

    def test_valid_layout_for_8_panels(self) -> None:
        """find_best_layout(8) must return a valid entry in _GRID_TEMPLATES."""
        from amplifier_module_comic_create.html_renderer import (
            _GRID_TEMPLATES,
            find_best_layout,
        )

        result = find_best_layout(8)
        assert result in _GRID_TEMPLATES, (
            f"find_best_layout(8) returned {result!r}, which is not in _GRID_TEMPLATES"
        )

    def test_prefers_simple_layouts(self) -> None:
        """find_best_layout must prefer simpler layouts via _SIMPLE_LAYOUT_PREFERENCE.

        4 panels -> 4p-grid (grid ranks higher than stacked/others)
        6 panels -> 6p-classic (classic ranks higher than wide/manga/dense)
        """
        from amplifier_module_comic_create.html_renderer import find_best_layout

        assert find_best_layout(4) == "4p-grid", (
            f"find_best_layout(4) should return '4p-grid', got {find_best_layout(4)!r}"
        )
        assert find_best_layout(6) == "6p-classic", (
            f"find_best_layout(6) should return '6p-classic', got {find_best_layout(6)!r}"
        )

    def test_single_panel_returns_1p_splash(self) -> None:
        """find_best_layout(1) must return '1p-splash'."""
        from amplifier_module_comic_create.html_renderer import find_best_layout

        assert find_best_layout(1) == "1p-splash"

    def test_result_always_in_grid_templates(self) -> None:
        """For any panel count 1-9, find_best_layout must return a key in _GRID_TEMPLATES."""
        from amplifier_module_comic_create.html_renderer import (
            _GRID_TEMPLATES,
            find_best_layout,
        )

        for count in range(1, 10):
            result = find_best_layout(count)
            assert result in _GRID_TEMPLATES, (
                f"find_best_layout({count}) returned {result!r}, "
                "which is not a key in _GRID_TEMPLATES"
            )


# ---------------------------------------------------------------------------
# validate_storyboard with panel_list — Phase 2 auto-correction tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_validate_storyboard_corrects_mismatched_layouts(service) -> None:
    """When panel_list shows page 1 has 2 panels but layout is 3p-top-wide, correct it."""
    tool = ComicCreateTool(service=service)
    page_layouts = [{"page": 1, "layout": "3p-top-wide", "panel_count": 3}]
    panel_list = [
        {"page": 1, "scene": "Opening"},
        {"page": 1, "scene": "Action"},
    ]
    result = await tool.execute(
        {
            "action": "validate_storyboard",
            "page_layouts": page_layouts,
            "panel_list": panel_list,
        }
    )
    assert result.success is True
    data = json.loads(result.output)
    assert data["validation"] == "CORRECTED"
    assert len(data["corrections"]) == 1
    correction = data["corrections"][0]
    assert correction["page"] == 1
    assert correction["original_layout"] == "3p-top-wide"
    assert correction["actual_panels"] == 2
    assert correction["corrected_layout"].startswith("2p-")


@pytest.mark.asyncio(loop_scope="function")
async def test_validate_storyboard_no_correction_when_counts_match(service) -> None:
    """When panel_list matches page layouts, validation is PASSED with empty corrections."""
    tool = ComicCreateTool(service=service)
    page_layouts = [{"page": 1, "layout": "3p-top-wide", "panel_count": 3}]
    panel_list = [
        {"page": 1, "scene": "Opening"},
        {"page": 1, "scene": "Action"},
        {"page": 1, "scene": "Cliffhanger"},
    ]
    result = await tool.execute(
        {
            "action": "validate_storyboard",
            "page_layouts": page_layouts,
            "panel_list": panel_list,
        }
    )
    assert result.success is True
    data = json.loads(result.output)
    assert data["validation"] == "PASSED"
    assert data["corrections"] == []


@pytest.mark.asyncio(loop_scope="function")
async def test_validate_storyboard_returns_corrected_page_layouts(service) -> None:
    """Returns corrected_page_layouts with fixed layout and panel_count for mismatched pages."""
    tool = ComicCreateTool(service=service)
    page_layouts = [
        {"page": 1, "layout": "3p-top-wide", "panel_count": 3},
        {"page": 2, "layout": "4p-grid", "panel_count": 4},
    ]
    # Page 1 has 2 panels (mismatch with 3p-top-wide), page 2 has 4 panels (matches 4p-grid)
    panel_list = [
        {"page": 1, "scene": "Opening"},
        {"page": 1, "scene": "Action"},
        {"page": 2, "scene": "Scene 1"},
        {"page": 2, "scene": "Scene 2"},
        {"page": 2, "scene": "Scene 3"},
        {"page": 2, "scene": "Scene 4"},
    ]
    result = await tool.execute(
        {
            "action": "validate_storyboard",
            "page_layouts": page_layouts,
            "panel_list": panel_list,
        }
    )
    assert result.success is True
    data = json.loads(result.output)
    assert data["validation"] == "CORRECTED"
    corrected = data["corrected_page_layouts"]
    assert len(corrected) == 2
    # Page 1 corrected
    page1 = corrected[0]
    assert page1["layout"].startswith("2p-")
    assert page1["panel_count"] == 2
    # Page 2 unchanged
    page2 = corrected[1]
    assert page2["layout"] == "4p-grid"
    assert page2["panel_count"] == 4


@pytest.mark.asyncio(loop_scope="function")
async def test_validate_storyboard_backward_compat_without_panel_list(service) -> None:
    """Without panel_list, validate_storyboard behaves as before (Phase 1 only)."""
    tool = ComicCreateTool(service=service)
    # Original behavior: valid layouts → PASSED
    result = await tool.execute(
        {
            "action": "validate_storyboard",
            "page_layouts": [{"page": 1, "layout": "3p-top-wide", "panel_count": 3}],
        }
    )
    assert result.success is True
    data = json.loads(result.output)
    assert data["validation"] == "PASSED"
    # Original behavior: invalid layout → FAILED
    result2 = await tool.execute(
        {
            "action": "validate_storyboard",
            "page_layouts": [
                {"page": 1, "layout": "not_a_real_layout", "panel_count": 3}
            ],
        }
    )
    assert result2.success is False
    data2 = json.loads(result2.output)
    assert data2["validation"] == "FAILED"
