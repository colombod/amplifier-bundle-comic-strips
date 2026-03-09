"""Tests for task-8: Update validate-storyboard for all saga issues.

Validates that the validate-storyboard step validates layouts across ALL
issues in the saga plan, not just a single page_layouts array.

Acceptance criteria:
  AC1: Step id="validate-storyboard" exists with agent="comic-strips:style-curator"
  AC2: output="storyboard_validation", parse_json=true, timeout=120
  AC3: Prompt references {{storyboard.saga_plan.issues}} to iterate all issues
  AC4: Prompt extracts page_layouts from each issue
  AC5: Validates ALL layouts via comic_create(action='validate_storyboard', page_layouts=<combined>)
  AC6: Success returns {"validation": "PASSED", "total_issues": <count>, "total_pages": <sum>}
  AC7: Failure returns {"validation": "FAILED", "invalid_layout_ids": ..., "suggestions": ..., "failed_issues": ...}
  AC8: Does NOT reference old {{storyboard.page_layouts}} (single-issue pattern)
"""

import pytest
import functools
import pathlib

import yaml

pytestmark = pytest.mark.skip(reason="legacy test for pre-v9 recipe")

RECIPE_PATH = pathlib.Path(__file__).parent.parent / "recipes" / "session-to-comic.yaml"


@functools.cache
def _load_recipe() -> dict:
    return yaml.safe_load(RECIPE_PATH.read_text())


def _get_all_steps(recipe: dict) -> list[dict]:
    """Get all steps from recipe (handles both flat and staged modes)."""
    if "steps" in recipe:
        return recipe["steps"]
    elif "stages" in recipe:
        steps = []
        for stage in recipe["stages"]:
            steps.extend(stage.get("steps", []))
        return steps
    return []


def _find_step(recipe: dict, step_id: str) -> dict | None:
    for step in _get_all_steps(recipe):
        if step.get("id") == step_id:
            return step
    return None


def _validate_step() -> dict:
    recipe = _load_recipe()
    step = _find_step(recipe, "validate-storyboard")
    assert step is not None, "validate-storyboard step not found in recipe"
    return step


def _validate_prompt() -> str:
    return _validate_step().get("prompt", "")


# =============================================================================
# AC1: STEP BASICS — agent
# =============================================================================


class TestValidateStepBasics:
    """AC1: Step exists with correct agent."""

    def test_step_exists(self):
        """validate-storyboard step must exist in the recipe."""
        step = _validate_step()
        assert step["id"] == "validate-storyboard"

    def test_agent_is_style_curator(self):
        """AC1: Uses comic-strips:style-curator agent."""
        step = _validate_step()
        assert step["agent"] == "comic-strips:style-curator"


# =============================================================================
# AC2: STEP CONFIG — output, parse_json, timeout
# =============================================================================


class TestValidateStepConfig:
    """AC2: output, parse_json, timeout are set correctly."""

    def test_output_is_storyboard_validation(self):
        """AC2: output field is 'storyboard_validation'."""
        step = _validate_step()
        assert step["output"] == "storyboard_validation"

    def test_parse_json_is_true(self):
        """AC2: parse_json is true."""
        step = _validate_step()
        assert step.get("parse_json") is True

    def test_timeout_is_120(self):
        """AC2: timeout is 120."""
        step = _validate_step()
        assert step.get("timeout") == 120


# =============================================================================
# AC3: PROMPT REFERENCES saga_plan.issues
# =============================================================================


class TestSagaIssuesReference:
    """AC3: Prompt references {{storyboard.saga_plan.issues}} for all issues."""

    def test_references_saga_plan_issues(self):
        """Prompt must reference {{storyboard.saga_plan.issues}}."""
        prompt = _validate_prompt()
        assert "{{storyboard.saga_plan.issues}}" in prompt


# =============================================================================
# AC4: EXTRACTS page_layouts FROM EACH ISSUE
# =============================================================================


class TestExtractsPageLayouts:
    """AC4: Prompt instructs extraction of page_layouts from each issue."""

    def test_mentions_page_layouts_extraction(self):
        """Prompt must mention extracting page_layouts from issues."""
        prompt = _validate_prompt()
        assert "page_layouts" in prompt


# =============================================================================
# AC5: VALIDATES VIA comic_create validate_storyboard
# =============================================================================


class TestValidateStoryboardCall:
    """AC5: Validates ALL layouts via comic_create(action='validate_storyboard')."""

    def test_calls_validate_storyboard(self):
        """Prompt must call comic_create with validate_storyboard action."""
        prompt = _validate_prompt()
        assert "comic_create" in prompt
        assert "validate_storyboard" in prompt


# =============================================================================
# AC6: SUCCESS RESPONSE — total_issues + total_pages
# =============================================================================


class TestSuccessResponse:
    """AC6: Success returns PASSED with total_issues and total_pages."""

    def test_success_includes_total_issues(self):
        """Success response must include total_issues."""
        prompt = _validate_prompt()
        assert "total_issues" in prompt

    def test_success_includes_total_pages(self):
        """Success response must include total_pages."""
        prompt = _validate_prompt()
        assert "total_pages" in prompt


# =============================================================================
# AC7: FAILURE RESPONSE — invalid_layout_ids, suggestions, failed_issues
# =============================================================================


class TestFailureResponse:
    """AC7: Failure returns FAILED with details."""

    def test_failure_includes_invalid_layout_ids(self):
        """Failure response must include invalid_layout_ids."""
        prompt = _validate_prompt()
        assert "invalid_layout_ids" in prompt

    def test_failure_includes_suggestions(self):
        """Failure response must include suggestions."""
        prompt = _validate_prompt()
        assert "suggestions" in prompt

    def test_failure_includes_failed_issues(self):
        """Failure response must include failed_issues."""
        prompt = _validate_prompt()
        assert "failed_issues" in prompt


# =============================================================================
# AC8: NO OLD SINGLE-ISSUE PATTERN
# =============================================================================


class TestNoOldPattern:
    """AC8: Prompt does NOT use old {{storyboard.page_layouts}} pattern."""

    def test_no_old_page_layouts_reference(self):
        """Prompt must NOT reference {{storyboard.page_layouts}} (old single-issue)."""
        prompt = _validate_prompt()
        assert "{{storyboard.page_layouts}}" not in prompt
