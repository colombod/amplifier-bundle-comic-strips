"""Tests for the /comic-design interactive mode file.

Validates YAML frontmatter structure, required keys, tool policies,
and body content requirements per the design specification.
"""

import yaml
from pathlib import Path

MODE_FILE = Path(__file__).parent.parent / "modes" / "comic-design.md"


def _parse_frontmatter() -> dict:
    """Parse YAML frontmatter from the mode markdown file."""
    text = MODE_FILE.read_text()
    parts = text.split("---")
    assert len(parts) >= 3, "No YAML frontmatter found (expected --- delimiters)"
    data = yaml.safe_load(parts[1])
    assert data is not None, "YAML frontmatter parsed to None"
    return data


def _get_body() -> str:
    """Get the body content after YAML frontmatter."""
    text = MODE_FILE.read_text()
    parts = text.split("---", 2)
    return parts[2] if len(parts) >= 3 else ""


# --- AC 1: File exists ---


def test_comic_design_md_exists():
    assert MODE_FILE.exists(), f"Mode file not found: {MODE_FILE}"


# --- AC 2: YAML parses correctly ---


def test_yaml_frontmatter_parses():
    data = _parse_frontmatter()
    assert isinstance(data, dict)


# --- AC 3: mode.name is 'comic-design' ---


def test_mode_name():
    data = _parse_frontmatter()
    assert data["mode"]["name"] == "comic-design"


# --- AC 4: mode.default_action is 'block' ---


def test_default_action_is_block():
    data = _parse_frontmatter()
    assert data["mode"]["default_action"] == "block"


# --- AC 5: mode.allow_clear is False ---


def test_allow_clear_is_false():
    data = _parse_frontmatter()
    assert data["mode"]["allow_clear"] is False


# --- AC 6: mode.allowed_transitions is ['comic-plan', 'comic-brainstorm'] ---


def test_allowed_transitions():
    data = _parse_frontmatter()
    transitions = data["mode"]["allowed_transitions"]
    assert set(transitions) == {"comic-plan", "comic-brainstorm"}


# --- AC 7: mode.tools.safe includes comic_asset but NOT comic_create ---


def test_comic_asset_in_safe():
    data = _parse_frontmatter()
    safe = data["mode"]["tools"]["safe"]
    assert "comic_asset" in safe, "comic_asset must be in tools.safe"


def test_comic_create_not_in_safe():
    data = _parse_frontmatter()
    safe = data["mode"]["tools"]["safe"]
    assert "comic_create" not in safe, "comic_create must NOT be in tools.safe"


# --- AC 8: comic_create NOT in safe or warn (blocked) ---


def test_comic_create_not_in_safe_or_warn():
    data = _parse_frontmatter()
    tools = data["mode"]["tools"]
    safe = tools.get("safe", [])
    warn = tools.get("warn", [])
    assert "comic_create" not in safe, "comic_create must NOT be in safe"
    assert "comic_create" not in warn, "comic_create must NOT be in warn"


# --- AC 9: Verification script structural coverage ---


def test_required_keys_present():
    data = _parse_frontmatter()
    m = data["mode"]
    for key in ["name", "default_action", "allowed_transitions", "allow_clear"]:
        assert key in m, f"mode.{key} is required"
    assert "tools" in m and "safe" in m["tools"], "mode.tools.safe is required"


# --- Spec content requirements ---


def test_critical_section_exists():
    body = _get_body()
    assert "<CRITICAL>" in body
    assert "comic_create" in body.lower()


def test_hard_gate_section_exists():
    body = _get_body()
    assert "<HARD-GATE>" in body


def test_anti_rationalization_table():
    body = _get_body()
    # Table should have at least 5 entries (rows with |)
    table_rows = [
        line
        for line in body.split("\n")
        if line.strip().startswith("|")
        and "---" not in line
        and "Your Excuse" not in line
    ]
    assert len(table_rows) >= 5, (
        f"Anti-Rationalization Table must have >= 5 entries, found {len(table_rows)}"
    )


def test_spec_safe_tools_list():
    """Verify the full safe tools list from the spec."""
    data = _parse_frontmatter()
    safe = data["mode"]["tools"]["safe"]
    expected = [
        "read_file",
        "glob",
        "grep",
        "delegate",
        "comic_project",
        "comic_character",
        "comic_asset",
        "comic_style",
        "load_skill",
        "web_search",
        "web_fetch",
    ]
    assert set(safe) == set(expected), (
        f"Safe tools mismatch. Expected: {sorted(expected)}, Got: {sorted(safe)}"
    )
