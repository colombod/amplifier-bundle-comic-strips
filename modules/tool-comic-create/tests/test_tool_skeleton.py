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


@pytest.mark.asyncio(loop_scope="function")
async def test_action_description_documents_per_action_params(service) -> None:
    """S-1: action field description must include per-action required-param hints.

    This helps LLMs know which params are needed for each action without
    requiring a flat union of all possible params to be inspected.
    """
    tool = ComicCreateTool(service=service)
    description = tool.input_schema["properties"]["action"]["description"]

    # Each action should appear with its required parameters documented
    assert "create_character_ref" in description
    assert "create_panel" in description
    assert "create_cover" in description
    assert "review_asset" in description
    assert "assemble_comic" in description

    # Key required params should be documented per-action
    assert "visual_traits" in description       # create_character_ref specific
    assert "distinctive_features" in description  # create_character_ref specific
    assert "character_uris" in description       # create_panel / create_cover optional
    assert "reference_uris" in description       # review_asset optional
    assert "output_path" in description          # assemble_comic specific
