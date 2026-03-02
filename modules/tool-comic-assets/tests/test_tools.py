"""Tests for the four ComicXxxTool classes in amplifier_module_comic_assets."""

from __future__ import annotations

import base64
import json

import pytest

from amplifier_module_comic_assets import (
    ComicAssetTool,
    ComicCharacterTool,
    ComicProjectTool,
    ComicStyleTool,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
_PNG_B64 = base64.b64encode(_PNG).decode("ascii")

_CHAR_STORE_PARAMS = dict(
    role="protagonist",
    character_type="main",
    bundle="comic-strips",
    visual_traits="tall, blue eyes",
    team_markers="hero badge",
    distinctive_features="scar",
)


async def _create_project_issue(
    service, project: str = "tool_test_proj", title: str = "I1"
):
    """Create a project+issue via ComicProjectTool, return (project_id, issue_id)."""
    tool = ComicProjectTool(service)
    r = await tool.execute(
        {"action": "create_issue", "project": project, "title": title}
    )
    data = json.loads(r.output)
    return data["project_id"], data["issue_id"]


# ===========================================================================
# ComicProjectTool
# ===========================================================================


@pytest.mark.asyncio(loop_scope="function")
async def test_comic_project_create_issue(service) -> None:
    tool = ComicProjectTool(service)
    result = await tool.execute(
        {"action": "create_issue", "project": "Test Comic", "title": "Issue One"}
    )
    assert result.success is True
    data = json.loads(result.output)
    assert "project_id" in data
    assert "issue_id" in data
    assert data["issue_id"] == "issue-001"


@pytest.mark.asyncio(loop_scope="function")
async def test_comic_project_list_projects(service) -> None:
    tool = ComicProjectTool(service)
    await tool.execute({"action": "create_issue", "project": "My Comic", "title": "I1"})
    result = await tool.execute({"action": "list_projects"})
    assert result.success is True
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["project_id"] == "my_comic"


@pytest.mark.asyncio(loop_scope="function")
async def test_comic_project_missing_required_param(service) -> None:
    tool = ComicProjectTool(service)
    # "project" key is missing — only "title" is provided
    result = await tool.execute({"action": "create_issue", "title": "Issue 1"})
    assert result.success is False
    assert "project" in result.output


# ===========================================================================
# ComicCharacterTool
# ===========================================================================


@pytest.mark.asyncio(loop_scope="function")
async def test_comic_character_store_and_get(service) -> None:
    pid, iid = await _create_project_issue(service, "char_tool_proj", "I1")
    tool = ComicCharacterTool(service)

    store = await tool.execute(
        {
            "action": "store",
            "project": pid,
            "issue": iid,
            "name": "The Hero",
            "style": "manga",
            "data": _PNG_B64,
            **_CHAR_STORE_PARAMS,
        }
    )
    assert store.success is True
    store_data = json.loads(store.output)
    assert store_data["version"] == 1

    get = await tool.execute({"action": "get", "project": pid, "name": "The Hero"})
    assert get.success is True
    get_data = json.loads(get.output)
    assert get_data["name"] == "The Hero"


# ===========================================================================
# ComicAssetTool
# ===========================================================================


@pytest.mark.asyncio(loop_scope="function")
async def test_comic_asset_store_and_get(service) -> None:
    pid, iid = await _create_project_issue(service, "asset_tool_proj", "I1")
    tool = ComicAssetTool(service)

    store = await tool.execute(
        {
            "action": "store",
            "project": pid,
            "issue": iid,
            "type": "panel",
            "name": "panel_01",
            "data": _PNG_B64,
        }
    )
    assert store.success is True
    store_data = json.loads(store.output)
    assert store_data["version"] == 1

    get = await tool.execute(
        {
            "action": "get",
            "project": pid,
            "issue": iid,
            "type": "panel",
            "name": "panel_01",
        }
    )
    assert get.success is True
    get_data = json.loads(get.output)
    assert get_data["name"] == "panel_01"


# ===========================================================================
# ComicStyleTool
# ===========================================================================


@pytest.mark.asyncio(loop_scope="function")
async def test_comic_style_store_and_get(service) -> None:
    pid, iid = await _create_project_issue(service, "style_tool_proj", "I1")
    tool = ComicStyleTool(service)

    store = await tool.execute(
        {
            "action": "store",
            "project": pid,
            "issue": iid,
            "name": "manga",
            "definition": {"palette": "vibrant", "line_weight": "medium"},
        }
    )
    assert store.success is True
    store_data = json.loads(store.output)
    assert store_data["version"] == 1

    get = await tool.execute({"action": "get", "project": pid, "name": "manga"})
    assert get.success is True
    get_data = json.loads(get.output)
    assert get_data["name"] == "manga"


# ===========================================================================
# Unknown action
# ===========================================================================


@pytest.mark.asyncio(loop_scope="function")
async def test_invalid_action(service) -> None:
    tool = ComicProjectTool(service)
    result = await tool.execute({"action": "does_not_exist"})
    assert result.success is False
    assert "does_not_exist" in result.output


# ===========================================================================
# I-4: schema description must not mention removed `batch_encode`
# ===========================================================================


def test_comic_asset_schema_no_batch_encode_reference(service) -> None:
    """I-4: The 'type' field description must not mention batch_encode."""
    tool = ComicAssetTool(service)
    schema_str = str(tool.input_schema)
    assert "batch_encode" not in schema_str, (
        "Stale 'batch_encode' reference found in ComicAssetTool.input_schema"
    )
