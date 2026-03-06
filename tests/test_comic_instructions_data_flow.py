"""Tests for comic-instructions.md Cross-Agent Data Flow section (v8.0.0 saga pipeline).

Validates that the Cross-Agent Data Flow section describes the v8.0.0
3-stage saga pipeline, not the old v7.7.0 linear 7-stage pipeline.
"""

from pathlib import Path

MD_FILE = Path(__file__).resolve().parent.parent / "context" / "comic-instructions.md"


def _read_md() -> str:
    return MD_FILE.read_text()


# --- Old content must be gone ---


def test_old_seven_stages_intro_removed():
    content = _read_md()
    assert "seven stages" not in content, (
        "Old intro 'seven stages' should be replaced with v8.0.0 description"
    )


def test_old_v770_marker_removed():
    content = _read_md()
    assert "*(new in v7.7.0)*" not in content, "Old v7.7.0 marker should be removed"


# --- New 3-stage saga structure ---


def test_section_header_exists():
    content = _read_md()
    assert "## Cross-Agent Data Flow" in content


def test_three_stage_headings_present():
    content = _read_md()
    assert "Stage 1" in content, "Stage 1 heading must exist"
    assert "Stage 2" in content, "Stage 2 heading must exist"
    assert "Stage 3" in content, "Stage 3 heading must exist"
    assert "Saga Planning" in content, "Stage 1 must be named Saga Planning"
    assert "Character Design" in content, "Stage 2 must be named Character Design"
    assert "Per-Issue Art Generation" in content, (
        "Stage 3 must be named Per-Issue Art Generation"
    )


# --- Stage 1: Saga Planning steps ---


def test_stage1_session_discovery():
    content = _read_md()
    assert "Session Discovery" in content
    assert "flexible" in content.lower()
    assert "source" in content


def test_stage1_research():
    content = _read_md()
    assert "asset URI" in content or "asset uri" in content.lower()


def test_stage1_style_curation():
    content = _read_md()
    assert "Style Curation" in content or "style-curator" in content


def test_stage1_saga_storyboard():
    content = _read_md()
    assert "Saga Storyboard" in content
    assert "issues[]" in content or "issues array" in content.lower()
    assert "character_roster" in content


def test_stage1_layout_validation():
    content = _read_md()
    assert "Layout Validation" in content


def test_stage1_issue_creation():
    content = _read_md()
    assert "Issue Creation" in content or "issue-001" in content


def test_stage1_approval_gate():
    content = _read_md()
    # Approval gate must be mentioned in stage 1
    assert "APPROVAL GATE" in content or "approval gate" in content.lower()


# --- Stage 2: Character Design ---


def test_stage2_character_design():
    content = _read_md()
    assert "Character Design" in content
    assert "cross-project" in content.lower() or "cross project" in content.lower()
    assert "evolution" in content.lower()


def test_stage2_per_issue_variants():
    content = _read_md()
    # Should mention per-issue variant creation
    assert "variant" in content.lower()


# --- Stage 3: Per-Issue Art Generation ---


def test_stage3_panel_art():
    content = _read_md()
    assert "panel art" in content.lower() or "panel" in content


def test_stage3_cover_art():
    content = _read_md()
    assert "cover art" in content.lower() or "cover" in content


def test_stage3_composition():
    content = _read_md()
    # Should mention recap page and cliffhanger
    assert "recap" in content.lower()
    assert "cliffhanger" in content.lower()


def test_stage3_assemble_comic():
    content = _read_md()
    assert "assemble_comic" in content


def test_stage3_separate_html_per_issue():
    content = _read_md()
    assert "separate HTML" in content or "HTML per issue" in content


# --- Scoping note ---


def test_scoping_note_present():
    """Characters and styles are project-scoped; panels etc. are issue-scoped."""
    content = _read_md()
    assert "project-scoped" in content
    assert "issue-scoped" in content
