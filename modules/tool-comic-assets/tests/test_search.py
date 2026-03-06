"""Tests for ComicProjectService.search_characters — cross-project character search."""

from __future__ import annotations

import json

import pytest

from amplifier_module_comic_assets import ComicCharacterTool
from amplifier_module_comic_assets.service import ComicProjectService

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

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
# search_characters
# ===========================================================================


@pytest.mark.asyncio(loop_scope="function")
async def test_search_characters_finds_across_projects(
    service: ComicProjectService,
) -> None:
    """Characters from multiple projects are returned when no project filter."""
    pid1, iid1 = await _new_issue(service, "project_alpha", "I1")
    pid2, iid2 = await _new_issue(service, "project_beta", "I1")

    await service.store_character(
        pid1, iid1, "The Explorer", "manga", data=_PNG, **_CHAR_META
    )
    await service.store_character(
        pid2, iid2, "The Villain", "manga", data=_PNG, **_CHAR_META
    )

    results = await service.search_characters()
    names = {r["name"] for r in results}
    assert "The Explorer" in names
    assert "The Villain" in names
    assert len(results) >= 2


@pytest.mark.asyncio(loop_scope="function")
async def test_search_characters_filters_by_style(
    service: ComicProjectService,
) -> None:
    """Only characters matching the given style slug are returned."""
    pid, iid = await _new_issue(service, "style_filter_proj", "I1")

    await service.store_character(pid, iid, "Hero", "manga", data=_PNG, **_CHAR_META)
    await service.store_character(
        pid, iid, "Sidekick", "watercolor", data=_PNG, **_CHAR_META
    )

    results = await service.search_characters(style="manga")
    names = {r["name"] for r in results}
    assert "Hero" in names
    assert "Sidekick" not in names


@pytest.mark.asyncio(loop_scope="function")
async def test_search_characters_filters_by_metadata(
    service: ComicProjectService,
) -> None:
    """Only characters whose metadata contains all filter key-value pairs are returned."""
    pid, iid = await _new_issue(service, "meta_filter_proj", "I1")

    await service.store_character(
        pid,
        iid,
        "TaggedHero",
        "manga",
        data=_PNG,
        metadata={"tier": "S"},
        **_CHAR_META,
    )
    await service.store_character(
        pid,
        iid,
        "PlainHero",
        "manga",
        data=_PNG,
        **_CHAR_META,
    )

    results = await service.search_characters(metadata_filter={"tier": "S"})
    names = {r["name"] for r in results}
    assert "TaggedHero" in names
    assert "PlainHero" not in names


@pytest.mark.asyncio(loop_scope="function")
async def test_search_characters_empty_results(
    service: ComicProjectService,
) -> None:
    """Searching with a non-matching style returns an empty list."""
    pid, iid = await _new_issue(service, "empty_search_proj", "I1")
    await service.store_character(
        pid,
        iid,
        "Solo",
        "manga",
        data=_PNG,
        **_CHAR_META,
    )

    results = await service.search_characters(style="nonexistent_style")
    assert results == []


@pytest.mark.asyncio(loop_scope="function")
async def test_search_characters_single_project_filter(
    service: ComicProjectService,
) -> None:
    """When project_id is given, only characters from that project appear."""
    pid1, iid1 = await _new_issue(service, "proj_one", "I1")
    pid2, iid2 = await _new_issue(service, "proj_two", "I1")

    await service.store_character(
        pid1,
        iid1,
        "Alpha",
        "manga",
        data=_PNG,
        **_CHAR_META,
    )
    await service.store_character(
        pid2,
        iid2,
        "Beta",
        "manga",
        data=_PNG,
        **_CHAR_META,
    )

    results = await service.search_characters(project_id=pid1)
    names = {r["name"] for r in results}
    assert "Alpha" in names
    assert "Beta" not in names


@pytest.mark.asyncio(loop_scope="function")
async def test_search_characters_returns_uri_and_traits(
    service: ComicProjectService,
) -> None:
    """Each result dict contains uri, visual_traits, and distinctive_features."""
    pid, iid = await _new_issue(service, "uri_traits_proj", "I1")
    await service.store_character(
        pid,
        iid,
        "Ranger",
        "manga",
        data=_PNG,
        **_CHAR_META,
    )

    results = await service.search_characters()
    assert len(results) == 1
    r = results[0]
    assert "uri" in r
    assert r["uri"].startswith("comic://")
    assert r["visual_traits"] == "tall, blue eyes"
    assert r["distinctive_features"] == "scar on left cheek"
    assert r["char_slug"] == "ranger"
    assert r["style"] == "manga"
    assert r["originating_project"] == pid
    assert "version" in r
    assert "metadata" in r
    assert r["name"] == "Ranger"


# ===========================================================================
# ComicCharacterTool — search action integration
# ===========================================================================


@pytest.mark.asyncio(loop_scope="function")
async def test_character_tool_search_action(
    service: ComicProjectService,
) -> None:
    """ComicCharacterTool dispatches 'search' and passes style to the service."""
    pid, iid = await _new_issue(service, "tool_search_proj", "I1")

    await service.store_character(pid, iid, "Ninja", "manga", data=_PNG, **_CHAR_META)
    await service.store_character(
        pid, iid, "Painter", "watercolor", data=_PNG, **_CHAR_META
    )

    tool = ComicCharacterTool(service)
    result = await tool.execute({"action": "search", "style": "manga"})
    assert result.success is True
    data = json.loads(result.output)
    names = {r["name"] for r in data}
    assert "Ninja" in names
    assert "Painter" not in names


@pytest.mark.asyncio(loop_scope="function")
async def test_character_tool_search_with_metadata_filter(
    service: ComicProjectService,
) -> None:
    """ComicCharacterTool dispatches 'search' and passes metadata_filter to the service."""
    pid, iid = await _new_issue(service, "tool_meta_search_proj", "I1")

    await service.store_character(
        pid,
        iid,
        "EliteAgent",
        "manga",
        data=_PNG,
        metadata={"rank": "elite"},
        **_CHAR_META,
    )
    await service.store_character(
        pid,
        iid,
        "Rookie",
        "manga",
        data=_PNG,
        **_CHAR_META,
    )

    tool = ComicCharacterTool(service)
    result = await tool.execute(
        {"action": "search", "metadata_filter": {"rank": "elite"}}
    )
    assert result.success is True
    data = json.loads(result.output)
    names = {r["name"] for r in data}
    assert "EliteAgent" in names
    assert "Rookie" not in names
