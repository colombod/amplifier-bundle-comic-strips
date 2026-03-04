"""Tests for the comic:// URI protocol (v2: scope-aware)."""

from __future__ import annotations

import pytest

from amplifier_module_comic_assets.comic_uri import (
    COMIC_URI_TYPES,
    ISSUE_SCOPED_TYPES,
    PROJECT_SCOPED_TYPES,
    ComicURI,
    InvalidComicURI,
    parse_comic_uri,
    pluralize_type,
    singularize_type,
)


class TestComicURIParsing:
    """Parse comic:// URIs into ComicURI dataclass."""

    # --- Project-scoped (3 segments after scheme) ---

    def test_parse_project_scoped_character(self) -> None:
        uri = parse_comic_uri("comic://my-project/characters/explorer")
        assert uri.project == "my-project"
        assert uri.asset_type == "characters"
        assert uri.name == "explorer"
        assert uri.issue is None
        assert uri.version is None

    def test_parse_project_scoped_style(self) -> None:
        uri = parse_comic_uri("comic://my-project/styles/manga")
        assert uri.project == "my-project"
        assert uri.asset_type == "styles"
        assert uri.name == "manga"
        assert uri.issue is None

    def test_parse_project_scoped_with_version(self) -> None:
        uri = parse_comic_uri("comic://my-project/characters/explorer?v=2")
        assert uri.project == "my-project"
        assert uri.asset_type == "characters"
        assert uri.name == "explorer"
        assert uri.issue is None
        assert uri.version == 2

    # --- Issue-scoped (5 segments after scheme) ---

    def test_parse_issue_scoped_panel(self) -> None:
        uri = parse_comic_uri("comic://my-project/issues/issue-001/panels/panel_01")
        assert uri.project == "my-project"
        assert uri.issue == "issue-001"
        assert uri.asset_type == "panels"
        assert uri.name == "panel_01"
        assert uri.version is None

    def test_parse_issue_scoped_cover(self) -> None:
        uri = parse_comic_uri("comic://my-project/issues/the-revenge/covers/cover")
        assert uri.project == "my-project"
        assert uri.issue == "the-revenge"
        assert uri.asset_type == "covers"
        assert uri.name == "cover"

    def test_parse_issue_scoped_with_version(self) -> None:
        uri = parse_comic_uri("comic://my-project/issues/issue-001/panels/panel_01?v=3")
        assert uri.project == "my-project"
        assert uri.issue == "issue-001"
        assert uri.asset_type == "panels"
        assert uri.name == "panel_01"
        assert uri.version == 3

    def test_parse_all_project_scoped_types(self) -> None:
        for atype in PROJECT_SCOPED_TYPES:
            uri = parse_comic_uri(f"comic://p/{atype}/n")
            assert uri.asset_type == atype
            assert uri.issue is None

    def test_parse_all_issue_scoped_types(self) -> None:
        for atype in ISSUE_SCOPED_TYPES:
            uri = parse_comic_uri(f"comic://p/issues/i/{atype}/n")
            assert uri.asset_type == atype
            assert uri.issue == "i"

    # --- Error cases ---

    def test_parse_rejects_wrong_scheme(self) -> None:
        with pytest.raises(InvalidComicURI, match="scheme"):
            parse_comic_uri("http://proj/characters/name")

    def test_parse_rejects_unknown_project_scoped_type(self) -> None:
        with pytest.raises(InvalidComicURI, match="Cannot parse"):
            parse_comic_uri("comic://proj/bogus/name")

    def test_parse_rejects_unknown_issue_scoped_type(self) -> None:
        with pytest.raises(InvalidComicURI, match="Unknown issue-scoped type"):
            parse_comic_uri("comic://proj/issues/i/bogus/name")

    def test_parse_rejects_empty_project(self) -> None:
        with pytest.raises(InvalidComicURI, match="project"):
            parse_comic_uri("comic:///characters/name")

    def test_parse_rejects_empty_name_project_scoped(self) -> None:
        with pytest.raises(InvalidComicURI, match="empty"):
            parse_comic_uri("comic://proj/characters/")

    def test_parse_rejects_empty_issue_segment(self) -> None:
        with pytest.raises(InvalidComicURI, match="empty"):
            parse_comic_uri("comic://proj/issues//panels/name")

    def test_parse_rejects_invalid_version(self) -> None:
        with pytest.raises(InvalidComicURI, match="version"):
            parse_comic_uri("comic://proj/characters/name?v=abc")

    def test_parse_rejects_too_few_segments(self) -> None:
        with pytest.raises(InvalidComicURI, match="Cannot parse"):
            parse_comic_uri("comic://proj/only")

    def test_parse_rejects_issues_with_too_few_segments(self) -> None:
        with pytest.raises(InvalidComicURI, match="Cannot parse"):
            parse_comic_uri("comic://proj/issues/i/panels")


class TestComicURIFormatting:
    """Format ComicURI dataclass back to string."""

    def test_format_project_scoped(self) -> None:
        uri = ComicURI(project="my-proj", asset_type="characters", name="explorer")
        assert str(uri) == "comic://my-proj/characters/explorer"

    def test_format_project_scoped_with_version(self) -> None:
        uri = ComicURI(project="p", asset_type="characters", name="explorer", version=3)
        assert str(uri) == "comic://p/characters/explorer?v=3"

    def test_format_issue_scoped(self) -> None:
        uri = ComicURI(
            project="my-proj", issue="issue-001", asset_type="panels", name="panel_01"
        )
        assert str(uri) == "comic://my-proj/issues/issue-001/panels/panel_01"

    def test_format_issue_scoped_with_version(self) -> None:
        uri = ComicURI(
            project="p", issue="i", asset_type="covers", name="cover", version=2
        )
        assert str(uri) == "comic://p/issues/i/covers/cover?v=2"

    def test_roundtrip_project_scoped(self) -> None:
        original = "comic://my-comic/characters/explorer?v=2"
        assert str(parse_comic_uri(original)) == original

    def test_roundtrip_issue_scoped(self) -> None:
        original = "comic://my-comic/issues/issue-001/panels/panel_01?v=3"
        assert str(parse_comic_uri(original)) == original


class TestComicURIProperties:
    """Scope and version properties."""

    def test_is_project_scoped(self) -> None:
        uri = ComicURI(project="p", asset_type="characters", name="n")
        assert uri.is_project_scoped is True
        assert uri.is_issue_scoped is False

    def test_is_issue_scoped(self) -> None:
        uri = ComicURI(project="p", issue="i", asset_type="panels", name="n")
        assert uri.is_project_scoped is False
        assert uri.is_issue_scoped is True

    def test_is_latest_when_no_version(self) -> None:
        uri = ComicURI(project="p", asset_type="characters", name="n")
        assert uri.is_latest is True

    def test_is_not_latest_when_version_set(self) -> None:
        uri = ComicURI(project="p", asset_type="characters", name="n", version=1)
        assert uri.is_latest is False


class TestComicURIBuilders:
    """Convenience class methods for building URIs from components."""

    def test_for_asset(self) -> None:
        uri = ComicURI.for_asset("proj", "issue-001", "panels", "panel_01", version=2)
        assert str(uri) == "comic://proj/issues/issue-001/panels/panel_01?v=2"
        assert uri.issue == "issue-001"

    def test_for_asset_latest(self) -> None:
        uri = ComicURI.for_asset("proj", "issue-001", "covers", "cover")
        assert uri.version is None
        assert str(uri) == "comic://proj/issues/issue-001/covers/cover"

    def test_for_asset_pluralizes_singular_type(self) -> None:
        """for_asset accepts singular types and pluralizes them."""
        uri = ComicURI.for_asset("proj", "issue-001", "panel", "panel_01")
        assert uri.asset_type == "panels"
        assert str(uri) == "comic://proj/issues/issue-001/panels/panel_01"

    def test_for_character(self) -> None:
        uri = ComicURI.for_character("proj", "explorer")
        assert uri.asset_type == "characters"
        assert uri.issue is None
        assert str(uri) == "comic://proj/characters/explorer"

    def test_for_character_with_version(self) -> None:
        uri = ComicURI.for_character("proj", "explorer", version=2)
        assert str(uri) == "comic://proj/characters/explorer?v=2"

    def test_for_style(self) -> None:
        uri = ComicURI.for_style("proj", "manga")
        assert uri.asset_type == "styles"
        assert uri.issue is None
        assert str(uri) == "comic://proj/styles/manga"

    def test_for_style_with_version(self) -> None:
        uri = ComicURI.for_style("proj", "manga", version=1)
        assert str(uri) == "comic://proj/styles/manga?v=1"


class TestComicURIRepr:
    """ComicURI has a custom __repr__."""

    def test_repr_project_scoped(self) -> None:
        uri = ComicURI(project="my-proj", asset_type="characters", name="explorer")
        assert repr(uri) == "ComicURI('comic://my-proj/characters/explorer')"

    def test_repr_issue_scoped_with_version(self) -> None:
        uri = ComicURI(
            project="p", issue="i", asset_type="covers", name="cover", version=3
        )
        assert repr(uri) == "ComicURI('comic://p/issues/i/covers/cover?v=3')"


class TestComicURIConstants:
    """COMIC_URI_TYPES = PROJECT_SCOPED_TYPES | ISSUE_SCOPED_TYPES."""

    def test_comic_uri_types_is_union(self) -> None:
        assert COMIC_URI_TYPES == PROJECT_SCOPED_TYPES | ISSUE_SCOPED_TYPES

    def test_project_scoped_types_content(self) -> None:
        assert "characters" in PROJECT_SCOPED_TYPES
        assert "styles" in PROJECT_SCOPED_TYPES

    def test_issue_scoped_types_content(self) -> None:
        for t in (
            "panels",
            "covers",
            "storyboards",
            "research",
            "finals",
            "avatars",
            "qa_screenshots",
        ):
            assert t in ISSUE_SCOPED_TYPES

    def test_no_overlap(self) -> None:
        assert PROJECT_SCOPED_TYPES.isdisjoint(ISSUE_SCOPED_TYPES)


class TestPluralizeAndSingularize:
    """pluralize_type / singularize_type helper functions."""

    def test_pluralize_known_singulars(self) -> None:
        assert pluralize_type("character") == "characters"
        assert pluralize_type("style") == "styles"
        assert pluralize_type("panel") == "panels"
        assert pluralize_type("cover") == "covers"
        assert pluralize_type("storyboard") == "storyboards"
        assert pluralize_type("research") == "research"
        assert pluralize_type("final") == "finals"
        assert pluralize_type("avatar") == "avatars"
        assert pluralize_type("qa_screenshot") == "qa_screenshots"

    def test_pluralize_unknown_passthrough(self) -> None:
        assert pluralize_type("already_plural") == "already_plural"
        assert pluralize_type("panels") == "panels"

    def test_singularize_known_plurals(self) -> None:
        assert singularize_type("characters") == "character"
        assert singularize_type("styles") == "style"
        assert singularize_type("panels") == "panel"
        assert singularize_type("covers") == "cover"
        assert singularize_type("storyboards") == "storyboard"
        assert singularize_type("research") == "research"
        assert singularize_type("finals") == "final"
        assert singularize_type("avatars") == "avatar"
        assert singularize_type("qa_screenshots") == "qa_screenshot"

    def test_singularize_unknown_passthrough(self) -> None:
        assert singularize_type("panel") == "panel"
        assert singularize_type("bogus") == "bogus"

    def test_roundtrip(self) -> None:
        """pluralize(singularize(x)) == x for all known plural types."""
        for plural in (
            "characters",
            "styles",
            "panels",
            "covers",
            "storyboards",
            "research",
            "finals",
            "avatars",
            "qa_screenshots",
        ):
            assert pluralize_type(singularize_type(plural)) == plural
