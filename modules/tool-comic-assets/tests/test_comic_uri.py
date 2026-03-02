"""Tests for the comic:// URI protocol."""
from __future__ import annotations

import pytest

from amplifier_module_comic_assets.comic_uri import ComicURI, InvalidComicURI, parse_comic_uri


class TestComicURIParsing:
    """Parse comic:// URIs into ComicURI dataclass."""

    def test_parse_basic_uri(self) -> None:
        uri = parse_comic_uri("comic://my-project/issue-001/panel/panel_01")
        assert uri.project == "my-project"
        assert uri.issue == "issue-001"
        assert uri.asset_type == "panel"
        assert uri.name == "panel_01"
        assert uri.version is None

    def test_parse_uri_with_version(self) -> None:
        uri = parse_comic_uri("comic://my-project/issue-001/character/explorer?v=2")
        assert uri.project == "my-project"
        assert uri.issue == "issue-001"
        assert uri.asset_type == "character"
        assert uri.name == "explorer"
        assert uri.version == 2

    def test_parse_all_asset_types(self) -> None:
        for atype in (
            "panel",
            "cover",
            "avatar",
            "character",
            "storyboard",
            "style",
            "research",
            "final",
            "qa_screenshot",
        ):
            uri = parse_comic_uri(f"comic://p/i/{atype}/n")
            assert uri.asset_type == atype

    def test_parse_rejects_wrong_scheme(self) -> None:
        with pytest.raises(InvalidComicURI, match="scheme"):
            parse_comic_uri("http://proj/issue/panel/name")

    def test_parse_rejects_missing_parts(self) -> None:
        with pytest.raises(InvalidComicURI, match="format"):
            parse_comic_uri("comic://proj/issue/panel")

    def test_parse_rejects_empty_segments(self) -> None:
        with pytest.raises(InvalidComicURI, match="empty"):
            parse_comic_uri("comic://proj//panel/name")

    def test_parse_rejects_invalid_version(self) -> None:
        with pytest.raises(InvalidComicURI, match="version"):
            parse_comic_uri("comic://proj/issue/panel/name?v=abc")


class TestComicURIFormatting:
    """Format ComicURI dataclass back to string."""

    def test_format_basic(self) -> None:
        uri = ComicURI(project="my-proj", issue="issue-001", asset_type="panel", name="panel_01")
        assert str(uri) == "comic://my-proj/issue-001/panel/panel_01"

    def test_format_with_version(self) -> None:
        uri = ComicURI(project="p", issue="i", asset_type="character", name="explorer", version=3)
        assert str(uri) == "comic://p/i/character/explorer?v=3"

    def test_roundtrip(self) -> None:
        original = "comic://my-comic/issue-001/cover/cover?v=2"
        uri = parse_comic_uri(original)
        assert str(uri) == original


class TestComicURILatest:
    """Version resolution: no version means latest."""

    def test_is_latest_when_no_version(self) -> None:
        uri = ComicURI(project="p", issue="i", asset_type="panel", name="n")
        assert uri.is_latest is True

    def test_is_not_latest_when_version_set(self) -> None:
        uri = ComicURI(project="p", issue="i", asset_type="panel", name="n", version=1)
        assert uri.is_latest is False


class TestComicURIBuilders:
    """Convenience class methods for building URIs from components."""

    def test_for_asset(self) -> None:
        uri = ComicURI.for_asset("proj", "issue-001", "panel", "panel_01", version=2)
        assert str(uri) == "comic://proj/issue-001/panel/panel_01?v=2"

    def test_for_asset_latest(self) -> None:
        uri = ComicURI.for_asset("proj", "issue-001", "cover", "cover")
        assert uri.version is None
        assert str(uri) == "comic://proj/issue-001/cover/cover"

    def test_for_character(self) -> None:
        uri = ComicURI.for_character("proj", "issue-001", "explorer")
        assert uri.asset_type == "character"
        assert str(uri) == "comic://proj/issue-001/character/explorer"

    def test_for_style(self) -> None:
        uri = ComicURI.for_style("proj", "issue-001", "manga")
        assert uri.asset_type == "style"
        assert str(uri) == "comic://proj/issue-001/style/manga"


class TestComicURIRepr:
    """S-6: ComicURI has a custom __repr__."""

    def test_repr_wraps_str(self) -> None:
        uri = ComicURI(project="my-proj", issue="issue-001", asset_type="panel", name="panel_01")
        assert repr(uri) == "ComicURI('comic://my-proj/issue-001/panel/panel_01')"

    def test_repr_includes_version(self) -> None:
        uri = ComicURI(project="p", issue="i", asset_type="cover", name="cover", version=3)
        assert repr(uri) == "ComicURI('comic://p/i/cover/cover?v=3')"
