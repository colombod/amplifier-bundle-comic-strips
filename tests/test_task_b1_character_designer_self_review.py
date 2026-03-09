"""Tests for Task B1: Character-Designer Self-Review Loop.

Validates that character-designer.md includes a Step 2.5 self-review loop
with vision inspection, matching the panel-artist pattern.

Acceptance criteria:
1. review_asset appears at least 2 times in the file
2. YAML frontmatter still parses (meta.name: character-designer)
3. Step 2.5 section exists between Step 2 and Step 3
4. Self-review includes 5-point quality checklist
5. Maximum 3 attempts documented
6. Specific remediation prompts for face, text, and format failures
7. Git diff shows only Step 2.5 added (verified manually)
8. Verification script B1 check passes (review_asset in file)
9. Commit message matches spec (verified at commit time)
"""

import re
from pathlib import Path

import yaml


AGENT_PATH = Path(__file__).parent.parent / "agents" / "character-designer.md"


def _read_agent() -> str:
    return AGENT_PATH.read_text()


def _parse_frontmatter(content: str) -> dict:
    """Extract and parse YAML frontmatter from markdown."""
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    assert match, "No YAML frontmatter found"
    return yaml.safe_load(match.group(1))


# ---------------------------------------------------------------
# AC 1: review_asset appears at least 2 times
# ---------------------------------------------------------------
def test_review_asset_appears_at_least_twice() -> None:
    """character-designer.md must contain 'review_asset' at least 2 times."""
    content = _read_agent()
    count = content.count("review_asset")
    assert count >= 2, (
        f"Expected at least 2 occurrences of 'review_asset', found {count}"
    )


# ---------------------------------------------------------------
# AC 2: YAML frontmatter parses correctly
# ---------------------------------------------------------------
def test_yaml_frontmatter_parses() -> None:
    """YAML frontmatter must parse and contain meta.name: character-designer."""
    content = _read_agent()
    fm = _parse_frontmatter(content)
    assert fm.get("meta", {}).get("name") == "character-designer", (
        f"Expected meta.name='character-designer', got {fm.get('meta', {}).get('name')}"
    )


# ---------------------------------------------------------------
# AC 3: Step 2.5 exists between Step 2 and Step 3
# ---------------------------------------------------------------
def test_step_2_5_exists() -> None:
    """A 'Step 2.5' section must exist in the agent instructions."""
    content = _read_agent()
    assert "Step 2.5" in content, "Missing 'Step 2.5' section"


def test_step_2_5_between_step_2_and_step_3() -> None:
    """Step 2.5 must appear after Step 2 heading and before Step 3 heading."""
    content = _read_agent()
    step2_pos = content.find("### Step 2:")
    step25_pos = content.find("Step 2.5")
    step3_pos = content.find("### Step 3:")
    assert step2_pos != -1, "Step 2 heading not found"
    assert step25_pos != -1, "Step 2.5 section not found"
    assert step3_pos != -1, "Step 3 heading not found"
    assert step2_pos < step25_pos < step3_pos, (
        f"Step 2.5 (pos {step25_pos}) must be between "
        f"Step 2 (pos {step2_pos}) and Step 3 (pos {step3_pos})"
    )


# ---------------------------------------------------------------
# AC 4: 5-point quality checklist
# ---------------------------------------------------------------
def test_five_point_quality_checklist() -> None:
    """Self-review must include all 5 quality checklist items."""
    content = _read_agent()
    checklist_items = [
        "Face clearly visible",
        "No baked-in text",
        "Style cohesion",
        "Reference-sheet format",
        "Distinctive features present",
    ]
    for item in checklist_items:
        assert item.lower() in content.lower(), f"Missing checklist item: '{item}'"


# ---------------------------------------------------------------
# AC 5: Maximum 3 attempts documented
# ---------------------------------------------------------------
def test_maximum_3_attempts() -> None:
    """Self-review must document a maximum of 3 attempts."""
    content = _read_agent()
    assert "3 attempts" in content.lower() or "three attempts" in content.lower(), (
        "Missing documentation of maximum 3 attempts"
    )


# ---------------------------------------------------------------
# AC 6: Specific remediation prompts for face, text, format
# ---------------------------------------------------------------
def test_remediation_for_face_failure() -> None:
    """Remediation text for face visibility failure must exist."""
    content = _read_agent()
    assert (
        "face" in content.lower()
        and "remediat" in content.lower()
        or ("face clearly visible" in content.lower() and "adjust" in content.lower())
    ), "Missing specific remediation for face visibility failure"


def test_remediation_for_text_failure() -> None:
    """Remediation text for baked-in text failure must exist."""
    content = _read_agent()
    # Must have remediation language about text artifacts
    assert "text" in content.lower() and (
        "no text" in content.lower() or "no words" in content.lower()
    ), "Missing specific remediation for baked-in text failure"


def test_remediation_for_format_failure() -> None:
    """Remediation text for reference-sheet format failure must exist."""
    content = _read_agent()
    # Must mention remediation for format issues (full body, neutral pose, plain background)
    assert "full body" in content.lower() and "neutral pose" in content.lower(), (
        "Missing specific remediation for reference-sheet format failure"
    )


# ---------------------------------------------------------------
# AC 8: review_asset in file (verification script B1 equivalent)
# ---------------------------------------------------------------
def test_verification_b1_review_asset_in_file() -> None:
    """Verification script B1: character-designer.md contains review_asset."""
    content = _read_agent()
    assert "review_asset" in content, (
        "Verification B1 FAILED: 'review_asset' not found in character-designer.md"
    )


# ---------------------------------------------------------------
# Additional: review_asset prompt includes reference-sheet note
# ---------------------------------------------------------------
def test_review_asset_prompt_includes_reference_sheet_note() -> None:
    """The review_asset call prompt must include the note about judging as character design document."""
    content = _read_agent()
    assert "character design document" in content.lower(), (
        "review_asset prompt must include note: "
        "'this is a reference sheet, not a panel — judge it as a character design document'"
    )


# ---------------------------------------------------------------
# Additional: best result + warning for comic-review on all 3 fails
# ---------------------------------------------------------------
def test_fallback_on_all_failures() -> None:
    """If all 3 attempts fail, use best result and log warning for /comic-review."""
    content = _read_agent()
    assert "best result" in content.lower(), (
        "Must document using best result when all 3 attempts fail"
    )
    assert "comic-review" in content.lower(), (
        "Must mention logging warning for /comic-review when all attempts fail"
    )
