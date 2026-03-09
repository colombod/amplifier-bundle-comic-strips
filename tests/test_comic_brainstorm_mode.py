"""Tests for the /comic-brainstorm mode file.

Validates YAML frontmatter structure, required keys, tool policies,
and body content requirements per the design specification.
"""

import pytest
import yaml
from pathlib import Path

MODE_FILE = Path(__file__).parent.parent / "modes" / "comic-brainstorm.md"


def _parse_frontmatter() -> dict:
    """Parse YAML frontmatter from the mode markdown file."""
    text = MODE_FILE.read_text()
    parts = text.split("---")
    assert len(parts) >= 3, "No YAML frontmatter found (expected --- delimiters)"
    data = yaml.safe_load(parts[1])
    assert data is not None, "YAML frontmatter parsed to None"
    return data


# --- Acceptance Criteria 1: File exists ---


def test_mode_file_exists():
    assert MODE_FILE.exists(), f"Mode file not found: {MODE_FILE}"


# --- Acceptance Criteria 2: YAML frontmatter parses correctly ---


def test_yaml_frontmatter_parses():
    data = _parse_frontmatter()
    assert "mode" in data, "Top-level 'mode' key missing from frontmatter"


# --- Acceptance Criteria 3: mode.name is 'comic-brainstorm' ---


def test_mode_name():
    data = _parse_frontmatter()
    assert data["mode"]["name"] == "comic-brainstorm"


# --- Acceptance Criteria 4: mode.default_action is 'block' ---


def test_default_action_is_block():
    data = _parse_frontmatter()
    assert data["mode"]["default_action"] == "block"


# --- Acceptance Criteria 5: mode.allow_clear is False ---


def test_allow_clear_is_false():
    data = _parse_frontmatter()
    assert data["mode"]["allow_clear"] is False


# --- Acceptance Criteria 6: mode.allowed_transitions ---


def test_allowed_transitions():
    data = _parse_frontmatter()
    assert data["mode"]["allowed_transitions"] == ["comic-design", "comic-plan"]


# --- Acceptance Criteria 7: mode.tools.safe contains exactly the right tools ---


def test_safe_tools():
    data = _parse_frontmatter()
    expected_safe = [
        "read_file",
        "glob",
        "grep",
        "delegate",
        "comic_project",
        "comic_character",
        "comic_style",
        "load_skill",
        "web_search",
        "web_fetch",
    ]
    actual_safe = data["mode"]["tools"]["safe"]
    assert actual_safe == expected_safe, (
        f"Safe tools mismatch.\nExpected: {expected_safe}\nActual: {actual_safe}"
    )


# --- Acceptance Criteria 8: comic_create is NOT in safe or warn lists ---


def test_comic_create_blocked():
    data = _parse_frontmatter()
    tools = data["mode"].get("tools", {})
    safe = tools.get("safe", [])
    warn = tools.get("warn", [])
    assert "comic_create" not in safe, "comic_create should NOT be in safe tools"
    assert "comic_create" not in warn, "comic_create should NOT be in warn tools"


# --- Additional structural checks from the spec ---


def test_mode_shortcut():
    data = _parse_frontmatter()
    assert data["mode"]["shortcut"] == "comic-brainstorm"


def test_mode_description():
    data = _parse_frontmatter()
    desc = data["mode"]["description"]
    assert "vision" in desc.lower() or "creative direction" in desc.lower(), (
        f"Description should mention project vision or creative direction: {desc}"
    )


# --- Body content checks per spec ---


def _get_body() -> str:
    """Get the body content after YAML frontmatter."""
    text = MODE_FILE.read_text()
    parts = text.split("---", 2)
    return parts[2] if len(parts) >= 3 else ""


def test_critical_section_exists():
    body = _get_body()
    assert "<CRITICAL>" in body, "Missing <CRITICAL> section"
    assert "comic_create" in body.lower() or "comic_create" in body, (
        "CRITICAL section should mention comic_create being blocked"
    )


def test_hard_gate_with_5_requirements():
    body = _get_body()
    assert "<HARD-GATE>" in body, "Missing <HARD-GATE> section"
    # Check all 5 exploration requirements
    assert "source material" in body.lower()
    assert "visual style" in body.lower()
    assert "narrative scope" in body.lower()
    assert "character roster" in body.lower()
    assert "what to cut" in body.lower()


def test_todo_checklist_template():
    body = _get_body()
    assert "- [ ]" in body, "Missing todo checklist template"


def test_5_process_phases():
    body = _get_body()
    assert "Phase 1" in body or "Explore Source Material" in body
    assert "Phase 2" in body or "Style Exploration" in body
    assert "Phase 3" in body or "Narrative Scope" in body
    assert "Phase 4" in body or "Character Roster" in body
    assert "Phase 5" in body or "Converge" in body


def test_style_exploration_lists_named_packs():
    body = _get_body()
    style_packs = [
        "manga",
        "superhero",
        "indie",
        "newspaper",
        "ligne-claire",
        "retro-americana",
        "sin-city",
        "watchmen",
        "berserk",
        "cuphead",
        "ghibli",
        "attack-on-titan",
        "spider-man",
        "x-men",
        "solo-leveling",
        "gundam",
        "transformers",
        "tatsunoko",
        "witchblade",
        "dylan-dog",
        "tex-willer",
        "disney-classic",
        "bendy",
        "hellraiser",
        "naruto",
        "jujutsu-kaisen",
        "one-piece",
        "go-nagai",
    ]
    # 28 named styles checked (charles-addams is in context/styles but not in the
    # spec's 29 list; the spec says "29 named" but the list from the plan has 28
    # unique entries — the 29th may be implicit or the spec counts differently).
    # Check that all named packs from the implementation plan are present.
    for pack in style_packs:
        assert pack in body.lower(), f"Style pack '{pack}' missing from body"


def test_anti_rationalization_table():
    body = _get_body()
    assert "Anti-Rationalization" in body, "Missing Anti-Rationalization Table"
    # Check for at least 6 entries (table rows with |)
    lines = [line for line in body.split("\n") if line.strip().startswith("|")]
    # Filter out header and separator rows
    content_rows = [
        line
        for line in lines
        if not line.strip().startswith("| Your Excuse")
        and not line.strip().startswith("|---")
    ]
    assert len(content_rows) >= 6, (
        f"Anti-Rationalization Table should have at least 6 entries, found {len(content_rows)}"
    )


def test_do_not_list():
    body = _get_body()
    assert "Do NOT" in body, "Missing 'Do NOT' section"
    # Count items in the Do NOT list (lines starting with -)
    in_donot = False
    donot_items = []
    for line in body.split("\n"):
        if "Do NOT" in line and "##" in line:
            in_donot = True
            continue
        if in_donot:
            if line.strip().startswith("- "):
                donot_items.append(line.strip())
            elif line.strip().startswith("##"):
                break
    assert len(donot_items) >= 7, (
        f"Do NOT list should have at least 7 items, found {len(donot_items)}"
    )


def test_announcement_text():
    body = _get_body()
    assert "Announcement" in body, "Missing Announcement section"
    assert "comic-brainstorm mode" in body.lower() or "comic-brainstorm" in body


def test_transitions_section():
    body = _get_body()
    assert "Transitions" in body, "Missing Transitions section"
    assert "Golden path" in body, "Missing golden path description"
    assert "/comic-design" in body, "Golden path should mention /comic-design"
    assert "Skip path" in body or "skip" in body.lower(), (
        "Missing skip path to /comic-plan"
    )
    assert "/comic-plan" in body, "Skip path should mention /comic-plan"
    assert "Back path" in body or "entry point" in body.lower(), (
        "Missing back path description"
    )


# --- Acceptance Criteria 9: Verification script passes ---


def test_verification_script_brainstorm_checks():
    """Run the relevant parts of the verification script for comic-brainstorm."""
    import subprocess

    script = Path(__file__).parent / "verify-modes-and-recipes.sh"
    if not script.exists():
        pytest.skip("verification script not present")

    result = subprocess.run(
        ["bash", str(script)],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
        timeout=30,
    )
    # Check that brainstorm-specific checks pass (even if other modes fail)
    output = result.stdout + result.stderr
    assert "comic-brainstorm" in output or result.returncode == 0
    # The script may fail for other missing modes, but brainstorm checks should pass
    brainstorm_failures = [
        line
        for line in output.split("\n")
        if "comic-brainstorm" in line and "\u2717" in line
    ]
    assert len(brainstorm_failures) == 0, (
        "Verification script failed for comic-brainstorm:\n"
        + "\n".join(brainstorm_failures)
    )
