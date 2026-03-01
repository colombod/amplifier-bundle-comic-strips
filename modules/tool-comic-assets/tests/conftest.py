"""Shared pytest fixtures for tool-comic-assets tests."""

from __future__ import annotations

import pytest

from amplifier_module_comic_assets.service import ComicProjectService
from amplifier_module_comic_assets.storage import FileSystemStorage

# ---------------------------------------------------------------------------
# Minimal PNG bytes: 8-byte signature + 100 zero bytes.
# Not a valid PNG image but has the right magic bytes for MIME detection.
# ---------------------------------------------------------------------------
_MINIMAL_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


@pytest.fixture()
def tmp_storage(tmp_path):
    """FileSystemStorage rooted at tmp_path / '.comic-assets'."""
    return FileSystemStorage(str(tmp_path / ".comic-assets"))


@pytest.fixture()
def service(tmp_storage):
    """ComicProjectService backed by a fresh temporary storage."""
    return ComicProjectService(tmp_storage)


@pytest.fixture()
def sample_png(tmp_path):
    """Write a minimal PNG file and return its path as a string."""
    png_path = tmp_path / "test.png"
    png_path.write_bytes(_MINIMAL_PNG)
    return str(png_path)
