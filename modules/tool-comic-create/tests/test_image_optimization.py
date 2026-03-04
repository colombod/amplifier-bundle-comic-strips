"""Tests for HTML image optimization (assembly-path resizing)."""

from __future__ import annotations

import base64
import io

import pytest

from amplifier_module_comic_create import (
    _detect_mime,
    _optimize_for_html,
    _optimize_resolved_images,
)

# ---------------------------------------------------------------------------
# Helpers — create minimal valid images without needing real photos
# ---------------------------------------------------------------------------

def _make_png(width: int = 200, height: int = 150, *, color: str = "red") -> bytes:
    """Create a minimal PNG using Pillow."""
    from PIL import Image

    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_rgba_png(width: int = 200, height: int = 150) -> bytes:
    """Create a PNG with alpha channel."""
    from PIL import Image

    img = Image.new("RGBA", (width, height), (255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _to_data_uri(image_bytes: bytes, mime: str = "image/png") -> str:
    encoded = base64.b64encode(image_bytes).decode()
    return f"data:{mime};base64,{encoded}"


# ---------------------------------------------------------------------------
# _optimize_for_html tests
# ---------------------------------------------------------------------------


class TestOptimizeForHtml:
    """Unit tests for the per-image HTML optimization function."""

    def test_returns_jpeg(self) -> None:
        raw = _make_png(1600, 1200)
        opt_bytes, mime = _optimize_for_html(raw, max_width=800, max_height=600)
        assert mime == "image/jpeg"
        # JPEG magic bytes
        assert opt_bytes[:3] == b"\xff\xd8\xff"

    def test_respects_max_dimensions(self) -> None:
        from PIL import Image

        raw = _make_png(2000, 1500)
        opt_bytes, _ = _optimize_for_html(raw, max_width=800, max_height=600)
        img = Image.open(io.BytesIO(opt_bytes))
        assert img.width <= 800
        assert img.height <= 600

    def test_preserves_aspect_ratio(self) -> None:
        from PIL import Image

        raw = _make_png(2000, 1000)  # 2:1 ratio
        opt_bytes, _ = _optimize_for_html(raw, max_width=800, max_height=600)
        img = Image.open(io.BytesIO(opt_bytes))
        ratio = img.width / img.height
        assert abs(ratio - 2.0) < 0.05  # within 5% of original

    def test_small_image_still_converted_to_jpeg(self) -> None:
        raw = _make_png(100, 100)
        opt_bytes, mime = _optimize_for_html(raw, max_width=1200, max_height=900)
        # Even small images get JPEG-converted for consistency
        assert mime == "image/jpeg"

    def test_rgba_converted_to_rgb(self) -> None:
        raw = _make_rgba_png(400, 300)
        opt_bytes, mime = _optimize_for_html(raw)
        # JPEG doesn't support alpha — should not raise
        assert mime == "image/jpeg"
        assert len(opt_bytes) > 0

    def test_reduces_file_size(self) -> None:
        # Large PNG will compress significantly
        raw = _make_png(1536, 1024)
        opt_bytes, _ = _optimize_for_html(raw, max_width=1200, max_height=900)
        assert len(opt_bytes) < len(raw)


# ---------------------------------------------------------------------------
# _optimize_resolved_images tests
# ---------------------------------------------------------------------------


class TestOptimizeResolvedImages:
    """Tests for the layout-aware batch optimization function."""

    def test_panel_images_optimized(self) -> None:
        panel_png = _make_png(1536, 1024)
        layout = {
            "pages": [
                {"panels": [{"uri": "comic://proj/issues/i1/panels/p1"}]}
            ],
        }
        resolved = {
            "comic://proj/issues/i1/panels/p1": _to_data_uri(panel_png),
        }
        result = _optimize_resolved_images(layout, resolved)
        # Output should be a data URI with JPEG
        assert "data:image/jpeg;base64," in result["comic://proj/issues/i1/panels/p1"]

    def test_cover_gets_larger_dimensions(self) -> None:
        """Cover images should use larger max dimensions than panels."""
        from PIL import Image

        cover_png = _make_png(2000, 1500)
        layout = {
            "cover": {"uri": "comic://proj/issues/i1/covers/cover"},
            "pages": [],
        }
        resolved = {
            "comic://proj/issues/i1/covers/cover": _to_data_uri(cover_png),
        }
        result = _optimize_resolved_images(layout, resolved)
        data_uri = result["comic://proj/issues/i1/covers/cover"]
        encoded = data_uri.split(",", 1)[1]
        img = Image.open(io.BytesIO(base64.b64decode(encoded)))
        # Cover max is 1600x1200, panel max is 1200x900
        # A 2000x1500 image scaled to fit 1600x1200 should be 1600x1200
        assert img.width <= 1600
        assert img.height <= 1200

    def test_character_gets_smaller_dimensions(self) -> None:
        from PIL import Image

        char_png = _make_png(1024, 1536)  # portrait
        layout = {
            "characters": [{"uri": "comic://proj/characters/hero", "name": "Hero"}],
            "pages": [],
        }
        resolved = {
            "comic://proj/characters/hero": _to_data_uri(char_png),
        }
        result = _optimize_resolved_images(layout, resolved)
        data_uri = result["comic://proj/characters/hero"]
        encoded = data_uri.split(",", 1)[1]
        img = Image.open(io.BytesIO(base64.b64decode(encoded)))
        # Character max is 600x800
        assert img.width <= 600
        assert img.height <= 800

    def test_preserves_all_uris(self) -> None:
        """All input URIs should appear in output."""
        panel_png = _make_png(200, 150)
        uris = {
            f"comic://proj/issues/i1/panels/p{i}": _to_data_uri(panel_png)
            for i in range(5)
        }
        layout = {
            "pages": [
                {"panels": [{"uri": uri} for uri in uris]}
            ]
        }
        result = _optimize_resolved_images(layout, uris)
        assert set(result.keys()) == set(uris.keys())

    def test_empty_layout_returns_empty(self) -> None:
        result = _optimize_resolved_images({"pages": []}, {})
        assert result == {}

    def test_invalid_data_uri_preserved(self) -> None:
        """Malformed data URIs are passed through unchanged."""
        layout = {
            "pages": [
                {"panels": [{"uri": "comic://proj/issues/i1/panels/bad"}]}
            ]
        }
        resolved = {"comic://proj/issues/i1/panels/bad": "not-a-data-uri"}
        result = _optimize_resolved_images(layout, resolved)
        assert result["comic://proj/issues/i1/panels/bad"] == "not-a-data-uri"
