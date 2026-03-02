"""Tests for html_renderer — SVG bubbles, navigation, style, and layout.

RED phase: all tests should fail until html_renderer.py is implemented.
"""

from __future__ import annotations


from amplifier_module_comic_create.html_renderer import (
    render_comic_html,
    render_overlay_svg,
)


# ---------------------------------------------------------------------------
# render_overlay_svg — speech bubble shapes
# ---------------------------------------------------------------------------


def test_oval_bubble_svg_has_ellipse_and_tail() -> None:
    """Oval bubble must contain an <ellipse> and a tail path/polygon."""
    overlay = {
        "type": "speech",
        "shape": "oval",
        "text": "Hello!",
        "position": {"x": 10, "y": 10, "width": 30, "height": 20},
        "tail": {"points_to": {"x": 50, "y": 80}},
    }
    html = render_overlay_svg(overlay)
    assert "<ellipse" in html
    # Tail can be a <polygon> or <path> element
    assert "<polygon" in html or "<path" in html
    assert "Hello!" in html


def test_oval_bubble_uses_percentage_position() -> None:
    """Overlay container must be positioned using % values from the spec."""
    overlay = {
        "type": "speech",
        "shape": "oval",
        "text": "Hi",
        "position": {"x": 20, "y": 35, "width": 40, "height": 25},
        "tail": {"points_to": {"x": 50, "y": 70}},
    }
    html = render_overlay_svg(overlay)
    assert "left:20%" in html or "left: 20%" in html
    assert "top:35%" in html or "top: 35%" in html


def test_rectangular_caption_has_no_tail() -> None:
    """Rectangular caption box (narrator) must NOT have a tail element."""
    overlay = {
        "type": "caption",
        "shape": "rectangular",
        "text": "Meanwhile…",
        "position": {"x": 5, "y": 5, "width": 90, "height": 15},
    }
    html = render_overlay_svg(overlay)
    # Should have a rect
    assert "<rect" in html
    # Must NOT have a tail
    assert "tail" not in html.lower() or (
        "<polygon" not in html and "<path" not in html and "tail-path" not in html
    )
    assert "Meanwhile" in html


def test_cloud_bubble_has_circles() -> None:
    """Thought bubble (cloud) must use multiple circles for the scalloped edge."""
    overlay = {
        "type": "thought",
        "shape": "cloud",
        "text": "I wonder…",
        "position": {"x": 10, "y": 10, "width": 35, "height": 25},
        "tail": {"points_to": {"x": 20, "y": 90}},
    }
    html = render_overlay_svg(overlay)
    # Cloud edge is made of circles, count at least 3 <circle> elements
    assert html.count("<circle") >= 3
    assert "I wonder" in html


def test_jagged_bubble_has_spiky_polygon() -> None:
    """Jagged (shout) bubble must use a <polygon> with many points."""
    overlay = {
        "type": "speech",
        "shape": "jagged",
        "text": "WATCH OUT!",
        "position": {"x": 15, "y": 10, "width": 40, "height": 30},
        "tail": {"points_to": {"x": 60, "y": 70}},
    }
    html = render_overlay_svg(overlay)
    assert "<polygon" in html
    assert "WATCH OUT!" in html


def test_whisper_bubble_has_dashed_stroke() -> None:
    """Whisper bubble must have a stroke-dasharray attribute."""
    overlay = {
        "type": "speech",
        "shape": "whisper",
        "text": "psst…",
        "position": {"x": 5, "y": 5, "width": 25, "height": 15},
        "tail": {"points_to": {"x": 30, "y": 60}},
    }
    html = render_overlay_svg(overlay)
    assert "stroke-dasharray" in html
    assert "psst" in html


# ---------------------------------------------------------------------------
# render_comic_html — page navigation
# ---------------------------------------------------------------------------

_MINIMAL_LAYOUT = {
    "title": "Test Comic",
    "pages": [
        {
            "layout": "1x1",
            "panels": [
                {
                    "uri": "comic://p/issues/i/panels/p1",
                    "overlays": [],
                }
            ],
        },
        {
            "layout": "1x1",
            "panels": [
                {
                    "uri": "comic://p/issues/i/panels/p2",
                    "overlays": [],
                }
            ],
        },
    ],
}

_RESOLVED = {
    "comic://p/issues/i/panels/p1": "data:image/png;base64,abc",
    "comic://p/issues/i/panels/p2": "data:image/png;base64,def",
}


def test_navigation_prev_next_buttons_present() -> None:
    """HTML must include previous and next navigation buttons."""
    html = render_comic_html(_MINIMAL_LAYOUT, _RESOLVED)
    html_lower = html.lower()
    assert "prev" in html_lower or "previous" in html_lower
    assert "next" in html_lower


def test_navigation_page_dots_present() -> None:
    """HTML must include page indicator dots."""
    html = render_comic_html(_MINIMAL_LAYOUT, _RESOLVED)
    # Dots can be implemented as a container with class 'dots', 'page-dots', etc.
    assert (
        "dot" in html.lower()
        or "indicator" in html.lower()
        or "page-nav" in html.lower()
    )


def test_navigation_keyboard_js_present() -> None:
    """HTML must include JavaScript handling left/right arrow keys."""
    html = render_comic_html(_MINIMAL_LAYOUT, _RESOLVED)
    assert "ArrowLeft" in html or "keyCode" in html
    assert "ArrowRight" in html or "keyCode" in html


def test_navigation_touch_swipe_js_present() -> None:
    """HTML must include touch swipe support."""
    html = render_comic_html(_MINIMAL_LAYOUT, _RESOLVED)
    assert "touchstart" in html.lower()
    assert "touchend" in html.lower() or "touchmove" in html.lower()


# ---------------------------------------------------------------------------
# render_comic_html — style CSS integration
# ---------------------------------------------------------------------------


def test_style_css_is_embedded() -> None:
    """Provided style_css must appear inside a <style> block in the output."""
    style = ":root { --primary: #ff0000; --font: 'Comic Sans'; }"
    html = render_comic_html(_MINIMAL_LAYOUT, _RESOLVED, style_css=style)
    assert "--primary" in html
    assert "--font" in html


def test_default_css_variables_present_without_style() -> None:
    """Even without style_css, default CSS custom properties must be set."""
    html = render_comic_html(_MINIMAL_LAYOUT, _RESOLVED)
    assert "--" in html  # At least some CSS variable defined


# ---------------------------------------------------------------------------
# render_comic_html — character intro page (S-3)
# ---------------------------------------------------------------------------

_LAYOUT_WITH_CHARS = {
    "title": "Hero Comic",
    "characters": [
        {
            "name": "Alice",
            "uri": "comic://p/characters/alice",
            "description": "The hero",
        },
        {
            "name": "Bob",
            "uri": "comic://p/characters/bob",
            "description": "The sidekick",
        },
    ],
    "pages": [
        {
            "layout": "1x1",
            "panels": [{"uri": "comic://p/issues/i/panels/p1", "overlays": []}],
        }
    ],
}

_RESOLVED_WITH_CHARS = {
    "comic://p/issues/i/panels/p1": "data:image/png;base64,abc",
    "comic://p/characters/alice": "data:image/png;base64,alice",
    "comic://p/characters/bob": "data:image/png;base64,bob",
}


def test_character_intro_page_rendered_when_characters_present() -> None:
    """An intro page must appear when the layout has a 'characters' array."""
    html = render_comic_html(_LAYOUT_WITH_CHARS, _RESOLVED_WITH_CHARS)
    html_lower = html.lower()
    # Should have character intro section
    assert "alice" in html_lower
    assert "bob" in html_lower
    # Character images must be embedded
    assert "data:image/png;base64,alice" in html
    assert "data:image/png;base64,bob" in html


def test_no_character_intro_page_without_characters() -> None:
    """No character intro should appear when 'characters' key is absent."""
    html = render_comic_html(_MINIMAL_LAYOUT, _RESOLVED)
    # Check that no actual character-intro *section element* is present.
    # (CSS may contain .character-intro-page as a selector, but not a section tag.)
    assert "Meet the Characters" not in html
    # No char-card elements rendered (distinct from CSS rule definitions)
    assert '<div class="char-card">' not in html


# ---------------------------------------------------------------------------
# render_comic_html — panel grid layouts
# ---------------------------------------------------------------------------


def test_grid_layout_2x2() -> None:
    """2x2 layout must produce a CSS grid with 2 columns."""
    layout = {
        "title": "Grid Test",
        "pages": [
            {
                "layout": "2x2",
                "panels": [
                    {"uri": "comic://p/issues/i/panels/p1", "overlays": []},
                    {"uri": "comic://p/issues/i/panels/p2", "overlays": []},
                    {"uri": "comic://p/issues/i/panels/p3", "overlays": []},
                    {"uri": "comic://p/issues/i/panels/p4", "overlays": []},
                ],
            }
        ],
    }
    resolved = {
        "comic://p/issues/i/panels/p1": "data:image/png;base64,a",
        "comic://p/issues/i/panels/p2": "data:image/png;base64,b",
        "comic://p/issues/i/panels/p3": "data:image/png;base64,c",
        "comic://p/issues/i/panels/p4": "data:image/png;base64,d",
    }
    html = render_comic_html(layout, resolved)
    # 2x2 means repeat(2, 1fr) or grid-template-columns with 2 columns
    assert "repeat(2" in html or "1fr 1fr" in html


def test_grid_layout_full_bleed() -> None:
    """full-bleed layout must stretch the single panel to 100%."""
    layout = {
        "title": "Full Bleed",
        "pages": [
            {
                "layout": "full-bleed",
                "panels": [{"uri": "comic://p/issues/i/panels/p1", "overlays": []}],
            }
        ],
    }
    resolved = {"comic://p/issues/i/panels/p1": "data:image/png;base64,a"}
    html = render_comic_html(layout, resolved)
    # full-bleed: single column, 100% width
    assert "full-bleed" in html or "100%" in html


def test_grid_layout_3_row() -> None:
    """3-row layout maps to a single-column grid with 3 rows."""
    layout = {
        "title": "Three Rows",
        "pages": [
            {
                "layout": "3-row",
                "panels": [
                    {"uri": "comic://p/issues/i/panels/p1", "overlays": []},
                    {"uri": "comic://p/issues/i/panels/p2", "overlays": []},
                    {"uri": "comic://p/issues/i/panels/p3", "overlays": []},
                ],
            }
        ],
    }
    resolved = {
        "comic://p/issues/i/panels/p1": "data:image/png;base64,a",
        "comic://p/issues/i/panels/p2": "data:image/png;base64,b",
        "comic://p/issues/i/panels/p3": "data:image/png;base64,c",
    }
    html = render_comic_html(layout, resolved)
    # 3-row: single column (repeat(1,...) or explicit 1 column)
    assert (
        "repeat(1" in html
        or "grid-template-columns:1fr" in html
        or "grid-template-columns: 1fr" in html
    )


# ---------------------------------------------------------------------------
# render_comic_html — HTML is self-contained
# ---------------------------------------------------------------------------


def test_html_is_self_contained() -> None:
    """Output must be a valid standalone HTML document — no external refs."""
    html = render_comic_html(_MINIMAL_LAYOUT, _RESOLVED)
    assert "<!DOCTYPE html>" in html
    assert "<html" in html
    assert "</html>" in html
    # No external stylesheet links
    assert '<link rel="stylesheet"' not in html
    # No external script src attributes (only inline <script>)
    import re

    external_scripts = re.findall(r"<script[^>]+src\s*=", html, re.IGNORECASE)
    assert not external_scripts, f"Found external scripts: {external_scripts}"


def test_panel_images_embedded_as_data_uris() -> None:
    """Panel images must use the resolved data URIs, not original comic:// URIs."""
    html = render_comic_html(_MINIMAL_LAYOUT, _RESOLVED)
    assert "data:image/png;base64,abc" in html
    assert "data:image/png;base64,def" in html
    # Original comic:// URIs must NOT appear in the output
    assert "comic://" not in html
