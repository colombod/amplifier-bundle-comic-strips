"""Tests for amplifier_module_comic_assets.service.ComicProjectService."""

from __future__ import annotations

import base64

import pytest

from amplifier_module_comic_assets.service import ComicProjectService

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

# Minimal keyword args for store_character
_CHAR_META = dict(
    role="protagonist",
    character_type="main",
    bundle="comic-strips",
    visual_traits="tall, blue eyes",
    team_markers="hero badge",
    distinctive_features="scar on left cheek",
)


async def _new_issue(
    service: ComicProjectService, project: str = "test_project", title: str = "Issue 1"
):
    """Create a project + issue, return (project_id, issue_id)."""
    r = await service.create_issue(project, title)
    return r["project_id"], r["issue_id"]


# ===========================================================================
# Project / Issue
# ===========================================================================


@pytest.mark.asyncio(loop_scope="function")
async def test_create_issue_creates_project_and_issue(
    service: ComicProjectService,
) -> None:
    result = await service.create_issue("My Comic", "Origin Story")
    assert result["project_id"] == "my_comic"
    assert result["issue_id"] == "issue-001"
    assert result["created"] is True


@pytest.mark.asyncio(loop_scope="function")
async def test_create_issue_reuses_existing_project(
    service: ComicProjectService,
) -> None:
    r1 = await service.create_issue("My Comic", "Issue One")
    r2 = await service.create_issue("My Comic", "Issue Two")
    assert r1["project_id"] == r2["project_id"]
    assert r2["issue_id"] == "issue-002"
    assert r2["created"] is False


@pytest.mark.asyncio(loop_scope="function")
async def test_list_projects_empty(service: ComicProjectService) -> None:
    projects = await service.list_projects()
    assert projects == []


@pytest.mark.asyncio(loop_scope="function")
async def test_list_projects_after_create(service: ComicProjectService) -> None:
    await service.create_issue("Alpha Comic", "First")
    projects = await service.list_projects()
    assert len(projects) == 1
    assert projects[0]["project_id"] == "alpha_comic"


@pytest.mark.asyncio(loop_scope="function")
async def test_list_issues(service: ComicProjectService) -> None:
    pid, _ = await _new_issue(service, "multi_comic", "First")
    await service.create_issue("multi_comic", "Second")
    issues = await service.list_issues(pid)
    assert len(issues) == 2
    issue_ids = {i["issue_id"] for i in issues}
    assert "issue-001" in issue_ids
    assert "issue-002" in issue_ids


@pytest.mark.asyncio(loop_scope="function")
async def test_get_issue(service: ComicProjectService) -> None:
    pid, iid = await _new_issue(service, "get_issue_proj", "My Story")
    await service.store_asset(pid, iid, "panel", "p01", data=_PNG)
    result = await service.get_issue(pid, iid)
    assert result["title"] == "My Story"
    assert result["asset_count"] == 1


@pytest.mark.asyncio(loop_scope="function")
async def test_cleanup_issue(service: ComicProjectService, tmp_storage) -> None:
    pid, iid = await _new_issue(service, "cleanup_issue_proj", "Temp")
    await service.store_asset(pid, iid, "panel", "p01", data=_PNG)
    await service.cleanup_issue(pid, iid)
    exists = await tmp_storage.exists(f"projects/{pid}/issues/{iid}")
    assert exists is False


@pytest.mark.asyncio(loop_scope="function")
async def test_cleanup_project(service: ComicProjectService, tmp_storage) -> None:
    pid, iid = await _new_issue(service, "cleanup_proj_proj", "Issue A")
    await service.create_issue("cleanup_proj_proj", "Issue B")
    await service.cleanup_project(pid)
    exists = await tmp_storage.exists(f"projects/{pid}")
    assert exists is False


# ===========================================================================
# Characters
# ===========================================================================


@pytest.mark.asyncio(loop_scope="function")
async def test_store_character_from_path(
    service: ComicProjectService, sample_png: str
) -> None:
    pid, iid = await _new_issue(service, "char_path_proj", "I1")
    result = await service.store_character(
        pid, iid, "The Explorer", "manga", source_path=sample_png, **_CHAR_META
    )
    assert result["version"] == 1


@pytest.mark.asyncio(loop_scope="function")
async def test_store_character_from_bytes(service: ComicProjectService) -> None:
    pid, iid = await _new_issue(service, "char_bytes_proj", "I1")
    result = await service.store_character(
        pid, iid, "The Villain", "manga", data=_PNG, **_CHAR_META
    )
    assert result["version"] == 1
    assert result["name"] == "The Villain"


@pytest.mark.asyncio(loop_scope="function")
async def test_store_character_auto_increments_version(
    service: ComicProjectService,
) -> None:
    pid, iid = await _new_issue(service, "char_ver_proj", "I1")
    r1 = await service.store_character(
        pid, iid, "Hero", "manga", data=_PNG, **_CHAR_META
    )
    r2 = await service.store_character(
        pid, iid, "Hero", "manga", data=_PNG, **_CHAR_META
    )
    assert r1["version"] == 1
    assert r2["version"] == 2


@pytest.mark.asyncio(loop_scope="function")
async def test_store_character_different_styles(service: ComicProjectService) -> None:
    pid, iid = await _new_issue(service, "char_styles_proj", "I1")
    r1 = await service.store_character(
        pid, iid, "Hero", "manga", data=_PNG, **_CHAR_META
    )
    r2 = await service.store_character(
        pid, iid, "Hero", "watercolor", data=_PNG, **_CHAR_META
    )
    assert r1["version"] == 1
    assert r2["version"] == 1


@pytest.mark.asyncio(loop_scope="function")
async def test_get_character_metadata_only(service: ComicProjectService) -> None:
    pid, iid = await _new_issue(service, "char_meta_only_proj", "I1")
    await service.store_character(pid, iid, "Scout", "manga", data=_PNG, **_CHAR_META)
    result = await service.get_character(pid, "Scout", include="metadata")
    assert result["name"] == "Scout"
    assert "image" not in result


@pytest.mark.asyncio(loop_scope="function")
async def test_get_character_full_path(
    service: ComicProjectService, sample_png: str
) -> None:
    pid, iid = await _new_issue(service, "char_full_path_proj", "I1")
    await service.store_character(
        pid, iid, "Ranger", "manga", source_path=sample_png, **_CHAR_META
    )
    result = await service.get_character(pid, "Ranger", include="full", format="path")
    assert "image" in result
    assert result["image"].startswith("/")


@pytest.mark.asyncio(loop_scope="function")
async def test_get_character_full_base64(
    service: ComicProjectService, sample_png: str
) -> None:
    pid, iid = await _new_issue(service, "char_full_b64_proj", "I1")
    await service.store_character(
        pid, iid, "Pilot", "manga", source_path=sample_png, **_CHAR_META
    )
    result = await service.get_character(pid, "Pilot", include="full", format="base64")
    assert "image" in result
    # Must be valid base64
    decoded = base64.b64decode(result["image"])
    assert decoded == _PNG


@pytest.mark.asyncio(loop_scope="function")
async def test_get_character_full_data_uri(
    service: ComicProjectService, sample_png: str
) -> None:
    pid, iid = await _new_issue(service, "char_full_uri_proj", "I1")
    await service.store_character(
        pid, iid, "Captain", "manga", source_path=sample_png, **_CHAR_META
    )
    result = await service.get_character(
        pid, "Captain", include="full", format="data_uri"
    )
    assert "image" in result
    assert result["image"].startswith("data:image/png;base64,")


@pytest.mark.asyncio(loop_scope="function")
async def test_get_character_latest_version(service: ComicProjectService) -> None:
    pid, iid = await _new_issue(service, "char_latest_proj", "I1")
    await service.store_character(pid, iid, "Agent", "manga", data=_PNG, **_CHAR_META)
    await service.store_character(pid, iid, "Agent", "manga", data=_PNG, **_CHAR_META)
    # Without style/version: resolves to the latest (v2) by created_at
    result = await service.get_character(pid, "Agent")
    assert result["version"] == 2


@pytest.mark.asyncio(loop_scope="function")
async def test_get_character_specific_version(service: ComicProjectService) -> None:
    pid, iid = await _new_issue(service, "char_ver_exact_proj", "I1")
    await service.store_character(pid, iid, "Knight", "manga", data=_PNG, **_CHAR_META)
    await service.store_character(pid, iid, "Knight", "manga", data=_PNG, **_CHAR_META)
    result = await service.get_character(pid, "Knight", style="manga", version=1)
    assert result["version"] == 1


@pytest.mark.asyncio(loop_scope="function")
async def test_list_characters(service: ComicProjectService) -> None:
    pid, iid = await _new_issue(service, "char_list_proj", "I1")
    await service.store_character(pid, iid, "Alpha", "manga", data=_PNG, **_CHAR_META)
    await service.store_character(pid, iid, "Beta", "manga", data=_PNG, **_CHAR_META)
    chars = await service.list_characters(pid)
    names = {c["name"] for c in chars}
    assert "Alpha" in names
    assert "Beta" in names


@pytest.mark.asyncio(loop_scope="function")
async def test_list_character_versions(service: ComicProjectService) -> None:
    pid, iid = await _new_issue(service, "char_ver_list_proj", "I1")
    await service.store_character(pid, iid, "Hero", "manga", data=_PNG, **_CHAR_META)
    await service.store_character(pid, iid, "Hero", "manga", data=_PNG, **_CHAR_META)
    await service.store_character(
        pid, iid, "Hero", "watercolor", data=_PNG, **_CHAR_META
    )
    versions = await service.list_character_versions(pid, "Hero")
    assert len(versions) == 3
    # Sorted by (style, version): manga_v1, manga_v2, watercolor_v1
    assert versions[0]["style"] == "manga" and versions[0]["version"] == 1
    assert versions[1]["style"] == "manga" and versions[1]["version"] == 2
    assert versions[2]["style"] == "watercolor" and versions[2]["version"] == 1


@pytest.mark.asyncio(loop_scope="function")
async def test_update_character_metadata(service: ComicProjectService) -> None:
    pid, iid = await _new_issue(service, "char_update_proj", "I1")
    await service.store_character(pid, iid, "Medic", "manga", data=_PNG, **_CHAR_META)
    await service.update_character_metadata(
        pid, "Medic", "manga", 1, review_status="accepted"
    )
    char = await service.get_character(pid, "Medic", style="manga", version=1)
    assert char["review_status"] == "accepted"


# ===========================================================================
# Assets
# ===========================================================================


@pytest.mark.asyncio(loop_scope="function")
async def test_store_asset_from_path(
    service: ComicProjectService, sample_png: str
) -> None:
    pid, iid = await _new_issue(service, "asset_path_proj", "I1")
    result = await service.store_asset(
        pid, iid, "panel", "panel_01", source_path=sample_png
    )
    assert result["version"] == 1
    assert result["name"] == "panel_01"


@pytest.mark.asyncio(loop_scope="function")
async def test_store_asset_from_bytes(service: ComicProjectService) -> None:
    pid, iid = await _new_issue(service, "asset_bytes_proj", "I1")
    result = await service.store_asset(pid, iid, "panel", "panel_01", data=_PNG)
    assert result["version"] == 1
    assert result["size_bytes"] == len(_PNG)


@pytest.mark.asyncio(loop_scope="function")
async def test_store_asset_structured_content(service: ComicProjectService) -> None:
    pid, iid = await _new_issue(service, "asset_struct_proj", "I1")
    content = {"theme": "adventure", "scene_count": 5}
    result = await service.store_asset(
        pid, iid, "research", "chapter_1", content=content
    )
    assert result["version"] == 1
    assert result["name"] == "chapter_1"


@pytest.mark.asyncio(loop_scope="function")
async def test_store_asset_invalid_type(service: ComicProjectService) -> None:
    pid, iid = await _new_issue(service, "asset_inv_proj", "I1")
    with pytest.raises(ValueError, match="Invalid asset_type"):
        await service.store_asset(pid, iid, "invalid_type", "test", data=_PNG)


@pytest.mark.asyncio(loop_scope="function")
async def test_store_asset_auto_increments(service: ComicProjectService) -> None:
    pid, iid = await _new_issue(service, "asset_incr_proj", "I1")
    r1 = await service.store_asset(pid, iid, "panel", "panel_01", data=_PNG)
    r2 = await service.store_asset(pid, iid, "panel", "panel_01", data=_PNG)
    assert r1["version"] == 1
    assert r2["version"] == 2


@pytest.mark.asyncio(loop_scope="function")
async def test_get_asset_metadata_only(service: ComicProjectService) -> None:
    pid, iid = await _new_issue(service, "asset_meta_only_proj", "I1")
    await service.store_asset(pid, iid, "panel", "panel_01", data=_PNG)
    result = await service.get_asset(pid, iid, "panel", "panel_01", include="metadata")
    assert result["name"] == "panel_01"
    assert "image" not in result
    # storage_path and content should not be included
    assert "storage_path" not in result


@pytest.mark.asyncio(loop_scope="function")
async def test_get_asset_full(service: ComicProjectService, sample_png: str) -> None:
    pid, iid = await _new_issue(service, "asset_full_proj", "I1")
    await service.store_asset(pid, iid, "panel", "panel_01", source_path=sample_png)
    result = await service.get_asset(
        pid, iid, "panel", "panel_01", include="full", format="path"
    )
    assert "image" in result
    assert result["image"].startswith("/")


@pytest.mark.asyncio(loop_scope="function")
async def test_get_asset_structured_content(service: ComicProjectService) -> None:
    pid, iid = await _new_issue(service, "asset_struct_get_proj", "I1")
    content = {"theme": "mystery", "clues": 3}
    await service.store_asset(pid, iid, "research", "clue_data", content=content)
    result = await service.get_asset(pid, iid, "research", "clue_data", include="full")
    assert isinstance(result.get("content"), dict)
    assert result["content"]["theme"] == "mystery"


@pytest.mark.asyncio(loop_scope="function")
async def test_list_assets(service: ComicProjectService) -> None:
    pid, iid = await _new_issue(service, "asset_list_proj", "I1")
    await service.store_asset(pid, iid, "panel", "panel_01", data=_PNG)
    await service.store_asset(pid, iid, "panel", "panel_02", data=_PNG)
    await service.store_asset(pid, iid, "cover", "cover_main", data=_PNG)
    assets = await service.list_assets(pid, iid)
    assert len(assets) == 3


@pytest.mark.asyncio(loop_scope="function")
async def test_list_assets_filter_by_type(service: ComicProjectService) -> None:
    pid, iid = await _new_issue(service, "asset_filter_proj", "I1")
    await service.store_asset(pid, iid, "panel", "panel_01", data=_PNG)
    await service.store_asset(pid, iid, "panel", "panel_02", data=_PNG)
    await service.store_asset(pid, iid, "cover", "cover_main", data=_PNG)
    panels = await service.list_assets(pid, iid, asset_type="panel")
    assert len(panels) == 2
    assert all(a["asset_type"] == "panel" for a in panels)


@pytest.mark.asyncio(loop_scope="function")
async def test_batch_encode_sorted(service: ComicProjectService) -> None:
    pid, iid = await _new_issue(service, "batch_encode_proj", "I1")
    # Store in reverse order to verify sorting
    await service.store_asset(pid, iid, "panel", "panel_02", data=_PNG)
    await service.store_asset(pid, iid, "panel", "panel_01", data=_PNG)
    results = await service.batch_encode(pid, iid, "panel", format="base64")
    assert len(results) == 2
    assert results[0]["name"] == "panel_01"
    assert results[1]["name"] == "panel_02"


@pytest.mark.asyncio(loop_scope="function")
async def test_update_asset_metadata(service: ComicProjectService) -> None:
    pid, iid = await _new_issue(service, "asset_update_proj", "I1")
    await service.store_asset(pid, iid, "panel", "panel_01", data=_PNG)
    await service.update_asset_metadata(
        pid, iid, "panel", "panel_01", 1, review_status="accepted"
    )
    result = await service.get_asset(pid, iid, "panel", "panel_01")
    assert result["review_status"] == "accepted"


# ===========================================================================
# Styles
# ===========================================================================


@pytest.mark.asyncio(loop_scope="function")
async def test_store_style(service: ComicProjectService) -> None:
    pid, iid = await _new_issue(service, "style_store_proj", "I1")
    result = await service.store_style(pid, iid, "manga", {"palette": "vibrant"})
    assert result["version"] == 1
    assert result["name"] == "manga"


@pytest.mark.asyncio(loop_scope="function")
async def test_store_style_auto_increments(service: ComicProjectService) -> None:
    pid, iid = await _new_issue(service, "style_incr_proj", "I1")
    r1 = await service.store_style(pid, iid, "manga", {"palette": "v1"})
    r2 = await service.store_style(pid, iid, "manga", {"palette": "v2"})
    assert r1["version"] == 1
    assert r2["version"] == 2


@pytest.mark.asyncio(loop_scope="function")
async def test_get_style_metadata(service: ComicProjectService) -> None:
    pid, iid = await _new_issue(service, "style_meta_proj", "I1")
    await service.store_style(pid, iid, "noir", {"tone": "dark"})
    result = await service.get_style(pid, "noir", include="metadata")
    assert result["name"] == "noir"
    assert "definition" not in result


@pytest.mark.asyncio(loop_scope="function")
async def test_get_style_full(service: ComicProjectService) -> None:
    pid, iid = await _new_issue(service, "style_full_proj", "I1")
    definition = {"palette": "monochrome", "line_weight": "bold"}
    await service.store_style(pid, iid, "noir", definition)
    result = await service.get_style(pid, "noir", include="full")
    assert "definition" in result
    assert result["definition"]["palette"] == "monochrome"


@pytest.mark.asyncio(loop_scope="function")
async def test_list_styles(service: ComicProjectService) -> None:
    pid, iid = await _new_issue(service, "style_list_proj", "I1")
    await service.store_style(pid, iid, "manga", {"palette": "vibrant"})
    await service.store_style(pid, iid, "watercolor", {"palette": "soft"})
    styles = await service.list_styles(pid)
    assert len(styles) == 2
    style_names = {s["name"] for s in styles}
    assert "manga" in style_names
    assert "watercolor" in style_names
