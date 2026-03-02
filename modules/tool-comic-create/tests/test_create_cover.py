"""Tests for comic_create(action='create_cover')."""

from __future__ import annotations

import json

import pytest

from amplifier_module_comic_create import ComicCreateTool


@pytest.mark.asyncio(loop_scope="function")
async def test_create_cover_returns_uri(service, image_gen) -> None:
    await service.create_issue("test-proj", "Issue 1")
    tool = ComicCreateTool(service=service, image_gen=image_gen)

    result = await tool.execute(
        {
            "action": "create_cover",
            "project": "test-proj",
            "issue": "issue-001",
            "prompt": "A dramatic group shot of heroes",
            "title": "The Great Debug",
            "subtitle": "Issue 1",
        }
    )

    assert result.success is True
    data = json.loads(result.output)
    assert data["uri"].startswith("comic://test-proj/issues/issue-001/covers/")
    assert "version" in data


@pytest.mark.asyncio(loop_scope="function")
async def test_create_cover_missing_prompt(service) -> None:
    tool = ComicCreateTool(service=service)
    result = await tool.execute(
        {
            "action": "create_cover",
            "project": "p",
            "issue": "i",
            # missing: prompt, title
        }
    )
    assert result.success is False


@pytest.mark.asyncio(loop_scope="function")
async def test_create_cover_cleans_up_temp_dir(service, image_gen) -> None:
    """I-5: Temp directory used during create_cover must be removed afterward."""
    import os
    import tempfile

    await service.create_issue("test-proj", "Issue 1")
    tool = ComicCreateTool(service=service, image_gen=image_gen)

    tmp_root = tempfile.gettempdir()
    before = {d for d in os.listdir(tmp_root) if d.startswith("comic_create_")}

    result = await tool.execute(
        {
            "action": "create_cover",
            "project": "test-proj",
            "issue": "issue-001",
            "prompt": "A dramatic group shot of heroes",
            "title": "Test Comic",
        }
    )
    assert result.success is True

    after = {d for d in os.listdir(tmp_root) if d.startswith("comic_create_")}
    leaked = after - before
    assert leaked == set(), f"Temp dirs leaked: {leaked}"
