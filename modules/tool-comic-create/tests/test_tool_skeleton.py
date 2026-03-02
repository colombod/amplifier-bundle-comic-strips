"""Smoke tests for ComicCreateTool skeleton."""
from __future__ import annotations

import pytest

from amplifier_module_comic_create import ComicCreateTool


@pytest.mark.asyncio(loop_scope="function")
async def test_tool_name(service) -> None:
    tool = ComicCreateTool(service=service)
    assert tool.name == "comic_create"


@pytest.mark.asyncio(loop_scope="function")
async def test_unknown_action(service) -> None:
    tool = ComicCreateTool(service=service)
    result = await tool.execute({"action": "does_not_exist"})
    assert result.success is False
    assert "does_not_exist" in result.output


@pytest.mark.asyncio(loop_scope="function")
async def test_all_actions_listed_in_schema(service) -> None:
    tool = ComicCreateTool(service=service)
    schema_actions = tool.input_schema["properties"]["action"]["enum"]
    expected = [
        "create_character_ref", "create_panel", "create_cover",
        "review_asset", "assemble_comic",
    ]
    assert sorted(schema_actions) == sorted(expected)
