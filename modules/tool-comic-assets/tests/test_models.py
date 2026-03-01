"""Tests for amplifier_module_comic_assets.models module."""

from __future__ import annotations

from amplifier_module_comic_assets.models import (
    ASSET_TYPES,
    Asset,
    CharacterDesign,
    Project,
    StyleGuide,
    slugify,
)


# ---------------------------------------------------------------------------
# slugify
# ---------------------------------------------------------------------------


def test_slugify_basic() -> None:
    assert slugify("The Explorer") == "the_explorer"


def test_slugify_special_chars() -> None:
    assert slugify("Hello World!!!") == "hello_world"


def test_slugify_empty() -> None:
    assert slugify("") == "unnamed"


def test_slugify_all_special() -> None:
    assert slugify("!!!") == "unnamed"


def test_slugify_hyphens() -> None:
    # Hyphens are preserved by the regex [^a-z0-9_-]+
    assert slugify("my-character") == "my-character"


# ---------------------------------------------------------------------------
# ASSET_TYPES
# ---------------------------------------------------------------------------


def test_asset_types_frozen() -> None:
    assert isinstance(ASSET_TYPES, frozenset)
    expected_members = {
        "research",
        "storyboard",
        "panel",
        "cover",
        "avatar",
        "qa_screenshot",
        "final",
    }
    assert ASSET_TYPES == expected_members


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------


def test_project_roundtrip() -> None:
    proj = Project(
        id="ampliverse",
        name="AmpliVerse",
        created_at="2024-01-01T00:00:00+00:00",
        description="Test project",
    )
    d = proj.to_dict()
    restored = Project.from_dict(d)
    assert restored.id == proj.id
    assert restored.name == proj.name
    assert restored.created_at == proj.created_at
    assert restored.description == proj.description


# ---------------------------------------------------------------------------
# CharacterDesign
# ---------------------------------------------------------------------------


def _make_char(**kwargs) -> CharacterDesign:
    defaults = dict(
        name="The Explorer",
        project_id="ampliverse",
        style="manga",
        version=1,
        created_at="2024-01-01T00:00:00+00:00",
        origin_issue_id="issue-001",
        role="protagonist",
        character_type="main",
        bundle="comic-strips",
        visual_traits="tall, blue eyes",
        team_markers="hero badge",
        distinctive_features="scar on cheek",
    )
    defaults.update(kwargs)
    return CharacterDesign(**defaults)


def test_character_design_roundtrip() -> None:
    char = _make_char()
    d = char.to_dict(include_image=True)
    restored = CharacterDesign.from_dict(d)
    assert restored.name == char.name
    assert restored.style == char.style
    assert restored.version == char.version
    assert restored.role == char.role


def test_character_design_to_dict_excludes_image_by_default() -> None:
    char = _make_char(
        image_path="projects/p/characters/explorer/manga_v1/reference.png"
    )
    d = char.to_dict()
    assert "image_path" not in d


def test_character_design_to_dict_includes_image_when_requested() -> None:
    image_path = "projects/p/characters/explorer/manga_v1/reference.png"
    char = _make_char(image_path=image_path)
    d = char.to_dict(include_image=True)
    assert "image_path" in d
    assert d["image_path"] == image_path


# ---------------------------------------------------------------------------
# StyleGuide
# ---------------------------------------------------------------------------


def test_style_guide_roundtrip() -> None:
    style = StyleGuide(
        name="manga",
        project_id="ampliverse",
        version=1,
        created_at="2024-01-01T00:00:00+00:00",
        origin_issue_id="issue-001",
        definition={"palette": "vibrant"},
    )
    d = style.to_dict(include_definition=True)
    restored = StyleGuide.from_dict(d)
    assert restored.name == style.name
    assert restored.version == style.version
    assert restored.definition == style.definition


def test_style_guide_to_dict_excludes_definition_by_default() -> None:
    style = StyleGuide(
        name="manga",
        project_id="ampliverse",
        version=1,
        created_at="2024-01-01T00:00:00+00:00",
        origin_issue_id="issue-001",
        definition={"palette": "vibrant"},
    )
    d = style.to_dict()
    assert "definition" not in d


# ---------------------------------------------------------------------------
# Asset
# ---------------------------------------------------------------------------


def test_asset_roundtrip() -> None:
    asset = Asset(
        name="panel_01",
        asset_type="panel",
        project_id="ampliverse",
        issue_id="issue-001",
        version=1,
        created_at="2024-01-01T00:00:00+00:00",
        mime_type="image/png",
        size_bytes=108,
        storage_path="projects/ampliverse/issues/issue-001/panels/panel_01_v1/image.png",
    )
    d = asset.to_dict(include_payload=True)
    restored = Asset.from_dict(d)
    assert restored.name == asset.name
    assert restored.asset_type == asset.asset_type
    assert restored.version == asset.version
    assert restored.mime_type == asset.mime_type
    assert restored.size_bytes == asset.size_bytes
    assert restored.storage_path == asset.storage_path
