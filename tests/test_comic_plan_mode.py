"""Tests for the /comic-plan interactive mode file.

Validates YAML frontmatter structure, required keys, tool policies,
and body content requirements per the design specification.
"""

import yaml
from pathlib import Path

MODE_FILE = Path(__file__).parent.parent / "modes" / "comic-plan.md"


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


def test_comic_plan_md_exists():
    assert MODE_FILE.exists(), f"Mode file not found: {MODE_FILE}"


# --- AC 2: YAML parses correctly ---


def test_yaml_frontmatter_parses():
    data = _parse_frontmatter()
    assert isinstance(data, dict)
    assert "mode" in data, "Top-level 'mode' key missing from frontmatter"


# --- AC 3: mode.name is 'comic-plan' ---


def test_mode_name():
    data = _parse_frontmatter()
    assert data["mode"]["name"] == "comic-plan"


# --- AC 4: mode.default_action is 'block' ---


def test_default_action_is_block():
    data = _parse_frontmatter()
    assert data["mode"]["default_action"] == "block"


# --- AC 5: mode.allow_clear is False ---


def test_allow_clear_is_false():
    data = _parse_frontmatter()
    assert data["mode"]["allow_clear"] is False


# --- AC 6: mode.allowed_transitions is ['comic-review', 'comic-design', 'comic-brainstorm'] ---


def test_allowed_transitions():
    data = _parse_frontmatter()
    transitions = data["mode"]["allowed_transitions"]
    assert transitions == ["comic-review", "comic-design", "comic-brainstorm"]


# --- AC 7: mode.tools.safe includes comic_create AND recipes ---


def test_comic_create_in_safe():
    data = _parse_frontmatter()
    safe = data["mode"]["tools"]["safe"]
    assert "comic_create" in safe, "comic_create must be in tools.safe (pivot point)"


def test_recipes_in_safe():
    data = _parse_frontmatter()
    safe = data["mode"]["tools"]["safe"]
    assert "recipes" in safe, "recipes must be in tools.safe (pivot point)"


def test_full_safe_tools_list():
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
        "comic_style",
        "comic_asset",
        "comic_create",
        "recipes",
        "load_skill",
        "web_search",
        "web_fetch",
    ]
    assert set(safe) == set(expected), (
        f"Safe tools mismatch. Expected: {sorted(expected)}, Got: {sorted(safe)}"
    )


# --- AC 8: mode.tools.warn is ['bash'] ---


def test_warn_tools():
    data = _parse_frontmatter()
    warn = data["mode"]["tools"]["warn"]
    assert warn == ["bash"], f"Warn tools should be ['bash'], got {warn}"


# --- Structural checks ---


def test_mode_shortcut():
    data = _parse_frontmatter()
    assert data["mode"]["shortcut"] == "comic-plan"


def test_mode_description():
    data = _parse_frontmatter()
    desc = data["mode"]["description"]
    assert "pipeline" in desc.lower() or "generation" in desc.lower(), (
        f"Description should mention pipeline or generation: {desc}"
    )


def test_required_keys_present():
    data = _parse_frontmatter()
    m = data["mode"]
    for key in ["name", "default_action", "allowed_transitions", "allow_clear"]:
        assert key in m, f"mode.{key} is required"
    assert "tools" in m and "safe" in m["tools"], "mode.tools.safe is required"
    assert "warn" in m["tools"], "mode.tools.warn is required"


# --- Body content checks per spec ---


def test_critical_section_exists():
    body = _get_body()
    assert "<CRITICAL>" in body, "Missing <CRITICAL> section"
    assert "comic_create" in body, "CRITICAL section should mention comic_create"
    assert "write_file" in body.lower() or "write_file" in body, (
        "CRITICAL section should mention write_file being blocked"
    )


def test_hard_gate_with_5_requirements():
    body = _get_body()
    assert "<HARD-GATE>" in body, "Missing <HARD-GATE> section"
    # 5 pre-execution requirements
    assert "project" in body.lower()
    assert "style guide" in body.lower()
    assert "character roster" in body.lower()
    assert "storyboard" in body.lower()
    assert "budget" in body.lower()


def test_todo_checklist():
    body = _get_body()
    checklist_items = [
        line for line in body.split("\n") if line.strip().startswith("- [ ]")
    ]
    assert len(checklist_items) >= 5, (
        f"Todo checklist should have >= 5 items, found {len(checklist_items)}"
    )


def test_4_process_phases():
    body = _get_body()
    assert "Pre-Flight" in body or "Pre-flight" in body
    assert "Generation Strategy" in body
    assert "Execute Pipeline" in body or "Execute" in body
    assert "Monitor" in body and "Approv" in body


def test_anti_rationalization_table():
    body = _get_body()
    assert "Anti-Rationalization" in body, "Missing Anti-Rationalization Table"
    lines = [line for line in body.split("\n") if line.strip().startswith("|")]
    content_rows = [
        line
        for line in lines
        if not line.strip().startswith("| Your Excuse")
        and not line.strip().startswith("|---")
    ]
    assert len(content_rows) >= 5, (
        f"Anti-Rationalization Table should have >= 5 entries, found {len(content_rows)}"
    )


def test_do_not_list():
    body = _get_body()
    assert "Do NOT" in body, "Missing 'Do NOT' section"
    in_donot = False
    donot_items = []
    for line in body.split("\n"):
        if "Do NOT" in line and "#" in line:
            in_donot = True
            continue
        if in_donot:
            if line.strip().startswith("- "):
                donot_items.append(line.strip())
            elif line.strip().startswith("#"):
                break
    assert len(donot_items) >= 5, (
        f"Do NOT list should have >= 5 items, found {len(donot_items)}"
    )


def test_announcement_text():
    body = _get_body()
    assert "Announcement" in body, "Missing Announcement section"
    assert "comic-plan" in body.lower()


def test_transitions_section():
    body = _get_body()
    assert "Transitions" in body, "Missing Transitions section"
    assert "Golden path" in body, "Missing golden path description"
    assert "/comic-review" in body, "Golden path should mention /comic-review"
    assert "/comic-design" in body, "Back path should mention /comic-design"
    assert "/comic-brainstorm" in body, "Back path should mention /comic-brainstorm"


def test_recipe_examples_in_body():
    """Spec requires saga-plan.yaml or session-to-comic.yaml recipe examples."""
    body = _get_body()
    assert "saga-plan" in body.lower() or "session-to-comic" in body.lower(), (
        "Body should mention saga-plan.yaml or session-to-comic.yaml recipe examples"
    )
