"""Tests for URI input support on comic_style, comic_asset, comic_character.

I-6: All three CRUD tools should accept `uri` as an alternative to decomposed
project/issue/type/name parameters.

v2 URI formats:
  - Issue-scoped:   comic://project/issues/issue-id/panels/panel_01
  - Project-scoped: comic://project/characters/explorer
  - Project-scoped: comic://project/styles/manga
"""

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
from amplifier_module_comic_assets import _parse_uri_params  # type: ignore[attr-defined]

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


async def _setup_project(service, project: str = "uri_test_proj", title: str = "I1"):
    """Create a project+issue, return (project_id, issue_id)."""
    tool = ComicProjectTool(service)
    r = await tool.execute(
        {"action": "create_issue", "project": project, "title": title}
    )
    data = json.loads(r.output)
    return data["project_id"], data["issue_id"]


# ---------------------------------------------------------------------------
# _parse_uri_params unit tests — scope-awareness and singularization
# ---------------------------------------------------------------------------


def test_project_scoped_uri_does_not_set_issue() -> None:
    """Project-scoped URI (characters) must NOT populate params['issue']."""
    params: dict = {"uri": "comic://my-project/characters/explorer"}
    err = _parse_uri_params(params)
    assert err is None
    assert "issue" not in params
    assert params["project"] == "my-project"
    assert params["name"] == "explorer"
    assert params["type"] == "character"  # singularized from "characters"


def test_issue_scoped_uri_sets_issue() -> None:
    """Issue-scoped URI (panels) MUST populate params['issue']."""
    params: dict = {"uri": "comic://my-project/issues/issue-001/panels/panel_01"}
    err = _parse_uri_params(params)
    assert err is None
    assert params["issue"] == "issue-001"
    assert params["project"] == "my-project"
    assert params["name"] == "panel_01"
    assert params["type"] == "panel"  # singularized from "panels"


def test_type_is_singularized() -> None:
    """URI uses plural collection name 'panels'; params['type'] must be singular 'panel'."""
    params: dict = {"uri": "comic://my-project/issues/issue-001/panels/panel_01"}
    _parse_uri_params(params)
    assert params["type"] == "panel"


# ---------------------------------------------------------------------------
# comic_asset: get via URI
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_comic_asset_get_via_uri(service) -> None:
    """comic_asset(action='get', uri='comic://proj/issues/issue-001/panels/panel_01') resolves correctly."""
    pid, iid = await _setup_project(service, "asset_uri_proj", "I1")
    tool = ComicAssetTool(service)

    # Store an asset first
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

    # Retrieve via v2 issue-scoped URI — no project/issue/type/name explicitly
    uri = f"comic://{pid}/issues/{iid}/panels/panel_01"
    result = await tool.execute({"action": "get", "uri": uri})

    assert result.success is True
    data = json.loads(result.output)
    assert data["name"] == "panel_01"


# ---------------------------------------------------------------------------
# comic_character: get via URI
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_comic_character_get_via_uri(service) -> None:
    """comic_character(action='get', uri='comic://proj/characters/explorer') resolves correctly."""
    pid, iid = await _setup_project(service, "char_uri_proj", "I1")
    tool = ComicCharacterTool(service)

    # Store a character first
    store = await tool.execute(
        {
            "action": "store",
            "project": pid,
            "issue": iid,
            "name": "explorer",
            "style": "manga",
            "data": _PNG_B64,
            **_CHAR_STORE_PARAMS,
        }
    )
    assert store.success is True

    # Retrieve via v2 project-scoped URI — no project/name explicitly
    uri = f"comic://{pid}/characters/explorer"
    result = await tool.execute({"action": "get", "uri": uri})

    assert result.success is True
    data = json.loads(result.output)
    assert data["name"] == "explorer"


# ---------------------------------------------------------------------------
# comic_style: get via URI
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_comic_style_get_via_uri(service) -> None:
    """comic_style(action='get', uri='comic://proj/styles/manga') resolves correctly."""
    pid, iid = await _setup_project(service, "style_uri_proj", "I1")
    tool = ComicStyleTool(service)

    # Store a style guide first
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

    # Retrieve via v2 project-scoped URI
    uri = f"comic://{pid}/styles/manga"
    result = await tool.execute({"action": "get", "uri": uri})

    assert result.success is True
    data = json.loads(result.output)
    assert data["name"] == "manga"


# ---------------------------------------------------------------------------
# Explicit params take priority over URI-parsed values
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_explicit_params_override_uri(service) -> None:
    """Params explicitly provided take priority over URI-extracted values (setdefault semantics).

    We store two panels (panel_01 and panel_02) in the same project/issue.
    We call get() with uri pointing to panel_01 but override name=panel_02 explicitly.
    The result should be panel_02 — the explicit param wins.
    """
    pid, iid = await _setup_project(service, "override_proj", "I1")
    tool = ComicAssetTool(service)

    # Store both panels
    for panel_name in ("panel_01", "panel_02"):
        r = await tool.execute(
            {
                "action": "store",
                "project": pid,
                "issue": iid,
                "type": "panel",
                "name": panel_name,
                "data": _PNG_B64,
            }
        )
        assert r.success is True

    # URI points to panel_01 (v2 format), but explicit name=panel_02 should win
    uri = f"comic://{pid}/issues/{iid}/panels/panel_01"
    result = await tool.execute(
        {
            "action": "get",
            "uri": uri,
            "project": pid,
            "issue": iid,
            "type": "panel",
            "name": "panel_02",  # explicit override
        }
    )

    assert result.success is True
    data = json.loads(result.output)
    assert data["name"] == "panel_02"  # explicit param won


# ---------------------------------------------------------------------------
# Invalid URI returns a clear error
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_invalid_uri_returns_error(service) -> None:
    """A malformed URI produces a clear error, not an exception."""
    tool = ComicAssetTool(service)
    result = await tool.execute({"action": "get", "uri": "not-a-uri"})

    assert result.success is False
    assert "Invalid URI" in result.output


@pytest.mark.asyncio(loop_scope="function")
async def test_invalid_uri_character_tool(service) -> None:
    """A malformed URI produces a clear error from comic_character too."""
    tool = ComicCharacterTool(service)
    result = await tool.execute({"action": "get", "uri": "not-a-uri"})

    assert result.success is False
    assert "Invalid URI" in result.output


@pytest.mark.asyncio(loop_scope="function")
async def test_invalid_uri_style_tool(service) -> None:
    """A malformed URI produces a clear error from comic_style too."""
    tool = ComicStyleTool(service)
    result = await tool.execute({"action": "get", "uri": "not-a-uri"})

    assert result.success is False
    assert "Invalid URI" in result.output
