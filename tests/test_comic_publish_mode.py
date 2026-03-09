"""Tests for the /comic-publish interactive mode file.

Validates YAML frontmatter structure, required keys, tool policies,
and body content requirements per the design specification.
"""

import pytest
import yaml
from pathlib import Path

MODE_FILE = Path(__file__).parent.parent / "modes" / "comic-publish.md"


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


def test_comic_publish_md_exists():
    assert MODE_FILE.exists(), f"Mode file not found: {MODE_FILE}"


# --- AC 2: YAML parses correctly ---


def test_yaml_frontmatter_parses():
    data = _parse_frontmatter()
    assert isinstance(data, dict)
    assert "mode" in data, "Top-level 'mode' key missing from frontmatter"


# --- AC 3: mode.name is 'comic-publish' ---


def test_mode_name():
    data = _parse_frontmatter()
    assert data["mode"]["name"] == "comic-publish"


# --- AC 4: mode.default_action is 'block' ---


def test_default_action_is_block():
    data = _parse_frontmatter()
    assert data["mode"]["default_action"] == "block"


# --- AC 5: mode.allow_clear is True (ONLY mode with this) ---


def test_allow_clear_is_true():
    data = _parse_frontmatter()
    assert data["mode"]["allow_clear"] is True


def test_only_mode_with_allow_clear_true():
    """Verify comic-publish is the ONLY mode with allow_clear: true."""
    modes_dir = MODE_FILE.parent
    for mode_file in modes_dir.glob("comic-*.md"):
        if mode_file.name == "comic-publish.md":
            continue
        text = mode_file.read_text()
        parts = text.split("---")
        if len(parts) >= 3:
            data = yaml.safe_load(parts[1])
            if data and "mode" in data:
                assert data["mode"].get("allow_clear") is not True, (
                    f"{mode_file.name} has allow_clear: true but only comic-publish should"
                )


# --- AC 6: mode.allowed_transitions is ['comic-review'] ---


def test_allowed_transitions():
    data = _parse_frontmatter()
    transitions = data["mode"]["allowed_transitions"]
    assert transitions == ["comic-review"]


# --- AC 7: mode.tools.safe includes write_file AND edit_file (unique to this mode) ---


def test_write_file_in_safe():
    data = _parse_frontmatter()
    safe = data["mode"]["tools"]["safe"]
    assert "write_file" in safe, "write_file must be in tools.safe"


def test_edit_file_in_safe():
    data = _parse_frontmatter()
    safe = data["mode"]["tools"]["safe"]
    assert "edit_file" in safe, "edit_file must be in tools.safe"


def test_full_safe_tools_list():
    """Verify the full safe tools list from the spec."""
    data = _parse_frontmatter()
    safe = data["mode"]["tools"]["safe"]
    expected = [
        "read_file",
        "glob",
        "grep",
        "bash",
        "delegate",
        "recipes",
        "comic_create",
        "comic_asset",
        "comic_character",
        "comic_style",
        "comic_project",
        "load_skill",
        "web_search",
        "web_fetch",
        "write_file",
        "edit_file",
    ]
    assert set(safe) == set(expected), (
        f"Safe tools mismatch. Expected: {sorted(expected)}, Got: {sorted(safe)}"
    )


def test_write_file_edit_file_unique_to_publish():
    """write_file and edit_file should NOT be in safe for other modes."""
    modes_dir = MODE_FILE.parent
    for mode_file in modes_dir.glob("comic-*.md"):
        if mode_file.name == "comic-publish.md":
            continue
        text = mode_file.read_text()
        parts = text.split("---")
        if len(parts) >= 3:
            data = yaml.safe_load(parts[1])
            if data and "mode" in data:
                safe = data["mode"].get("tools", {}).get("safe", [])
                assert "write_file" not in safe, (
                    f"{mode_file.name} has write_file in safe but only comic-publish should"
                )
                assert "edit_file" not in safe, (
                    f"{mode_file.name} has edit_file in safe but only comic-publish should"
                )


# --- Structural checks ---


def test_mode_shortcut():
    data = _parse_frontmatter()
    assert data["mode"]["shortcut"] == "comic-publish"


def test_mode_description():
    data = _parse_frontmatter()
    desc = data["mode"]["description"]
    assert "final" in desc.lower() or "qa" in desc.lower() or "ship" in desc.lower(), (
        f"Description should mention final QA or shipping: {desc}"
    )


def test_required_keys_present():
    data = _parse_frontmatter()
    m = data["mode"]
    for key in ["name", "default_action", "allowed_transitions", "allow_clear"]:
        assert key in m, f"mode.{key} is required"
    assert "tools" in m and "safe" in m["tools"], "mode.tools.safe is required"


# --- Body content checks per spec ---


def test_critical_section_exists():
    body = _get_body()
    assert "<CRITICAL>" in body, "Missing <CRITICAL> section"
    assert "html" in body.lower(), "CRITICAL section should mention assembled HTML"
    assert "cover" in body.lower(), "CRITICAL section should mention cover"
    assert "images" in body.lower() or "embedded" in body.lower(), (
        "CRITICAL section should mention images embedded"
    )


def test_4_step_process():
    body = _get_body()
    body_lower = body.lower()
    assert "final qa" in body_lower or "qa checklist" in body_lower, (
        "Missing Final QA Checklist step"
    )
    assert "package" in body_lower or "deliverables" in body_lower, (
        "Missing Package Deliverables step"
    )
    assert "summary" in body_lower or "present" in body_lower, (
        "Missing Present Summary step"
    )
    assert "ship" in body_lower, "Missing Ship It step"


def test_qa_checklist_items():
    """QA checklist should check HTML exists, size, cover, panels, dialogue, layouts, saga."""
    body = _get_body()
    body_lower = body.lower()
    assert "html" in body_lower and "exist" in body_lower, "QA must check HTML exists"
    assert "size" in body_lower, "QA must check size is reasonable"
    assert "cover" in body_lower, "QA must check cover is embedded"
    assert "panel" in body_lower, "QA must check panels are embedded"
    assert "dialogue" in body_lower, "QA must check dialogue is present"
    assert "layout" in body_lower or "render" in body_lower, (
        "QA must check layouts render"
    )
    assert "saga" in body_lower or "continuity" in body_lower, (
        "QA must check saga continuity"
    )


def test_anti_rationalization_table():
    body = _get_body()
    assert "Anti-Rationalization" in body, "Missing Anti-Rationalization Table"
    lines = [line for line in body.split("\n") if line.strip().startswith("|")]
    content_rows = [
        line
        for line in lines
        if not line.strip().startswith("| Your Excuse")
        and not line.strip().startswith("|---")
        and not line.strip().startswith("| ---")
    ]
    assert len(content_rows) >= 3, (
        f"Anti-Rationalization Table should have >= 3 entries, found {len(content_rows)}"
    )


def test_announcement_text():
    body = _get_body()
    assert "Announcement" in body, "Missing Announcement section"
    assert "comic-publish" in body.lower()


def test_transitions_section():
    body = _get_body()
    assert "Transitions" in body, "Missing Transitions section"
    assert "mode clear" in body.lower() or "mode(operation='clear')" in body, (
        "Should mention exit via mode clear"
    )
    assert "/comic-review" in body, "Back path should mention /comic-review"


def test_ship_it_mentions_mode_clear():
    """Ship It step should use mode clear to exit."""
    body = _get_body()
    assert "mode" in body.lower() and "clear" in body.lower(), (
        "Ship It step must mention mode clear for exit"
    )


# --- AC 8: Full verification script passes ---


def test_verification_script_publish_checks():
    """Run the full verification script - all mode checks should pass."""
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
    output = result.stdout + result.stderr
    # Check that publish-specific checks pass
    publish_failures = [
        line
        for line in output.split("\n")
        if "comic-publish" in line and "\u2717" in line
    ]
    assert len(publish_failures) == 0, (
        "Verification script failed for comic-publish:\n" + "\n".join(publish_failures)
    )
