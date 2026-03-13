"""Tests for cast page auto-population and overlay auto-layout.

Fix 1: assemble_comic auto-populates layout["characters"] from the project's
       character roster when the agent omits it, so the cast page renders.

Fix 2: render_overlay_svg distributes bubbles across the panel when the agent
       omits position coordinates, instead of stacking them all at (10, 10).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from amplifier_module_comic_create import ComicCreateTool
from amplifier_module_comic_create.html_renderer import render_overlay_svg

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


async def _setup_project_with_characters_and_panels(service, tmp_path):
    """Create a project with 2 characters, a cover, and 2 panels."""
    await service.create_issue("test-proj", "Issue 1")

    # Store two characters with reference images
    for name, slug in [("Explorer", "explorer"), ("Bug Hunter", "bug-hunter")]:
        ref = tmp_path / f"ref_{slug}.png"
        ref.write_bytes(_PNG)
        await service.store_character(
            "test-proj",
            "issue-001",
            name,
            "manga",
            role="protagonist",
            character_type="main",
            bundle="foundation",
            visual_traits=f"{name} visual traits",
            team_markers="blue badge",
            distinctive_features=f"{name} features",
            backstory=f"{name} is a seasoned agent.",
            source_path=str(ref),
        )

    # Store panels and cover
    for asset_name in ("panel_01", "panel_02"):
        img = tmp_path / f"{asset_name}.png"
        img.write_bytes(_PNG)
        await service.store_asset(
            "test-proj", "issue-001", "panel", asset_name, source_path=str(img)
        )

    cover = tmp_path / "cover.png"
    cover.write_bytes(_PNG)
    await service.store_asset(
        "test-proj", "issue-001", "cover", "cover", source_path=str(cover)
    )

    return "test-proj", "issue-001"


# ---------------------------------------------------------------------------
# Fix 1: Cast page auto-population
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_assemble_auto_populates_characters_for_cast_page(
    service, tmp_path, image_gen
) -> None:
    """When layout has no 'characters' key, assemble_comic should auto-populate
    from the project's character roster so the cast page renders."""
    pid, iid = await _setup_project_with_characters_and_panels(service, tmp_path)
    tool = ComicCreateTool(service=service, image_gen=image_gen)

    output_path = str(tmp_path / "comic.html")
    layout = {
        "title": "Test Comic",
        "cover": {"uri": f"comic://{pid}/issues/{iid}/covers/cover"},
        # NOTE: no "characters" key — the tool should auto-populate it
        "pages": [
            {
                "layout": "2x1",
                "panels": [
                    {"uri": f"comic://{pid}/issues/{iid}/panels/panel_01", "overlays": []},
                    {"uri": f"comic://{pid}/issues/{iid}/panels/panel_02", "overlays": []},
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
            "layout": layout,
        }
    )
    assert result.success is True

    html = Path(output_path).read_text()
    # Cast page should be present with character names
    assert "character-intro-page" in html
    assert "Explorer" in html
    assert "Bug Hunter" in html


@pytest.mark.asyncio(loop_scope="function")
async def test_assemble_respects_explicit_characters(
    service, tmp_path, image_gen
) -> None:
    """When layout already has 'characters', the tool should NOT override it."""
    pid, iid = await _setup_project_with_characters_and_panels(service, tmp_path)
    tool = ComicCreateTool(service=service, image_gen=image_gen)

    output_path = str(tmp_path / "comic.html")
    layout = {
        "title": "Test Comic",
        "cover": {"uri": f"comic://{pid}/issues/{iid}/covers/cover"},
        "characters": [
            {"name": "Custom Hero", "role": "Lead", "backstory": "A custom character."},
        ],
        "pages": [
            {
                "layout": "2x1",
                "panels": [
                    {"uri": f"comic://{pid}/issues/{iid}/panels/panel_01", "overlays": []},
                    {"uri": f"comic://{pid}/issues/{iid}/panels/panel_02", "overlays": []},
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
            "layout": layout,
        }
    )
    assert result.success is True

    html = Path(output_path).read_text()
    assert "Custom Hero" in html
    # Should NOT contain the auto-populated characters
    assert "Explorer" not in html


# ---------------------------------------------------------------------------
# Fix 2: Overlay auto-layout
# ---------------------------------------------------------------------------


def test_overlay_auto_layout_distributes_bubbles() -> None:
    """Overlays without position data should get distinct positions, not all (10,10)."""
    overlays = [
        {"text": "First line", "shape": "oval"},
        {"text": "Second line", "shape": "oval"},
        {"text": "Third line", "shape": "oval"},
    ]
    results = [
        render_overlay_svg(ov, index=i, total=len(overlays))
        for i, ov in enumerate(overlays)
    ]
    # Extract left: percentages from the style attributes
    lefts = []
    for html in results:
        # Find left:N% in the style string
        import re
        m = re.search(r"left:(\d+)%", html)
        assert m, f"No left: found in: {html[:200]}"
        lefts.append(int(m.group(1)))

    # They should NOT all be the same (the old default was all 10%)
    assert len(set(lefts)) > 1, f"All bubbles at same x: {lefts}"


def test_overlay_auto_layout_alternates_sides() -> None:
    """Auto-layout should alternate bubbles left/right for readability."""
    overlays = [
        {"text": "Speaker A", "shape": "oval"},
        {"text": "Speaker B", "shape": "oval"},
    ]
    results = [
        render_overlay_svg(ov, index=i, total=len(overlays))
        for i, ov in enumerate(overlays)
    ]
    import re
    lefts = []
    for html in results:
        m = re.search(r"left:(\d+)%", html)
        assert m
        lefts.append(int(m.group(1)))

    # First bubble should be on the left side (<50), second on right (>=50)
    assert lefts[0] < 50, f"First bubble not on left: {lefts[0]}"
    assert lefts[1] >= 50, f"Second bubble not on right: {lefts[1]}"


def test_overlay_explicit_position_preserved() -> None:
    """When position is explicitly provided, auto-layout should NOT override it."""
    overlay = {
        "text": "Hello",
        "shape": "oval",
        "position": {"x": 70, "y": 25, "width": 25, "height": 15},
    }
    html = render_overlay_svg(overlay, index=0, total=1)
    assert "left:70%" in html
    assert "top:25%" in html
