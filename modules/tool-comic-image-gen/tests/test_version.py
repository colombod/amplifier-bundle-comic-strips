"""Tests for module version."""

from __future__ import annotations


def test_version_is_0_2_0() -> None:
    """Version must be 0.2.0 to reflect v4 changes."""
    from amplifier_comic_image_gen._version import __version__

    assert __version__ == "0.2.0"
