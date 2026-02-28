"""Tests for Task 3.1: Explicit tools: sections in all 6 agent YAML frontmatter."""

import yaml
from pathlib import Path

AGENTS_DIR = Path(__file__).parent.parent / "agents"

EXPECTED_TOOLS = {
    "style-curator": ["read_file"],
    "storyboard-writer": ["load_skill", "read_file"],
    "character-designer": ["generate_image", "load_skill"],
    "panel-artist": ["generate_image", "load_skill"],
    "cover-artist": ["generate_image", "load_skill", "read_file", "web_fetch", "bash"],
    "strip-compositor": ["load_skill", "read_file", "write_file", "bash", "delegate"],
}


def _parse_frontmatter(agent_name: str) -> dict:
    """Parse YAML frontmatter from an agent markdown file."""
    file_path = AGENTS_DIR / f"{agent_name}.md"
    content = file_path.read_text()
    assert content.startswith("---"), f"{agent_name}.md does not start with ---"
    # Find the closing ---
    end = content.index("---", 3)
    frontmatter = content[3:end]
    return yaml.safe_load(frontmatter)


def test_all_six_agent_files_have_tools_section():
    """AC1: All 6 agent files have tools: section in YAML frontmatter."""
    for agent_name in EXPECTED_TOOLS:
        data = _parse_frontmatter(agent_name)
        assert "tools" in data, f"{agent_name}.md is missing tools: section"


def test_style_curator_tools():
    """AC2: style-curator has ['read_file']."""
    data = _parse_frontmatter("style-curator")
    assert data["tools"] == ["read_file"]


def test_storyboard_writer_tools():
    """AC3: storyboard-writer has ['load_skill', 'read_file']."""
    data = _parse_frontmatter("storyboard-writer")
    assert data["tools"] == ["load_skill", "read_file"]


def test_character_designer_tools():
    """AC4: character-designer has ['generate_image', 'load_skill']."""
    data = _parse_frontmatter("character-designer")
    assert data["tools"] == ["generate_image", "load_skill"]


def test_panel_artist_tools():
    """AC5: panel-artist has ['generate_image', 'load_skill']."""
    data = _parse_frontmatter("panel-artist")
    assert data["tools"] == ["generate_image", "load_skill"]


def test_cover_artist_tools():
    """AC6: cover-artist has ['generate_image', 'load_skill', 'read_file', 'web_fetch', 'bash']."""
    data = _parse_frontmatter("cover-artist")
    assert data["tools"] == [
        "generate_image",
        "load_skill",
        "read_file",
        "web_fetch",
        "bash",
    ]


def test_strip_compositor_tools():
    """AC7: strip-compositor has ['load_skill', 'read_file', 'write_file', 'bash', 'delegate']."""
    data = _parse_frontmatter("strip-compositor")
    assert data["tools"] == [
        "load_skill",
        "read_file",
        "write_file",
        "bash",
        "delegate",
    ]


def test_all_six_files_parse_as_valid_yaml():
    """AC8: All 6 files parse as valid YAML."""
    for agent_name in EXPECTED_TOOLS:
        data = _parse_frontmatter(agent_name)
        assert isinstance(data, dict), f"{agent_name}.md frontmatter is not a dict"
        # Verify key structure is preserved
        assert "meta" in data, f"{agent_name}.md is missing meta: section"
        assert "provider_preferences" in data, (
            f"{agent_name}.md is missing provider_preferences:"
        )


def test_tools_section_present_in_all_agent_files_via_grep():
    """AC9: grep for 'tools' finds tools in all 6 agent files."""
    for agent_name in EXPECTED_TOOLS:
        file_path = AGENTS_DIR / f"{agent_name}.md"
        content = file_path.read_text()
        # Extract frontmatter only
        end = content.index("---", 3)
        frontmatter = content[3:end]
        assert "tools:" in frontmatter, (
            f"{agent_name}.md frontmatter does not contain 'tools:'"
        )
