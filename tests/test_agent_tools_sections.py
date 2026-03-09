"""Tests for agent tool guidance in markdown body instructions.

Agents inherit all tools from the parent session. Tool focus is achieved
through instruction-based guidance in the agent body (Asset Integration
sections), not through YAML frontmatter.  These tests verify that each
agent's body contains the correct tool references for its pipeline role.
"""

import pytest
import yaml
from pathlib import Path

pytestmark = pytest.mark.skip(reason="legacy test for pre-v9 recipe")

AGENTS_DIR = Path(__file__).parent.parent / "agents"

# Tools each agent should reference in its body instructions.
EXPECTED_TOOL_REFS = {
    "style-curator": ["comic_style"],
    "storyboard-writer": ["comic_asset", "comic_style"],
    "character-designer": ["comic_character", "comic_style"],
    "panel-artist": ["comic_character", "comic_asset"],
    "cover-artist": ["comic_character", "comic_asset", "comic_style"],
    "strip-compositor": [
        "comic_character",
        "comic_asset",
        "comic_style",
        "batch_encode",
    ],
}

# Tools that specific agents should NOT reference (removed during migration).
EXCLUDED_TOOL_REFS = {
    "cover-artist": ["bash"],
    "strip-compositor": ["read_file"],
}


def _read_frontmatter(agent_name: str) -> str:
    """Read raw YAML frontmatter text from an agent markdown file."""
    file_path = AGENTS_DIR / f"{agent_name}.md"
    content = file_path.read_text()
    assert content.startswith("---"), f"{agent_name}.md does not start with ---"
    try:
        end = content.index("---", 3)
    except ValueError:
        raise ValueError(f"{agent_name}.md has no closing --- delimiter") from None
    return content[3:end]


def _parse_frontmatter(agent_name: str) -> dict:
    """Parse YAML frontmatter from an agent markdown file."""
    return yaml.safe_load(_read_frontmatter(agent_name))


def _read_body(agent_name: str) -> str:
    """Read the markdown body (after frontmatter) from an agent file."""
    file_path = AGENTS_DIR / f"{agent_name}.md"
    content = file_path.read_text()
    end = content.index("---", 3)
    return content[end + 3 :]


def test_no_tools_in_frontmatter():
    """Agent frontmatter should NOT have tools: string lists (they're silently ignored)."""
    for agent_name in EXPECTED_TOOL_REFS:
        data = _parse_frontmatter(agent_name)
        assert "tools" not in data, (
            f"{agent_name}.md has tools: in frontmatter — "
            f"string lists are silently ignored by the framework. "
            f"Use instruction-based tool guidance in the body instead."
        )


def test_all_six_files_parse_as_valid_yaml():
    """All 6 files parse as valid YAML with required sections."""
    for agent_name in EXPECTED_TOOL_REFS:
        data = _parse_frontmatter(agent_name)
        assert isinstance(data, dict), f"{agent_name}.md frontmatter is not a dict"
        assert "meta" in data, f"{agent_name}.md is missing meta: section"
        assert "provider_preferences" in data, (
            f"{agent_name}.md is missing provider_preferences:"
        )


def test_style_curator_tool_refs():
    """style-curator body references comic_style tool."""
    body = _read_body("style-curator")
    for tool in EXPECTED_TOOL_REFS["style-curator"]:
        assert tool in body, f"style-curator body should reference {tool}"


def test_storyboard_writer_tool_refs():
    """storyboard-writer body references comic_asset and comic_style."""
    body = _read_body("storyboard-writer")
    for tool in EXPECTED_TOOL_REFS["storyboard-writer"]:
        assert tool in body, f"storyboard-writer body should reference {tool}"


def test_character_designer_tool_refs():
    """character-designer body references comic_character and comic_style."""
    body = _read_body("character-designer")
    for tool in EXPECTED_TOOL_REFS["character-designer"]:
        assert tool in body, f"character-designer body should reference {tool}"


def test_panel_artist_tool_refs():
    """panel-artist body references comic_character and comic_asset."""
    body = _read_body("panel-artist")
    for tool in EXPECTED_TOOL_REFS["panel-artist"]:
        assert tool in body, f"panel-artist body should reference {tool}"


def test_cover_artist_tool_refs():
    """cover-artist body references asset manager tools."""
    body = _read_body("cover-artist")
    for tool in EXPECTED_TOOL_REFS["cover-artist"]:
        assert tool in body, f"cover-artist body should reference {tool}"


def test_strip_compositor_tool_refs():
    """strip-compositor body references asset manager tools including batch_encode."""
    body = _read_body("strip-compositor")
    for tool in EXPECTED_TOOL_REFS["strip-compositor"]:
        assert tool in body, f"strip-compositor body should reference {tool}"


def test_cover_artist_no_bash_in_asset_integration():
    """cover-artist Asset Integration section should not instruct using bash."""
    body = _read_body("cover-artist")
    # Find the Asset Integration section
    marker = "## Asset Integration"
    idx = body.find(marker)
    assert idx != -1, "cover-artist should have an Asset Integration section"
    integration_section = body[idx:]
    assert (
        "Do NOT use bash" in integration_section or "IMPORTANT" in integration_section
    ), "cover-artist Asset Integration should explicitly warn against bash usage"


def test_strip_compositor_no_delete_instruction():
    """strip-compositor should instruct NOT to delete intermediate files."""
    body = _read_body("strip-compositor")
    assert "Do NOT delete" in body, (
        "strip-compositor should instruct not to delete intermediate files"
    )
