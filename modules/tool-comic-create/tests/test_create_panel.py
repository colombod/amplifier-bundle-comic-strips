"""Tests for comic_create(action='create_panel')."""

from __future__ import annotations

import json

import pytest

from amplifier_module_comic_create import ComicCreateTool


_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


async def _setup_project_with_character(service, tmp_path):
    """Create project, issue, and one stored character with a reference image."""
    await service.create_issue("test-proj", "Issue 1")

    # Write a fake reference image to disk, then store the character
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


@pytest.mark.asyncio(loop_scope="function")
async def test_create_panel_returns_uri(service, tmp_path, image_gen) -> None:
    pid, iid = await _setup_project_with_character(service, tmp_path)
    tool = ComicCreateTool(service=service, image_gen=image_gen)

    result = await tool.execute(
        {
            "action": "create_panel",
            "project": pid,
            "issue": iid,
            "name": "panel_01",
            "prompt": "Explorer faces a wall of errors",
            "character_uris": [f"comic://{pid}/characters/explorer"],
            "size": "landscape",
        }
    )

    assert result.success is True
    data = json.loads(result.output)
    assert "uri" in data
    assert data["uri"].startswith(f"comic://{pid}/issues/{iid}/panels/panel_01")
    assert "version" in data


@pytest.mark.asyncio(loop_scope="function")
async def test_create_panel_without_characters(service, image_gen) -> None:
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


@pytest.mark.asyncio(loop_scope="function")
async def test_create_panel_missing_prompt(service) -> None:
    tool = ComicCreateTool(service=service)
    result = await tool.execute(
        {
            "action": "create_panel",
            "project": "p",
            "issue": "i",
            "name": "panel_01",
            # missing: prompt
        }
    )
    assert result.success is False


@pytest.mark.asyncio(loop_scope="function")
async def test_create_panel_cleans_up_temp_dir(service, image_gen) -> None:
    """I-5: Temp directory used during create_panel must be removed afterward."""
    import os
    import tempfile

    await service.create_issue("test-proj", "Issue 1")
    tool = ComicCreateTool(service=service, image_gen=image_gen)

    # Snapshot comic_create_ dirs before the call
    tmp_root = tempfile.gettempdir()
    before = {d for d in os.listdir(tmp_root) if d.startswith("comic_create_")}

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

    # No new comic_create_ dirs should remain after the call
    after = {d for d in os.listdir(tmp_root) if d.startswith("comic_create_")}
    leaked = after - before
    assert leaked == set(), f"Temp dirs leaked: {leaked}"
