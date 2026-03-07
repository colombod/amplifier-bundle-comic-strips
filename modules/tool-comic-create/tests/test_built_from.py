"""Tests for built_from provenance metadata on generated assets.

Every generated asset (panel, cover, character ref) must store a ``built_from``
dict in its metadata recording the exact upstream dependencies used during
creation.  ``assemble_comic`` returns ``built_from`` in its result payload.

Design doc: docs/plans/2026-03-07-composable-pipeline-design.md
"""

from __future__ import annotations

import json

import pytest

from amplifier_module_comic_create import ComicCreateTool

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


async def _setup_project_with_character(service, tmp_path):
    """Create project, issue, and one stored character with a reference image."""
    await service.create_issue("test-proj", "Issue 1")
    ref_path = tmp_path / "ref_explorer.png"
    ref_path.write_bytes(_PNG)
    await service.store_character(
        "test-proj",
        "issue-001",
        "Explorer",
        "default",
        role="protagonist",
        character_type="main",
        bundle="foundation",
        visual_traits="tall, blue eyes",
        team_markers="blue badge",
        distinctive_features="scar",
        source_path=str(ref_path),
    )
    return "test-proj", "issue-001"


# ---------------------------------------------------------------------------
# create_panel: built_from
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_create_panel_stores_built_from_with_character_uris(
    service, tmp_path, image_gen
) -> None:
    """Panels must store built_from metadata listing the character URIs used."""
    pid, iid = await _setup_project_with_character(service, tmp_path)
    tool = ComicCreateTool(service=service, image_gen=image_gen)
    char_uri = f"comic://{pid}/characters/explorer"

    result = await tool.execute(
        {
            "action": "create_panel",
            "project": pid,
            "issue": iid,
            "name": "panel_01",
            "prompt": "Explorer faces a wall of errors",
            "character_uris": [char_uri],
        }
    )
    assert result.success is True

    asset = await service.get_asset(pid, iid, "panel", "panel_01")
    meta = asset["metadata"]
    assert "built_from" in meta
    assert meta["built_from"]["character_uris"] == [char_uri]


@pytest.mark.asyncio(loop_scope="function")
async def test_create_panel_built_from_empty_when_no_characters(
    service, image_gen
) -> None:
    """Panels without characters still have built_from with empty character list."""
    await service.create_issue("test-proj", "Issue 1")
    tool = ComicCreateTool(service=service, image_gen=image_gen)

    result = await tool.execute(
        {
            "action": "create_panel",
            "project": "test-proj",
            "issue": "issue-001",
            "name": "panel_01",
            "prompt": "An empty landscape",
        }
    )
    assert result.success is True

    asset = await service.get_asset("test-proj", "issue-001", "panel", "panel_01")
    meta = asset["metadata"]
    assert "built_from" in meta
    assert meta["built_from"]["character_uris"] == []


@pytest.mark.asyncio(loop_scope="function")
async def test_create_panel_merges_caller_built_from(service, image_gen) -> None:
    """Caller-provided built_from fields are preserved alongside auto-populated ones."""
    await service.create_issue("test-proj", "Issue 1")
    tool = ComicCreateTool(service=service, image_gen=image_gen)

    result = await tool.execute(
        {
            "action": "create_panel",
            "project": "test-proj",
            "issue": "issue-001",
            "name": "panel_01",
            "prompt": "An empty landscape",
            "built_from": {
                "storyboard": "comic://test-proj/issues/issue-001/storyboards/storyboard?v=2",
                "style": "comic://test-proj/styles/manga?v=1",
            },
        }
    )
    assert result.success is True

    asset = await service.get_asset("test-proj", "issue-001", "panel", "panel_01")
    built_from = asset["metadata"]["built_from"]
    # Caller-provided fields preserved
    assert built_from["storyboard"] == (
        "comic://test-proj/issues/issue-001/storyboards/storyboard?v=2"
    )
    assert built_from["style"] == "comic://test-proj/styles/manga?v=1"
    # Auto-populated field also present
    assert "character_uris" in built_from


# ---------------------------------------------------------------------------
# create_cover: built_from
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_create_cover_stores_built_from_with_character_uris(
    service, tmp_path, image_gen
) -> None:
    """Covers must store built_from metadata listing the character URIs used."""
    pid, iid = await _setup_project_with_character(service, tmp_path)
    tool = ComicCreateTool(service=service, image_gen=image_gen)
    char_uri = f"comic://{pid}/characters/explorer"

    result = await tool.execute(
        {
            "action": "create_cover",
            "project": pid,
            "issue": iid,
            "prompt": "A dramatic group shot",
            "title": "The Great Debug",
            "character_uris": [char_uri],
        }
    )
    assert result.success is True

    asset = await service.get_asset(pid, iid, "cover", "cover")
    meta = asset["metadata"]
    assert "built_from" in meta
    assert meta["built_from"]["character_uris"] == [char_uri]


@pytest.mark.asyncio(loop_scope="function")
async def test_create_cover_merges_caller_built_from(service, image_gen) -> None:
    """Caller-provided built_from fields (e.g. storyboard) are preserved."""
    await service.create_issue("test-proj", "Issue 1")
    tool = ComicCreateTool(service=service, image_gen=image_gen)

    result = await tool.execute(
        {
            "action": "create_cover",
            "project": "test-proj",
            "issue": "issue-001",
            "prompt": "A dramatic scene",
            "title": "Test Comic",
            "built_from": {
                "storyboard": "comic://test-proj/issues/issue-001/storyboards/storyboard?v=1",
            },
        }
    )
    assert result.success is True

    asset = await service.get_asset("test-proj", "issue-001", "cover", "cover")
    built_from = asset["metadata"]["built_from"]
    assert built_from["storyboard"] == (
        "comic://test-proj/issues/issue-001/storyboards/storyboard?v=1"
    )
    assert "character_uris" in built_from


# ---------------------------------------------------------------------------
# create_character_ref: built_from
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_create_character_ref_stores_built_from_with_style(
    service, image_gen
) -> None:
    """Character refs must store built_from metadata including the style used."""
    await service.create_issue("test-proj", "Issue 1")
    tool = ComicCreateTool(service=service, image_gen=image_gen)

    result = await tool.execute(
        {
            "action": "create_character_ref",
            "project": "test-proj",
            "issue": "issue-001",
            "name": "The Explorer",
            "prompt": "A seasoned scout",
            "visual_traits": "tall, blue eyes",
            "distinctive_features": "scar",
            "style": "manga",
        }
    )
    assert result.success is True

    # slugify("The Explorer") = "the_explorer" (underscores, not hyphens)
    char = await service.get_character("test-proj", "The Explorer", style="manga")
    meta = char["metadata"]
    assert "built_from" in meta
    assert meta["built_from"]["style"] == "manga"


@pytest.mark.asyncio(loop_scope="function")
async def test_create_character_ref_merges_caller_built_from(
    service, image_gen
) -> None:
    """Caller-provided built_from (e.g. base_character_uri for variants) is preserved."""
    await service.create_issue("test-proj", "Issue 1")
    tool = ComicCreateTool(service=service, image_gen=image_gen)

    result = await tool.execute(
        {
            "action": "create_character_ref",
            "project": "test-proj",
            "issue": "issue-001",
            "name": "The Explorer",
            "prompt": "A seasoned scout",
            "visual_traits": "tall, blue eyes",
            "distinctive_features": "scar",
            "style": "manga",
            "built_from": {
                "base_character_uri": "comic://other-proj/characters/the_explorer?v=3",
            },
        }
    )
    assert result.success is True

    char = await service.get_character("test-proj", "The Explorer", style="manga")
    built_from = char["metadata"]["built_from"]
    assert built_from["base_character_uri"] == (
        "comic://other-proj/characters/the_explorer?v=3"
    )
    assert built_from["style"] == "manga"


# ---------------------------------------------------------------------------
# assemble_comic: built_from in return value
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_assemble_comic_returns_built_from(service, tmp_path) -> None:
    """assemble_comic must include built_from in the result payload."""
    await service.create_issue("test-proj", "Issue 1")

    for name in ("panel_01", "panel_02"):
        img = tmp_path / f"{name}.png"
        img.write_bytes(_PNG)
        await service.store_asset(
            "test-proj", "issue-001", "panel", name, source_path=str(img)
        )

    cover_img = tmp_path / "cover.png"
    cover_img.write_bytes(_PNG)
    await service.store_asset(
        "test-proj", "issue-001", "cover", "cover", source_path=str(cover_img)
    )

    tool = ComicCreateTool(service=service)
    output_path = str(tmp_path / "final.html")
    panel_01_uri = "comic://test-proj/issues/issue-001/panels/panel_01"
    panel_02_uri = "comic://test-proj/issues/issue-001/panels/panel_02"
    cover_uri = "comic://test-proj/issues/issue-001/covers/cover"

    result = await tool.execute(
        {
            "action": "assemble_comic",
            "project": "test-proj",
            "issue": "issue-001",
            "output_path": output_path,
            "layout": {
                "title": "Test Comic",
                "cover": {"uri": cover_uri},
                "pages": [
                    {
                        "layout": "2x1",
                        "panels": [
                            {"uri": panel_01_uri, "overlays": []},
                            {"uri": panel_02_uri, "overlays": []},
                        ],
                    },
                ],
            },
        }
    )
    assert result.success is True

    data = json.loads(result.output)
    assert "built_from" in data
    assert cover_uri == data["built_from"]["cover_uri"]
    assert panel_01_uri in data["built_from"]["panel_uris"]
    assert panel_02_uri in data["built_from"]["panel_uris"]


@pytest.mark.asyncio(loop_scope="function")
async def test_assemble_comic_built_from_includes_caller_fields(
    service, tmp_path
) -> None:
    """Caller-provided built_from fields (storyboard, style) appear in result."""
    await service.create_issue("test-proj", "Issue 1")

    img = tmp_path / "panel_01.png"
    img.write_bytes(_PNG)
    await service.store_asset(
        "test-proj", "issue-001", "panel", "panel_01", source_path=str(img)
    )

    cover_img = tmp_path / "cover.png"
    cover_img.write_bytes(_PNG)
    await service.store_asset(
        "test-proj", "issue-001", "cover", "cover", source_path=str(cover_img)
    )

    tool = ComicCreateTool(service=service)
    output_path = str(tmp_path / "final.html")

    result = await tool.execute(
        {
            "action": "assemble_comic",
            "project": "test-proj",
            "issue": "issue-001",
            "output_path": output_path,
            "built_from": {
                "storyboard": "comic://test-proj/issues/issue-001/storyboards/storyboard?v=2",
                "style": "comic://test-proj/styles/manga?v=1",
            },
            "layout": {
                "title": "Test Comic",
                "cover": {
                    "uri": "comic://test-proj/issues/issue-001/covers/cover",
                },
                "pages": [
                    {
                        "layout": "1x1",
                        "panels": [
                            {
                                "uri": "comic://test-proj/issues/issue-001/panels/panel_01",
                                "overlays": [],
                            },
                        ],
                    },
                ],
            },
        }
    )
    assert result.success is True

    data = json.loads(result.output)
    built_from = data["built_from"]
    assert built_from["storyboard"] == (
        "comic://test-proj/issues/issue-001/storyboards/storyboard?v=2"
    )
    assert built_from["style"] == "comic://test-proj/styles/manga?v=1"
