"""Self-contained HTML renderer for comic strips.

Produces a single HTML file with:
- SVG speech/thought/caption bubbles
- Page navigation (keyboard, touch, click)
- Style CSS integration via CSS custom properties
- Optional character intro page
- Panel grid layouts

Public API:
    render_comic_html(layout, resolved_images, style_css) -> str
    render_overlay_svg(overlay) -> str
"""

from __future__ import annotations

import html as _html
import math
import re
from typing import Any

# ---------------------------------------------------------------------------
# CSS grid templates keyed by layout identifier
# ---------------------------------------------------------------------------

_GRID_TEMPLATES: dict[str, str] = {
    # Simple grids
    "1x1": "grid-template-columns:1fr",
    "2x1": "grid-template-columns:repeat(2,1fr)",
    "1x2": "grid-template-columns:1fr",
    "2x2": "grid-template-columns:repeat(2,1fr)",
    "3x1": "grid-template-columns:repeat(3,1fr)",
    "3-row": "grid-template-columns:1fr",
    "2-row": "grid-template-columns:1fr",
    "full-bleed": "grid-template-columns:1fr",
    # Named comic layouts
    "wide-establishing-plus-grid": "grid-template-columns:1fr 1fr;"
    "grid-template-rows:auto auto",
    "crescendo": "grid-template-columns:1fr 1fr;grid-template-rows:auto auto",
    "spotlight": "grid-template-columns:2fr 1fr;grid-template-rows:auto auto",
    "action-sequence": "grid-template-columns:repeat(3,1fr)",
    "dialogue-focus": "grid-template-columns:1fr 1fr",
    "montage": "grid-template-columns:repeat(3,1fr);grid-template-rows:auto auto",
    "cliffhanger": "grid-template-columns:1fr 1fr;grid-template-rows:auto auto",
}

_DEFAULT_GRID = "grid-template-columns:1fr 1fr"

# ---------------------------------------------------------------------------
# Default CSS custom properties (theming)
# ---------------------------------------------------------------------------

_DEFAULT_STYLE_CSS = """\
:root {
  --comic-bg: #1a1a2e;
  --panel-border: #e94560;
  --panel-border-radius: 4px;
  --bubble-fill: #ffffff;
  --bubble-stroke: #000000;
  --bubble-stroke-width: 2;
  --bubble-font: 'Bangers', 'Comic Sans MS', cursive;
  --bubble-font-size: 14px;
  --caption-fill: #fffde0;
  --caption-stroke: #888800;
  --nav-bg: rgba(0,0,0,0.6);
  --nav-color: #ffffff;
  --page-max-width: 900px;
}
"""

# ---------------------------------------------------------------------------
# SVG bubble helpers
# ---------------------------------------------------------------------------


def _tail_triangle(
    bx: float,
    by: float,
    bw: float,
    bh: float,
    tx: float,
    ty: float,
) -> str:
    """Return a tiny SVG <polygon> tail triangle.

    The bubble occupies the rect (bx, by, bw, bh) in the SVG viewBox.
    The tail tip points toward (tx, ty) in the *same* viewBox coordinates.
    Returns the ``points`` attribute value string for a <polygon>.
    """
    cx = bx + bw / 2
    cy = by + bh / 2

    # Vector from bubble centre to tip
    dx = tx - cx
    dy = ty - cy
    dist = math.hypot(dx, dy) or 1.0
    # Normalise
    ndx = dx / dist
    ndy = dy / dist

    # Perpendicular direction
    px = -ndy
    py = ndx

    half_base = min(bw, bh) * 0.10
    # Use actual ellipse radius in the tail direction for edge placement
    rx = bw / 2
    ry = bh / 2
    # Parametric ellipse: distance from center at angle (ndx, ndy)
    if abs(ndx) < 0.001 and abs(ndy) < 0.001:
        edge_dist = min(rx, ry)
    else:
        # Distance to ellipse boundary along (ndx, ndy) direction
        edge_dist = (rx * ry) / math.hypot(rx * ndy, ry * ndx)
    edge_x = cx + ndx * edge_dist * 0.92
    edge_y = cy + ndy * edge_dist * 0.92

    p1x = edge_x + px * half_base
    p1y = edge_y + py * half_base
    p2x = edge_x - px * half_base
    p2y = edge_y - py * half_base

    return f"{p1x:.1f},{p1y:.1f} {tx:.1f},{ty:.1f} {p2x:.1f},{p2y:.1f}"


def _oval_svg(text: str, tail_tx: float, tail_ty: float) -> str:
    """Return inline SVG for an oval speech bubble with tail."""
    # ViewBox 0 0 100 100; ellipse fills top portion, tail points down/sideways
    bx, by, bw, bh = 2, 2, 96, 70
    points = _tail_triangle(bx, by, bw, bh, tail_tx, tail_ty)
    safe = _html.escape(text)
    font_size = "var(--bubble-font-size)"
    if len(text) > 100:
        font_size = "10px"
    elif len(text) > 60:
        font_size = "11px"
    elif len(text) > 40:
        font_size = "12px"
    return (
        f'<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" '
        f'width="100%" height="100%" overflow="visible">'
        f'<ellipse cx="50" cy="{by + bh / 2:.1f}" rx="{bw / 2:.1f}" ry="{bh / 2:.1f}" '
        f'fill="var(--bubble-fill)" stroke="var(--bubble-stroke)" '
        f'stroke-width="var(--bubble-stroke-width)"/>'
        f'<polygon points="{points}" '
        f'fill="var(--bubble-fill)" stroke="var(--bubble-stroke)" '
        f'stroke-width="var(--bubble-stroke-width)"/>'
        f'<foreignObject x="5" y="5" width="90" height="65">'
        f'<div xmlns="http://www.w3.org/1999/xhtml" '
        f'style="font-family:var(--bubble-font);font-size:{font_size};'
        f"text-align:center;display:flex;align-items:center;justify-content:center;"
        f'overflow:hidden;word-break:break-word;height:100%;width:100%;">{safe}</div>'
        f"</foreignObject>"
        f"</svg>"
    )


def _cloud_svg(text: str, tail_tx: float, tail_ty: float) -> str:
    """Return inline SVG for a cloud (thought) bubble."""
    safe = _html.escape(text)
    # Cloud outline: many overlapping circles
    circles = ""
    # Main cloud circles (perimeter)
    perimeter = [
        (30, 20, 20),
        (55, 15, 22),
        (75, 22, 18),
        (85, 38, 16),
        (78, 55, 17),
        (60, 62, 15),
        (40, 62, 15),
        (22, 52, 16),
        (14, 35, 17),
        (22, 20, 16),
    ]
    for cx, cy, r in perimeter:
        circles += (
            f'<circle cx="{cx}" cy="{cy}" r="{r}" '
            f'fill="var(--bubble-fill)" stroke="var(--bubble-stroke)" '
            f'stroke-width="var(--bubble-stroke-width)"/>'
        )
    # Small trail circles toward tail
    tcx, tcy = 50, 50  # bubble centre-ish
    for i, (frac, r) in enumerate([(0.72, 5), (0.85, 3.5), (0.93, 2.5)]):
        cx = tcx + (tail_tx - tcx) * frac
        cy = tcy + (tail_ty - tcy) * frac
        circles += (
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" '
            f'fill="var(--bubble-fill)" stroke="var(--bubble-stroke)" '
            f'stroke-width="var(--bubble-stroke-width)"/>'
        )
    font_size = "var(--bubble-font-size)"
    if len(text) > 100:
        font_size = "10px"
    elif len(text) > 60:
        font_size = "11px"
    elif len(text) > 40:
        font_size = "12px"
    return (
        f'<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" '
        f'width="100%" height="100%" overflow="visible">'
        f'<rect x="18" y="14" width="72" height="52" fill="var(--bubble-fill)" stroke="none"/>'
        f"{circles}"
        f'<foreignObject x="20" y="18" width="62" height="44">'
        f'<div xmlns="http://www.w3.org/1999/xhtml" '
        f'style="font-family:var(--bubble-font);font-size:{font_size};'
        f"text-align:center;display:flex;align-items:center;justify-content:center;"
        f'overflow:hidden;word-break:break-word;height:100%;width:100%;">{safe}</div>'
        f"</foreignObject>"
        f"</svg>"
    )


def _jagged_svg(text: str, tail_tx: float, tail_ty: float) -> str:
    """Return inline SVG for a jagged/explosive speech bubble."""
    safe = _html.escape(text)
    # Build a spiky star polygon (16 points: alternating outer/inner)
    n_spikes = 12
    points_list = []
    for i in range(n_spikes * 2):
        angle = math.pi * i / n_spikes - math.pi / 2
        r = 46 if i % 2 == 0 else 32
        x = 50 + r * math.cos(angle)
        y = 50 + r * math.sin(angle)
        points_list.append(f"{x:.1f},{y:.1f}")
    pts = " ".join(points_list)
    # Tail
    tail_pts = _tail_triangle(10, 10, 80, 80, tail_tx, tail_ty)
    font_size = "var(--bubble-font-size)"
    if len(text) > 100:
        font_size = "10px"
    elif len(text) > 60:
        font_size = "11px"
    elif len(text) > 40:
        font_size = "12px"
    return (
        f'<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" '
        f'width="100%" height="100%" overflow="visible">'
        f'<polygon points="{pts}" '
        f'fill="var(--bubble-fill)" stroke="var(--bubble-stroke)" '
        f'stroke-width="var(--bubble-stroke-width)"/>'
        f'<polygon points="{tail_pts}" '
        f'fill="var(--bubble-fill)" stroke="var(--bubble-stroke)" '
        f'stroke-width="var(--bubble-stroke-width)"/>'
        f'<foreignObject x="15" y="15" width="70" height="70">'
        f'<div xmlns="http://www.w3.org/1999/xhtml" '
        f'style="font-family:var(--bubble-font);font-size:{font_size};'
        f"font-weight:bold;text-align:center;display:flex;align-items:center;"
        f'justify-content:center;overflow:hidden;word-break:break-word;height:100%;width:100%;">{safe}</div>'
        f"</foreignObject>"
        f"</svg>"
    )


def _whisper_svg(text: str, tail_tx: float, tail_ty: float) -> str:
    """Return inline SVG for a whisper bubble (dashed oval, no tail)."""
    safe = _html.escape(text)
    bx, by, bw, bh = 2, 2, 96, 70
    tail_pts = _tail_triangle(bx, by, bw, bh, tail_tx, tail_ty)
    font_size = "var(--bubble-font-size)"
    if len(text) > 100:
        font_size = "10px"
    elif len(text) > 60:
        font_size = "11px"
    elif len(text) > 40:
        font_size = "12px"
    return (
        f'<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" '
        f'width="100%" height="100%" overflow="visible">'
        f'<ellipse cx="50" cy="{by + bh / 2:.1f}" rx="{bw / 2:.1f}" ry="{bh / 2:.1f}" '
        f'fill="var(--bubble-fill)" stroke="var(--bubble-stroke)" '
        f'stroke-width="var(--bubble-stroke-width)" stroke-dasharray="5,3"/>'
        f'<polygon points="{tail_pts}" '
        f'fill="var(--bubble-fill)" stroke="var(--bubble-stroke)" '
        f'stroke-width="var(--bubble-stroke-width)" stroke-dasharray="3,2"/>'
        f'<foreignObject x="5" y="5" width="90" height="65">'
        f'<div xmlns="http://www.w3.org/1999/xhtml" '
        f'style="font-family:var(--bubble-font);font-size:{font_size};'
        f"font-style:italic;text-align:center;display:flex;align-items:center;"
        f'justify-content:center;overflow:hidden;word-break:break-word;height:100%;width:100%;">{safe}</div>'
        f"</foreignObject>"
        f"</svg>"
    )


def _rectangular_svg(text: str) -> str:
    """Return inline SVG for a rectangular caption box (no tail)."""
    safe = _html.escape(text)
    font_size = "var(--bubble-font-size)"
    if len(text) > 100:
        font_size = "10px"
    elif len(text) > 60:
        font_size = "11px"
    elif len(text) > 40:
        font_size = "12px"
    return (
        f'<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" '
        f'width="100%" height="100%" overflow="visible">'
        f'<rect x="2" y="2" width="96" height="96" rx="4" ry="4" '
        f'fill="var(--caption-fill)" stroke="var(--caption-stroke)" '
        f'stroke-width="var(--bubble-stroke-width)"/>'
        f'<foreignObject x="6" y="6" width="88" height="88">'
        f'<div xmlns="http://www.w3.org/1999/xhtml" '
        f'style="font-family:var(--bubble-font);font-size:{font_size};'
        f'text-align:left;padding:4px;overflow:hidden;word-break:break-word;height:100%;width:100%;">{safe}</div>'
        f"</foreignObject>"
        f"</svg>"
    )


# ---------------------------------------------------------------------------
# Public overlay renderer
# ---------------------------------------------------------------------------


def render_overlay_svg(overlay: dict[str, Any]) -> str:
    """Render a speech/thought/caption overlay as positioned HTML with SVG bubble.

    The returned string is a ``<div>`` absolutely positioned inside its
    panel container, using ``position.x/y/width/height`` as CSS percentages.

    Supported shapes: oval, cloud, rectangular, jagged, whisper.
    """
    pos = overlay.get("position", {})
    x = pos.get("x", 10)
    y = pos.get("y", 10)
    w = pos.get("width", 30)
    h = pos.get("height", 20)

    text = overlay.get("text", "")
    shape = overlay.get("shape", "oval").lower()

    # Compute tail target in SVG viewBox (0-100) coordinates
    tail_info = overlay.get("tail") or {}
    tip = tail_info.get("points_to", {})
    # Convert panel-% tip coords into bubble-relative viewBox coords
    tip_panel_x = float(tip.get("x", x + w / 2))
    tip_panel_y = float(tip.get("y", y + h + 20))
    # Direction vector from bubble centre (panel %) to tip (panel %)
    bubble_cx_panel = x + w / 2
    bubble_cy_panel = y + h / 2
    rel_x = tip_panel_x - bubble_cx_panel
    rel_y = tip_panel_y - bubble_cy_panel
    # Scale to viewBox: map panel-% offsets to 0-100 SVG space
    # Use bubble dimensions to account for non-square panels
    scale_x = 100.0 / max(w, 1)
    scale_y = 100.0 / max(h, 1)
    vb_tip_x = 50 + rel_x * scale_x * 0.8
    vb_tip_y = 50 + rel_y * scale_y * 0.8

    style = (
        f"position:absolute;"
        f"left:{x}%;top:{y}%;"
        f"width:{w}%;height:{h}%;"
        f"pointer-events:none;"
        f"overflow:visible;"
    )

    if shape == "rectangular":
        inner = _rectangular_svg(text)
    elif shape == "cloud":
        inner = _cloud_svg(text, vb_tip_x, vb_tip_y)
    elif shape == "jagged":
        inner = _jagged_svg(text, vb_tip_x, vb_tip_y)
    elif shape == "whisper":
        inner = _whisper_svg(text, vb_tip_x, vb_tip_y)
    else:
        # Default: oval
        inner = _oval_svg(text, vb_tip_x, vb_tip_y)

    return f'<div class="bubble-overlay" style="{style}">{inner}</div>'


# ---------------------------------------------------------------------------
# Layout → CSS grid
# ---------------------------------------------------------------------------


def _grid_css(layout_id: str) -> str:
    """Return inline CSS ``grid-template-columns`` declaration for a layout id."""
    return _GRID_TEMPLATES.get(layout_id, _DEFAULT_GRID)


# ---------------------------------------------------------------------------
# Page rendering helpers
# ---------------------------------------------------------------------------


def _render_panel(panel_def: dict[str, Any], resolved: dict[str, str]) -> str:
    uri = panel_def.get("uri", "")
    data_uri = resolved.get(uri, "")
    if not data_uri:
        return ""

    overlays_html = "".join(
        render_overlay_svg(ov) for ov in panel_def.get("overlays", [])
    )
    return (
        f'<div class="panel">'
        f'<img src="{data_uri}" alt="Comic panel" />'
        f"{overlays_html}"
        f"</div>"
    )


def _render_page(
    page_def: dict[str, Any], resolved: dict[str, str], page_idx: int
) -> str:
    layout_id = page_def.get("layout", "1x1")
    grid_css = _grid_css(layout_id)

    panels_html = "".join(
        _render_panel(p, resolved) for p in page_def.get("panels", [])
    )

    layout_class = f"layout-{layout_id.replace('-', '_')}"
    return (
        f'<section class="page story-page" data-page="{page_idx}" '
        f'style="display:none;">'
        f'<div class="panel-grid {layout_class}" '
        f'style="display:grid;{grid_css};gap:8px;width:100%;">'
        f"{panels_html}"
        f"</div>"
        f"</section>"
    )


def _render_cover(
    cover_info: dict[str, Any], resolved: dict[str, str], page_idx: int
) -> str:
    uri = cover_info.get("uri", "")
    data_uri = resolved.get(uri, "")
    if not data_uri:
        return ""

    title = _html.escape(cover_info.get("title", ""))
    subtitle = _html.escape(cover_info.get("subtitle", ""))

    title_block = f'<h1 class="cover-title">{title}</h1>' if title else ""
    subtitle_block = f'<p class="cover-subtitle">{subtitle}</p>' if subtitle else ""

    return (
        f'<section class="page cover-page" data-page="{page_idx}" style="display:none;">'
        f'<div class="cover-image-wrap">'
        f'<img src="{data_uri}" alt="Cover" />'
        f"{title_block}{subtitle_block}"
        f"</div>"
        f"</section>"
    )


def _render_character_intro(
    characters: list[dict[str, Any]],
    resolved: dict[str, str],
    page_idx: int,
) -> str:
    """Render the character introduction page."""
    cards = ""
    for char in characters:
        name = _html.escape(char.get("name", ""))
        description = _html.escape(char.get("description", ""))
        uri = char.get("uri", "")
        data_uri = resolved.get(uri, "")
        img_tag = f'<img src="{data_uri}" alt="{name}" />' if data_uri else ""
        cards += (
            f'<div class="char-card">'
            f"{img_tag}"
            f'<h3 class="char-name">{name}</h3>'
            f'<p class="char-desc">{description}</p>'
            f"</div>"
        )

    return (
        f'<section class="page character-intro-page" data-page="{page_idx}" style="display:none;">'
        f'<h2 class="intro-heading">Meet the Characters</h2>'
        f'<div class="char-grid">{cards}</div>'
        f"</section>"
    )


# ---------------------------------------------------------------------------
# Navigation JS + CSS
# ---------------------------------------------------------------------------

_NAV_CSS = """\
/* --- Comic Navigation --- */
body {
  margin: 0;
  background: var(--comic-bg, #1a1a2e);
  font-family: sans-serif;
  overflow-x: hidden;
}
.comic-container {
  max-width: var(--page-max-width, 900px);
  margin: 0 auto;
  position: relative;
}
.page {
  box-sizing: border-box;
  width: 100%;
  padding: 16px;
}
.cover-image-wrap {
  position: relative;
  text-align: center;
}
.cover-image-wrap img {
  max-width: 100%;
  max-height: 85vh;
  display: inline-block;
  border: 3px solid var(--panel-border, #e94560);
  border-radius: var(--panel-border-radius, 4px);
}
.cover-title {
  position: absolute;
  top: 5%;
  left: 50%;
  transform: translateX(-50%);
  color: #fff;
  text-shadow: 2px 2px 6px rgba(0,0,0,0.8), 0 0 20px rgba(0,0,0,0.4);
  font-family: var(--bubble-font, 'Bangers', cursive);
  font-size: clamp(1.4em, 5vw, 3em);
  max-width: 90%;
  text-align: center;
  line-height: 1.1;
}
.cover-subtitle {
  color: #ddd;
  text-align: center;
  margin-top: 8px;
}
.panel-grid {
  width: 100%;
}
.panel {
  position: relative;
  border: 2px solid var(--panel-border, #e94560);
  border-radius: var(--panel-border-radius, 4px);
  overflow: visible;
  background: #000;
}
.panel img {
  width: 100%;
  display: block;
  max-height: 70vh;
  object-fit: contain;
}
/* Named comic layouts */
.layout-wide_establishing_plus_grid .panel:first-child {
  grid-column: 1 / -1;
}
.layout-crescendo .panel:first-child {
  grid-column: 1 / -1;
}
.layout-crescendo .panel:last-child {
  grid-column: 1 / -1;
}
.layout-spotlight .panel:first-child {
  grid-row: 1 / 3;
}
.layout-action_sequence .panel { min-height: 200px; }
.layout-cliffhanger .panel:last-child {
  grid-column: 1 / -1;
}
.bubble-overlay {
  position: absolute;
}
/* Character intro */
.character-intro-page {
  color: #fff;
}
.intro-heading {
  text-align: center;
  font-family: var(--bubble-font, 'Bangers', cursive);
  font-size: 2em;
  margin-bottom: 16px;
}
.char-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}
.char-card {
  text-align: center;
  background: rgba(255,255,255,0.05);
  border-radius: 8px;
  padding: 12px;
}
.char-card img {
  width: 100%;
  border-radius: 4px;
  max-height: 200px;
  object-fit: cover;
}
.char-name {
  margin: 8px 0 4px;
  font-family: var(--bubble-font, 'Bangers', cursive);
}
.char-desc {
  font-size: 0.85em;
  color: #bbb;
}
/* Navigation bar */
.nav-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 12px 0;
  background: var(--nav-bg, rgba(0,0,0,0.6));
  position: sticky;
  bottom: 0;
  z-index: 100;
}
.nav-btn {
  background: none;
  border: 2px solid var(--nav-color, #fff);
  color: var(--nav-color, #fff);
  padding: 8px 20px;
  cursor: pointer;
  font-size: 1em;
  border-radius: 4px;
  font-family: var(--bubble-font, cursive);
  transition: background 0.2s;
}
.nav-btn:hover { background: rgba(255,255,255,0.15); }
.nav-btn:disabled { opacity: 0.3; cursor: default; }
.page-dots {
  display: flex;
  gap: 8px;
  align-items: center;
}
.page-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgba(255,255,255,0.3);
  cursor: pointer;
  transition: background 0.2s;
  border: none;
  padding: 0;
}
.page-dot.active { background: var(--nav-color, #fff); }
"""

_NAV_JS_TEMPLATE = """\
(function() {
  var pages = document.querySelectorAll('.page');
  var dots = document.querySelectorAll('.page-dot');
  var prevBtn = document.getElementById('nav-prev');
  var nextBtn = document.getElementById('nav-next');
  var current = 0;
  var total = pages.length;

  function show(idx) {
    if (idx < 0 || idx >= total) return;
    pages[current].style.display = 'none';
    dots[current].classList.remove('active');
    current = idx;
    pages[current].style.display = '';
    dots[current].classList.add('active');
    prevBtn.disabled = current === 0;
    nextBtn.disabled = current === total - 1;
  }

  // Initialise
  show(0);

  // Button handlers
  prevBtn.addEventListener('click', function() { show(current - 1); });
  nextBtn.addEventListener('click', function() { show(current + 1); });

  // Dot handlers
  dots.forEach(function(dot, i) {
    dot.addEventListener('click', function() { show(i); });
  });

  // Keyboard: ArrowLeft / ArrowRight
  document.addEventListener('keydown', function(e) {
    if (e.key === 'ArrowLeft')  { show(current - 1); }
    if (e.key === 'ArrowRight') { show(current + 1); }
  });

  // Touch swipe support
  var touchStartX = 0;
  var touchStartY = 0;
  document.addEventListener('touchstart', function(e) {
    touchStartX = e.changedTouches[0].screenX;
    touchStartY = e.changedTouches[0].screenY;
  }, { passive: true });
  document.addEventListener('touchend', function(e) {
    var dx = e.changedTouches[0].screenX - touchStartX;
    var dy = e.changedTouches[0].screenY - touchStartY;
    if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 40) {
      if (dx < 0) { show(current + 1); }
      else         { show(current - 1); }
    }
  }, { passive: true });
})();
"""


def _build_nav_bar(total_pages: int) -> str:
    dots_html = "".join(
        f'<button class="page-dot" aria-label="Page {i + 1}"></button>'
        for i in range(total_pages)
    )
    return (
        f'<nav class="nav-bar" role="navigation" aria-label="Comic pages">'
        f'<button id="nav-prev" class="nav-btn" aria-label="Previous page">&#9664; Prev</button>'
        f'<div class="page-dots" role="tablist">{dots_html}</div>'
        f'<button id="nav-next" class="nav-btn" aria-label="Next page">Next &#9654;</button>'
        f"</nav>"
    )


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------


def render_comic_html(
    layout: dict[str, Any],
    resolved_images: dict[str, str],
    style_css: str = "",
) -> str:
    """Produce a complete self-contained HTML comic page.

    Args:
        layout: The structured layout definition (title, cover, pages, characters).
        resolved_images: Mapping of comic:// URI → data URI string.
        style_css: Optional CSS block (CSS custom properties / theming rules).
                   Appended after the default variables.

    Returns:
        A complete ``<!DOCTYPE html>`` string with all assets embedded.
    """
    title = _html.escape(layout.get("title", "Comic"))
    pages_html_parts: list[str] = []
    page_idx = 0

    # 1. Character intro page (S-3)
    characters = layout.get("characters")
    if characters:
        pages_html_parts.append(
            _render_character_intro(characters, resolved_images, page_idx)
        )
        page_idx += 1

    # 2. Cover page
    cover_info = layout.get("cover")
    if cover_info and cover_info.get("uri"):
        cover_info_with_title = dict(cover_info)
        if "title" not in cover_info_with_title:
            cover_info_with_title["title"] = layout.get("title", "")
        rendered = _render_cover(cover_info_with_title, resolved_images, page_idx)
        if rendered:
            pages_html_parts.append(rendered)
            page_idx += 1

    # 3. Story pages
    for page_def in layout.get("pages", []):
        pages_html_parts.append(_render_page(page_def, resolved_images, page_idx))
        page_idx += 1

    total_pages = page_idx
    pages_html = "\n".join(pages_html_parts)
    nav_bar = _build_nav_bar(total_pages)

    combined_css = _DEFAULT_STYLE_CSS + "\n" + (style_css or "") + "\n" + _NAV_CSS

    return (
        f"<!DOCTYPE html>\n"
        f'<html lang="en">\n'
        f"<head>\n"
        f'  <meta charset="UTF-8" />\n'
        f'  <meta name="viewport" content="width=device-width, initial-scale=1" />\n'
        f'  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bangers&display=swap" />\n'
        f"  <title>{title}</title>\n"
        f"  <style>\n{combined_css}\n  </style>\n"
        f"</head>\n"
        f"<body>\n"
        f'<div class="comic-container">\n'
        f"{pages_html}\n"
        f"{nav_bar}\n"
        f"</div>\n"
        f"<script>\n{_NAV_JS_TEMPLATE}\n</script>\n"
        f"</body>\n"
        f"</html>"
    )


# ---------------------------------------------------------------------------
# HTML validation
# ---------------------------------------------------------------------------


def validate_rendered_html(
    html: str,
    expected_pages: int = 2,
    expected_panels: int = 0,
) -> tuple[list[str], list[str]]:
    """Validate rendered HTML structural integrity.

    Returns:
        (errors, warnings) where errors are hard failures and warnings are soft issues.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # 1. DOCTYPE
    if "<!DOCTYPE html>" not in html and "<!doctype html>" not in html:
        errors.append("Missing <!DOCTYPE html> declaration")

    # 2. Script block exists
    script_match = re.search(r"<script>(.*?)</script>", html, re.DOTALL)
    if not script_match:
        errors.append("No <script> block found in HTML")
    else:
        js = script_match.group(1)
        # 3. JS balanced braces
        open_braces = js.count("{")
        close_braces = js.count("}")
        if open_braces != close_braces:
            errors.append(
                f"JS brace imbalance: {open_braces} opening vs {close_braces} closing"
            )
        # 4. No double-brace escaping artifacts
        if "{{" in js or "}}" in js:
            errors.append(
                "JS contains double-brace '{{' or '}}' — likely Python template escaping leak"
            )

    # 5. No unresolved comic:// URIs
    comic_uri_count = html.count("comic://")
    if comic_uri_count > 0:
        errors.append(f"HTML contains {comic_uri_count} unresolved comic:// URI(s)")

    # 6. Images embedded
    image_count = html.count("data:image/")
    if image_count == 0:
        errors.append("No embedded images (data:image/) found in HTML")

    # 7. Page sections
    page_count = len(re.findall(r'class="page[\s"]', html))
    if page_count < 2:
        errors.append(
            f"Only {page_count} page section(s) found — need at least 2 (cover + story)"
        )
    if expected_pages > 0 and page_count != expected_pages:
        warnings.append(
            f"Page count mismatch: found {page_count}, expected {expected_pages}"
        )

    # 8. Panel count
    panel_count = len(re.findall(r'class="panel[\s"]', html))
    if expected_panels > 0 and panel_count != expected_panels:
        warnings.append(
            f"Panel count mismatch: found {panel_count}, expected {expected_panels}"
        )

    # 9. Navigation elements
    if "nav-prev" not in html or "nav-next" not in html:
        warnings.append("Navigation buttons (nav-prev/nav-next) missing from HTML")

    return errors, warnings
