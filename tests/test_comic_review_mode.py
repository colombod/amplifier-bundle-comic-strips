"""Tests for the /comic-review interactive mode file.

Validates YAML frontmatter structure, required keys, tool policies,
and body content requirements per the design specification.
"""

import yaml
from pathlib import Path

MODE_FILE = Path(__file__).parent.parent / "modes" / "comic-review.md"


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


def test_comic_review_md_exists():
    assert MODE_FILE.exists(), f"Mode file not found: {MODE_FILE}"


# --- AC 2: YAML parses correctly ---


def test_yaml_frontmatter_parses():
    data = _parse_frontmatter()
    assert isinstance(data, dict)
    assert "mode" in data, "Top-level 'mode' key missing from frontmatter"


# --- AC 3: mode.name is 'comic-review' ---


def test_mode_name():
    data = _parse_frontmatter()
    assert data["mode"]["name"] == "comic-review"


# --- AC 4: mode.default_action is 'block' ---


def test_default_action_is_block():
    data = _parse_frontmatter()
    assert data["mode"]["default_action"] == "block"


# --- AC 5: mode.allow_clear is False ---


def test_allow_clear_is_false():
    data = _parse_frontmatter()
    assert data["mode"]["allow_clear"] is False


# --- AC 6: mode.allowed_transitions is ['comic-publish', 'comic-plan'] ---


def test_allowed_transitions():
    data = _parse_frontmatter()
    transitions = data["mode"]["allowed_transitions"]
    assert transitions == ["comic-publish", "comic-plan"]


# --- AC 7: mode.tools.safe includes comic_create, recipes, bash ---


def test_comic_create_in_safe():
    data = _parse_frontmatter()
    safe = data["mode"]["tools"]["safe"]
    assert "comic_create" in safe, "comic_create must be in tools.safe"


def test_recipes_in_safe():
    data = _parse_frontmatter()
    safe = data["mode"]["tools"]["safe"]
    assert "recipes" in safe, "recipes must be in tools.safe"


def test_bash_in_safe():
    data = _parse_frontmatter()
    safe = data["mode"]["tools"]["safe"]
    assert "bash" in safe, "bash must be in tools.safe"


def test_full_safe_tools_list():
    """Verify the full safe tools list from the spec."""
    data = _parse_frontmatter()
    safe = data["mode"]["tools"]["safe"]
    expected = [
        "read_file",
        "glob",
        "grep",
        "comic_create",
        "comic_asset",
        "comic_character",
        "comic_style",
        "comic_project",
        "recipes",
        "bash",
        "load_skill",
    ]
    assert set(safe) == set(expected), (
        f"Safe tools mismatch. Expected: {sorted(expected)}, Got: {sorted(safe)}"
    )


# --- AC 8: mode.tools.warn is ['delegate'] ---


def test_warn_tools():
    data = _parse_frontmatter()
    warn = data["mode"]["tools"]["warn"]
    assert warn == ["delegate"], f"Warn tools should be ['delegate'], got {warn}"


# --- Structural checks ---


def test_mode_shortcut():
    data = _parse_frontmatter()
    assert data["mode"]["shortcut"] == "comic-review"


def test_mode_description():
    data = _parse_frontmatter()
    desc = data["mode"]["description"]
    assert (
        "quality" in desc.lower()
        or "review" in desc.lower()
        or "inspect" in desc.lower()
    ), f"Description should mention quality, review, or inspect: {desc}"


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
    assert "delegate" in body.lower(), (
        "CRITICAL section should mention delegate being warn-tier"
    )
    assert "verify" in body.lower() or "YOU" in body, (
        "CRITICAL section should emphasize YOU verify results"
    )


def test_hard_gate_with_5_evidence_requirements():
    body = _get_body()
    assert "<HARD-GATE>" in body, "Missing <HARD-GATE> section"
    # 5 evidence requirements from spec
    body_lower = body.lower()
    assert "panel" in body_lower and "uri" in body_lower, (
        "HARD-GATE must mention panels with URIs"
    )
    assert "review status" in body_lower or "review_status" in body_lower, (
        "HARD-GATE must mention review status"
    )
    assert "flagged" in body_lower, "HARD-GATE must mention flagged assets"
    assert "review_asset" in body, "HARD-GATE must mention review_asset"
    assert "cover" in body_lower, "HARD-GATE must mention cover check"
    assert "html" in body_lower, "HARD-GATE must mention HTML verification"


def test_todo_checklist():
    body = _get_body()
    checklist_items = [
        line for line in body.split("\n") if line.strip().startswith("- [ ]")
    ]
    assert len(checklist_items) >= 7, (
        f"Todo checklist should have >= 7 items, found {len(checklist_items)}"
    )


def test_4_process_phases():
    body = _get_body()
    assert "Inventory" in body, "Missing Inventory phase"
    assert "Quality Inspection" in body or "Quality" in body, (
        "Missing Quality Inspection phase"
    )
    assert "Surgical Retri" in body or "Surgical" in body, (
        "Missing Surgical Retries phase"
    )
    assert "Final Verification" in body, "Missing Final Verification phase"


def test_inventory_phase_uses_comic_project_and_comic_asset():
    body = _get_body()
    assert "comic_project" in body, "Inventory phase must reference comic_project"
    assert "comic_asset" in body, "Inventory phase must reference comic_asset"


def test_quality_inspection_uses_review_asset():
    body = _get_body()
    assert "review_asset" in body, (
        "Quality Inspection phase must reference review_asset"
    )
    assert "comic_create" in body, (
        "Quality Inspection phase must reference comic_create"
    )


def test_surgical_retries_mentions_recipes():
    body = _get_body()
    body_lower = body.lower()
    # Should mention individual panel, issue-retry, and issue-compose recipes
    assert "panel" in body_lower and "retr" in body_lower, (
        "Surgical Retries must mention panel retry"
    )


def test_evidence_before_claims_table():
    body = _get_body()
    assert "Evidence-Before-Claims" in body or "Evidence" in body, (
        "Missing Evidence-Before-Claims table"
    )
    # Find the evidence table and count rows
    in_evidence_table = False
    evidence_rows = []
    for line in body.split("\n"):
        stripped = line.strip()
        if "Evidence" in line and "Claim" in line and "|" in line:
            in_evidence_table = True
            continue
        if in_evidence_table and stripped.startswith("|"):
            if stripped.startswith("|---") or stripped.startswith("| ---"):
                continue
            evidence_rows.append(stripped)
        elif in_evidence_table and not stripped.startswith("|") and stripped:
            break
    assert len(evidence_rows) >= 5, (
        f"Evidence-Before-Claims table should have >= 5 rows, found {len(evidence_rows)}"
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
        and not line.strip().startswith("| Claim")
        and not line.strip().startswith("| Evidence")
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
    assert "comic-review" in body.lower()


def test_transitions_section():
    body = _get_body()
    assert "Transitions" in body, "Missing Transitions section"
    assert "Golden path" in body, "Missing golden path description"
    assert "/comic-publish" in body, "Golden path should mention /comic-publish"
    assert "Back path" in body, "Missing back path description"
    assert "/comic-plan" in body, "Back path should mention /comic-plan"
