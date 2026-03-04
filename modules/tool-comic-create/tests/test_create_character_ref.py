"""Tests for comic_create(action='create_character_ref')."""

from __future__ import annotations

import json

import pytest

from amplifier_module_comic_create import ComicCreateTool


@pytest.mark.asyncio(loop_scope="function")
async def test_create_character_ref_returns_uri(service, image_gen) -> None:
    # Setup: create a project + issue first
    await service.create_issue("test-proj", "Issue 1")

    tool = ComicCreateTool(service=service, image_gen=image_gen)

    result = await tool.execute(
        {
            "action": "create_character_ref",
            "project": "test-proj",
            "issue": "issue-001",
            "name": "The Explorer",
            "prompt": "A seasoned scout in worn leather jacket",
            "visual_traits": "tall, blue eyes, leather jacket",
            "distinctive_features": "compass pendant, scar on cheek",
        }
    )

    assert result.success is True
    data = json.loads(result.output)
    assert "uri" in data
    assert data["uri"].startswith("comic://test-proj/characters/")
    assert "version" in data
    assert isinstance(data["version"], int)


@pytest.mark.asyncio(loop_scope="function")
async def test_create_character_ref_missing_required_param(service) -> None:
    tool = ComicCreateTool(service=service)
    result = await tool.execute(
        {
            "action": "create_character_ref",
            "project": "test-proj",
            "issue": "issue-001",
            # missing: name, prompt, visual_traits, distinctive_features
        }
    )
    assert result.success is False
    assert "Missing" in result.output


@pytest.mark.asyncio(loop_scope="function")
async def test_create_character_ref_no_image_gen(service) -> None:
    await service.create_issue("test-proj", "Issue 1")
    tool = ComicCreateTool(service=service, image_gen=None)

    result = await tool.execute(
        {
            "action": "create_character_ref",
            "project": "test-proj",
            "issue": "issue-001",
            "name": "Explorer",
            "prompt": "A scout",
            "visual_traits": "tall",
            "distinctive_features": "scar",
        }
    )
    assert result.success is False
    assert "image generation" in result.output.lower()


@pytest.mark.asyncio(loop_scope="function")
async def test_create_character_ref_cleans_up_temp_dir(service, image_gen) -> None:
    """I-5: Temp directory used during create_character_ref must be removed afterward."""
    import os
    import tempfile

    await service.create_issue("test-proj", "Issue 1")
    tool = ComicCreateTool(service=service, image_gen=image_gen)

    tmp_root = tempfile.gettempdir()
    before = {d for d in os.listdir(tmp_root) if d.startswith("comic_create_")}

    result = await tool.execute(
        {
            "action": "create_character_ref",
            "project": "test-proj",
            "issue": "issue-001",
            "name": "The Explorer",
            "prompt": "A seasoned scout",
            "visual_traits": "tall, blue eyes",
            "distinctive_features": "scar",
        }
    )
    assert result.success is True

    after = {d for d in os.listdir(tmp_root) if d.startswith("comic_create_")}
    leaked = after - before
    assert leaked == set(), f"Temp dirs leaked: {leaked}"
