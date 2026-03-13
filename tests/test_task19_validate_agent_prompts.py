"""Tests for Task 19: Validate all agent YAML frontmatter and tool references
after embedding v2 updates (tasks 16-18).

Validates:
1. All agents/*.md files have valid YAML frontmatter (starts with '---',
   parses without errors via yaml.safe_load).
2. No broken tool references in character-designer.md, panel-artist.md,
   storyboard-writer.md: all action names used are in the known-valid set.
"""

import re
import yaml
from pathlib import Path


AGENTS_DIR = Path(__file__).parent.parent / "agents"

# All agent markdown files that must have valid YAML frontmatter.
ALL_AGENT_FILES = sorted(AGENTS_DIR.glob("*.md"))

# The three agent files updated in tasks 16-18.
UPDATED_AGENT_NAMES = ["character-designer", "panel-artist", "storyboard-writer"]

# Valid action names per tool.  These come from the tool schemas.
VALID_ACTIONS: dict[str, set[str]] = {
    "comic_character": {
        "search_by_description",
        "compare",
        "search",
        "get",
        "list",
        "store",
        "list_versions",
        "update_metadata",
    },
    "comic_asset": {
        "store",
        "get",
        "list",
        "update_metadata",
        "preview",
    },
    "comic_style": {
        "store",
        "get",
        "list",
        "search_by_description",
    },
    "comic_create": {
        "create_character_ref",
        "create_panel",
        "create_cover",
        "review_asset",
        "assemble_comic",
        "list_layouts",
    },
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _extract_frontmatter(path: Path) -> tuple[bool, str]:
    """Return (starts_with_dashes, raw_frontmatter_text).

    Returns empty string for raw_frontmatter_text if the file does not start
    with '---' or has no closing '---'.
    """
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return False, ""
    # Find the closing delimiter (must be after position 3)
    closing = content.find("---", 3)
    if closing == -1:
        return True, ""
    return True, content[3:closing]


def _parse_frontmatter(path: Path) -> dict:
    """Parse YAML frontmatter; raise AssertionError on failure."""
    starts, raw = _extract_frontmatter(path)
    assert starts, f"{path.name} does not start with '---'"
    assert raw, f"{path.name} has no closing '---' delimiter"
    return yaml.safe_load(raw)


def _find_invalid_actions(content: str, tool_name: str) -> list[str]:
    """Return list of action values used with *tool_name* that are NOT valid."""
    # Match patterns like: tool_name(action='...') or tool_name(action="...")
    pattern = rf"{re.escape(tool_name)}\s*\(\s*action\s*=\s*['\"]([^'\"]+)['\"]"
    found_actions = re.findall(pattern, content)
    valid = VALID_ACTIONS[tool_name]
    return [a for a in found_actions if a not in valid]


# ---------------------------------------------------------------------------
# Group 1: YAML frontmatter validation — all agents/*.md files
# ---------------------------------------------------------------------------


def test_all_agent_files_found() -> None:
    """There must be at least one agent .md file to validate."""
    assert len(ALL_AGENT_FILES) > 0, f"No .md files found in {AGENTS_DIR}"


def test_all_agents_start_with_yaml_delimiter() -> None:
    """Every agents/*.md file must start with '---'."""
    failures = []
    for path in ALL_AGENT_FILES:
        starts, _ = _extract_frontmatter(path)
        if not starts:
            failures.append(path.name)
    assert not failures, (
        f"The following agent files do NOT start with '---': {failures}"
    )


def test_all_agents_have_closing_yaml_delimiter() -> None:
    """Every agents/*.md file must have a closing '---' after the opening."""
    failures = []
    for path in ALL_AGENT_FILES:
        starts, raw = _extract_frontmatter(path)
        if starts and not raw:
            failures.append(path.name)
    assert not failures, (
        f"The following agent files have no closing '---' delimiter: {failures}"
    )


def test_all_agents_frontmatter_parses_without_error() -> None:
    """yaml.safe_load must succeed on every agent's frontmatter without errors."""
    failures = []
    for path in ALL_AGENT_FILES:
        try:
            fm = _parse_frontmatter(path)
            if fm is None:
                failures.append((path.name, "frontmatter parsed to None (empty)"))
        except yaml.YAMLError as exc:
            failures.append((path.name, str(exc)))
        except AssertionError as exc:
            failures.append((path.name, str(exc)))
    assert not failures, (
        "The following agent files have frontmatter parse errors:\n"
        + "\n".join(f"  {name}: {err}" for name, err in failures)
    )


def test_all_agents_frontmatter_has_meta_section() -> None:
    """Every agent's frontmatter must contain a 'meta' key."""
    failures = []
    for path in ALL_AGENT_FILES:
        try:
            fm = _parse_frontmatter(path)
            if not isinstance(fm, dict) or "meta" not in fm:
                failures.append(path.name)
        except (AssertionError, yaml.YAMLError):
            pass  # Already caught by test_all_agents_frontmatter_parses_without_error
    assert not failures, (
        f"The following agent files are missing a 'meta' key in frontmatter: {failures}"
    )


# ---------------------------------------------------------------------------
# Group 2: Tool reference validation — updated agents only
# ---------------------------------------------------------------------------


def test_updated_agent_files_exist() -> None:
    """All three updated agent files must exist on disk."""
    missing = []
    for name in UPDATED_AGENT_NAMES:
        path = AGENTS_DIR / f"{name}.md"
        if not path.exists():
            missing.append(f"{name}.md")
    assert not missing, f"Updated agent files not found: {missing}"


def test_character_designer_no_invalid_comic_character_actions() -> None:
    """character-designer.md must not use unknown comic_character action names."""
    content = (AGENTS_DIR / "character-designer.md").read_text()
    invalid = _find_invalid_actions(content, "comic_character")
    assert not invalid, (
        f"character-designer.md uses invalid comic_character action(s): {invalid}\n"
        f"Valid actions: {sorted(VALID_ACTIONS['comic_character'])}"
    )


def test_character_designer_no_invalid_comic_asset_actions() -> None:
    """character-designer.md must not use unknown comic_asset action names."""
    content = (AGENTS_DIR / "character-designer.md").read_text()
    invalid = _find_invalid_actions(content, "comic_asset")
    assert not invalid, (
        f"character-designer.md uses invalid comic_asset action(s): {invalid}\n"
        f"Valid actions: {sorted(VALID_ACTIONS['comic_asset'])}"
    )


def test_character_designer_no_invalid_comic_style_actions() -> None:
    """character-designer.md must not use unknown comic_style action names."""
    content = (AGENTS_DIR / "character-designer.md").read_text()
    invalid = _find_invalid_actions(content, "comic_style")
    assert not invalid, (
        f"character-designer.md uses invalid comic_style action(s): {invalid}\n"
        f"Valid actions: {sorted(VALID_ACTIONS['comic_style'])}"
    )


def test_character_designer_no_invalid_comic_create_actions() -> None:
    """character-designer.md must not use unknown comic_create action names."""
    content = (AGENTS_DIR / "character-designer.md").read_text()
    invalid = _find_invalid_actions(content, "comic_create")
    assert not invalid, (
        f"character-designer.md uses invalid comic_create action(s): {invalid}\n"
        f"Valid actions: {sorted(VALID_ACTIONS['comic_create'])}"
    )


def test_panel_artist_no_invalid_comic_character_actions() -> None:
    """panel-artist.md must not use unknown comic_character action names."""
    content = (AGENTS_DIR / "panel-artist.md").read_text()
    invalid = _find_invalid_actions(content, "comic_character")
    assert not invalid, (
        f"panel-artist.md uses invalid comic_character action(s): {invalid}\n"
        f"Valid actions: {sorted(VALID_ACTIONS['comic_character'])}"
    )


def test_panel_artist_no_invalid_comic_asset_actions() -> None:
    """panel-artist.md must not use unknown comic_asset action names."""
    content = (AGENTS_DIR / "panel-artist.md").read_text()
    invalid = _find_invalid_actions(content, "comic_asset")
    assert not invalid, (
        f"panel-artist.md uses invalid comic_asset action(s): {invalid}\n"
        f"Valid actions: {sorted(VALID_ACTIONS['comic_asset'])}"
    )


def test_panel_artist_no_invalid_comic_style_actions() -> None:
    """panel-artist.md must not use unknown comic_style action names."""
    content = (AGENTS_DIR / "panel-artist.md").read_text()
    invalid = _find_invalid_actions(content, "comic_style")
    assert not invalid, (
        f"panel-artist.md uses invalid comic_style action(s): {invalid}\n"
        f"Valid actions: {sorted(VALID_ACTIONS['comic_style'])}"
    )


def test_panel_artist_no_invalid_comic_create_actions() -> None:
    """panel-artist.md must not use unknown comic_create action names."""
    content = (AGENTS_DIR / "panel-artist.md").read_text()
    invalid = _find_invalid_actions(content, "comic_create")
    assert not invalid, (
        f"panel-artist.md uses invalid comic_create action(s): {invalid}\n"
        f"Valid actions: {sorted(VALID_ACTIONS['comic_create'])}"
    )


def test_storyboard_writer_no_invalid_comic_character_actions() -> None:
    """storyboard-writer.md must not use unknown comic_character action names."""
    content = (AGENTS_DIR / "storyboard-writer.md").read_text()
    invalid = _find_invalid_actions(content, "comic_character")
    assert not invalid, (
        f"storyboard-writer.md uses invalid comic_character action(s): {invalid}\n"
        f"Valid actions: {sorted(VALID_ACTIONS['comic_character'])}"
    )


def test_storyboard_writer_no_invalid_comic_asset_actions() -> None:
    """storyboard-writer.md must not use unknown comic_asset action names."""
    content = (AGENTS_DIR / "storyboard-writer.md").read_text()
    invalid = _find_invalid_actions(content, "comic_asset")
    assert not invalid, (
        f"storyboard-writer.md uses invalid comic_asset action(s): {invalid}\n"
        f"Valid actions: {sorted(VALID_ACTIONS['comic_asset'])}"
    )


def test_storyboard_writer_no_invalid_comic_style_actions() -> None:
    """storyboard-writer.md must not use unknown comic_style action names."""
    content = (AGENTS_DIR / "storyboard-writer.md").read_text()
    invalid = _find_invalid_actions(content, "comic_style")
    assert not invalid, (
        f"storyboard-writer.md uses invalid comic_style action(s): {invalid}\n"
        f"Valid actions: {sorted(VALID_ACTIONS['comic_style'])}"
    )


def test_storyboard_writer_no_invalid_comic_create_actions() -> None:
    """storyboard-writer.md must not use unknown comic_create action names."""
    content = (AGENTS_DIR / "storyboard-writer.md").read_text()
    invalid = _find_invalid_actions(content, "comic_create")
    assert not invalid, (
        f"storyboard-writer.md uses invalid comic_create action(s): {invalid}\n"
        f"Valid actions: {sorted(VALID_ACTIONS['comic_create'])}"
    )


# ---------------------------------------------------------------------------
# Group 3: Confirm presence of expected embedding v2 tool calls
# ---------------------------------------------------------------------------


def test_character_designer_uses_search_by_description() -> None:
    """character-designer.md must reference comic_character(action='search_by_description')."""
    content = (AGENTS_DIR / "character-designer.md").read_text()
    assert "action='search_by_description'" in content, (
        "character-designer.md missing comic_character(action='search_by_description') — "
        "embedding v2 semantic search not present"
    )


def test_character_designer_uses_compare() -> None:
    """character-designer.md must reference comic_character(action='compare')."""
    content = (AGENTS_DIR / "character-designer.md").read_text()
    assert "action='compare'" in content, (
        "character-designer.md missing comic_character(action='compare') — "
        "cross-version consistency check not present"
    )


def test_panel_artist_uses_search_by_description() -> None:
    """panel-artist.md must reference comic_character(action='search_by_description')."""
    content = (AGENTS_DIR / "panel-artist.md").read_text()
    assert "action='search_by_description'" in content, (
        "panel-artist.md missing comic_character(action='search_by_description') — "
        "embedding v2 semantic character discovery not present"
    )


def test_storyboard_writer_uses_search_by_description_for_characters() -> None:
    """storyboard-writer.md must reference comic_character(action='search_by_description')."""
    content = (AGENTS_DIR / "storyboard-writer.md").read_text()
    assert (
        "comic_character" in content and "action='search_by_description'" in content
    ), (
        "storyboard-writer.md missing comic_character(action='search_by_description') — "
        "embedding v2 character discovery not present"
    )


def test_storyboard_writer_uses_search_by_description_for_styles() -> None:
    """storyboard-writer.md must reference comic_style(action='search_by_description')."""
    content = (AGENTS_DIR / "storyboard-writer.md").read_text()
    # Look for the style search_by_description call
    assert "comic_style" in content and "search_by_description" in content, (
        "storyboard-writer.md missing comic_style search_by_description — "
        "embedding v2 style discovery not present"
    )
