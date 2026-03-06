"""Tests for task-10: Update approval gate for full saga summary.

Validates that the approval gate prompt is saga-aware and displays:
  AC1: Saga title ({{storyboard.title}})
  AC2: Subtitle ({{storyboard.subtitle}})
  AC3: Total issues ({{storyboard.saga_plan.total_issues}})
  AC4: Arc summary ({{storyboard.saga_plan.arc_summary}})
  AC5: Max issues budget ({{max_issues}})
  AC6: Layout validation status ({{storyboard_validation.validation}})
  AC7: All planned issues ({{storyboard.saga_plan.issues}})
  AC8: Full character roster ({{storyboard.character_roster}})
  AC9: Created issues ({{saga_issues}})
  AC10: Instructions: if layout validation FAILED, DENY and fix layouts
  AC11: Instructions: otherwise approve to proceed with character design and per-issue art generation
  AC12: timeout: 0, default: deny
  AC13: Old single-issue fields (panel_count, page_count, panel_list, page_layouts,
        character_list, storyboard.saga_plan as raw dump) are NOT in the prompt
"""

import functools
import pathlib

import yaml

RECIPE_PATH = pathlib.Path(__file__).parent.parent / "recipes" / "session-to-comic.yaml"


@functools.cache
def _load_recipe() -> dict:
    """Load and cache the session-to-comic recipe YAML."""
    return yaml.safe_load(RECIPE_PATH.read_text())


def _get_approval() -> dict:
    """Get the approval gate from the first stage."""
    recipe = _load_recipe()
    first_stage = recipe["stages"][0]
    return first_stage["approval"]


def _get_approval_prompt() -> str:
    """Get the approval gate prompt text."""
    return _get_approval().get("prompt", "")


# ---------------------------------------------------------------
# Test 1: Approval gate has required: true
# ---------------------------------------------------------------
def test_approval_gate_required():
    """Approval gate must be required."""
    approval = _get_approval()
    assert approval.get("required") is True, "Approval gate must have required: true"


# ---------------------------------------------------------------
# Test 2: timeout is 0, default is deny
# ---------------------------------------------------------------
def test_approval_gate_timeout_and_default():
    """Approval gate must have timeout: 0 and default: deny."""
    approval = _get_approval()
    assert approval.get("timeout") == 0, (
        f"Expected timeout: 0, got {approval.get('timeout')}"
    )
    assert approval.get("default") == "deny", (
        f"Expected default: deny, got {approval.get('default')}"
    )


# ---------------------------------------------------------------
# Test 3: Prompt contains saga title
# ---------------------------------------------------------------
def test_prompt_contains_saga_title():
    """Prompt must display {{storyboard.title}}."""
    prompt = _get_approval_prompt()
    assert "{{storyboard.title}}" in prompt, "Prompt must contain {{storyboard.title}}"


# ---------------------------------------------------------------
# Test 4: Prompt contains subtitle
# ---------------------------------------------------------------
def test_prompt_contains_subtitle():
    """Prompt must display {{storyboard.subtitle}}."""
    prompt = _get_approval_prompt()
    assert "{{storyboard.subtitle}}" in prompt, (
        "Prompt must contain {{storyboard.subtitle}}"
    )


# ---------------------------------------------------------------
# Test 5: Prompt contains total issues count
# ---------------------------------------------------------------
def test_prompt_contains_total_issues():
    """Prompt must display {{storyboard.saga_plan.total_issues}}."""
    prompt = _get_approval_prompt()
    assert "{{storyboard.saga_plan.total_issues}}" in prompt, (
        "Prompt must contain {{storyboard.saga_plan.total_issues}}"
    )


# ---------------------------------------------------------------
# Test 6: Prompt contains arc summary
# ---------------------------------------------------------------
def test_prompt_contains_arc_summary():
    """Prompt must display {{storyboard.saga_plan.arc_summary}}."""
    prompt = _get_approval_prompt()
    assert "{{storyboard.saga_plan.arc_summary}}" in prompt, (
        "Prompt must contain {{storyboard.saga_plan.arc_summary}}"
    )


# ---------------------------------------------------------------
# Test 7: Prompt contains max issues budget
# ---------------------------------------------------------------
def test_prompt_contains_max_issues():
    """Prompt must display {{max_issues}}."""
    prompt = _get_approval_prompt()
    assert "{{max_issues}}" in prompt, "Prompt must contain {{max_issues}}"


# ---------------------------------------------------------------
# Test 8: Prompt contains layout validation status
# ---------------------------------------------------------------
def test_prompt_contains_validation_status():
    """Prompt must display {{storyboard_validation.validation}}."""
    prompt = _get_approval_prompt()
    assert "{{storyboard_validation.validation}}" in prompt, (
        "Prompt must contain {{storyboard_validation.validation}}"
    )


# ---------------------------------------------------------------
# Test 9: Prompt contains all planned issues
# ---------------------------------------------------------------
def test_prompt_contains_planned_issues():
    """Prompt must display {{storyboard.saga_plan.issues}}."""
    prompt = _get_approval_prompt()
    assert "{{storyboard.saga_plan.issues}}" in prompt, (
        "Prompt must contain {{storyboard.saga_plan.issues}}"
    )


# ---------------------------------------------------------------
# Test 10: Prompt contains full character roster
# ---------------------------------------------------------------
def test_prompt_contains_character_roster():
    """Prompt must display {{storyboard.character_roster}}."""
    prompt = _get_approval_prompt()
    assert "{{storyboard.character_roster}}" in prompt, (
        "Prompt must contain {{storyboard.character_roster}}"
    )


# ---------------------------------------------------------------
# Test 11: Prompt contains created saga issues
# ---------------------------------------------------------------
def test_prompt_contains_saga_issues():
    """Prompt must display {{saga_issues}}."""
    prompt = _get_approval_prompt()
    assert "{{saga_issues}}" in prompt, "Prompt must contain {{saga_issues}}"


# ---------------------------------------------------------------
# Test 12: Prompt has DENY instruction for failed validation
# ---------------------------------------------------------------
def test_prompt_deny_instruction_for_failed_validation():
    """Prompt must instruct to DENY if layout validation FAILED."""
    prompt = _get_approval_prompt().lower()
    assert "failed" in prompt, "Prompt must mention FAILED validation"
    assert "deny" in prompt, "Prompt must instruct to DENY"
    # Must mention fixing layouts
    assert "layout" in prompt, "Prompt must mention fixing layouts"


# ---------------------------------------------------------------
# Test 13: Prompt has approve instruction for character design and per-issue art
# ---------------------------------------------------------------
def test_prompt_approve_instruction():
    """Prompt must instruct to approve for character design and per-issue art generation."""
    prompt = _get_approval_prompt().lower()
    assert "character design" in prompt, "Prompt must mention character design"
    assert "per-issue" in prompt or "per issue" in prompt, (
        "Prompt must mention per-issue art generation"
    )


# ---------------------------------------------------------------
# Test 14: Old single-issue fields are NOT in the prompt
# ---------------------------------------------------------------
def test_old_single_issue_fields_removed():
    """Old single-issue fields must not appear in the saga-aware prompt.

    The old prompt had: panel_count, page_count, character_list, panel_list,
    page_layouts as direct storyboard fields. The saga prompt should use
    saga_plan.issues and character_roster instead.
    """
    prompt = _get_approval_prompt()
    # Old fields that should not be in the saga-aware prompt
    assert "{{storyboard.panel_count}}" not in prompt, (
        "Old field {{storyboard.panel_count}} should be removed from saga prompt"
    )
    assert "{{storyboard.page_count}}" not in prompt, (
        "Old field {{storyboard.page_count}} should be removed from saga prompt"
    )
    assert "{{storyboard.character_list}}" not in prompt, (
        "Old field {{storyboard.character_list}} should be replaced by {{storyboard.character_roster}}"
    )
    assert "{{storyboard.panel_list}}" not in prompt, (
        "Old field {{storyboard.panel_list}} should be removed from saga prompt"
    )
    assert "{{storyboard.page_layouts}}" not in prompt, (
        "Old field {{storyboard.page_layouts}} should be removed from saga prompt"
    )
