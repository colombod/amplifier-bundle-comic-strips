"""Tests for Step 3b: create-issues foreach step (Task 9).

Validates that the create-issues step in session-to-comic.yaml:
1. Exists with id 'create-issues' (replaces old 'update-issue-title')
2. Is a foreach over {{storyboard.saga_plan.issues}} with as: saga_issue
3. Uses comic-strips:style-curator agent
4. Has max_iterations: 20 and timeout: 120
5. Prompt handles issue #1 (update_issue) and issues #2+ (create_issue)
6. Collects results to saga_issues
7. Old update-issue-title step no longer exists
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


def test_old_update_issue_title_step_removed():
    """The old update-issue-title step must no longer exist."""
    recipe = _load_recipe()
    step = _find_step(recipe, "update-issue-title")
    assert step is None, (
        "Old 'update-issue-title' step must be removed — replaced by 'create-issues'"
    )


def test_create_issues_step_exists():
    """The create-issues step must exist in the recipe."""
    recipe = _load_recipe()
    step = _find_step(recipe, "create-issues")
    assert step is not None, "Step 'create-issues' not found in recipe"


def test_create_issues_foreach_source():
    """create-issues must foreach over {{storyboard.saga_plan.issues}}."""
    recipe = _load_recipe()
    step = _find_step(recipe, "create-issues")
    assert step is not None, "Step 'create-issues' not found"
    foreach_val = step.get("foreach", "")
    assert "storyboard.saga_plan.issues" in foreach_val, (
        f"foreach must reference storyboard.saga_plan.issues, got: {foreach_val}"
    )


def test_create_issues_as_variable():
    """create-issues must use 'as: saga_issue'."""
    recipe = _load_recipe()
    step = _find_step(recipe, "create-issues")
    assert step is not None, "Step 'create-issues' not found"
    assert step.get("as") == "saga_issue", (
        f"'as' must be 'saga_issue', got: {step.get('as')}"
    )


def test_create_issues_agent():
    """create-issues must use comic-strips:style-curator agent."""
    recipe = _load_recipe()
    step = _find_step(recipe, "create-issues")
    assert step is not None, "Step 'create-issues' not found"
    assert step.get("agent") == "comic-strips:style-curator", (
        f"Agent must be 'comic-strips:style-curator', got: {step.get('agent')}"
    )


def test_create_issues_max_iterations():
    """create-issues must have max_iterations: 20."""
    recipe = _load_recipe()
    step = _find_step(recipe, "create-issues")
    assert step is not None, "Step 'create-issues' not found"
    assert step.get("max_iterations") == 20, (
        f"max_iterations must be 20, got: {step.get('max_iterations')}"
    )


def test_create_issues_timeout():
    """create-issues must have timeout: 120."""
    recipe = _load_recipe()
    step = _find_step(recipe, "create-issues")
    assert step is not None, "Step 'create-issues' not found"
    assert step.get("timeout") == 120, (
        f"timeout must be 120, got: {step.get('timeout')}"
    )


def test_create_issues_collects_to_saga_issues():
    """create-issues must collect results to 'saga_issues'."""
    recipe = _load_recipe()
    step = _find_step(recipe, "create-issues")
    assert step is not None, "Step 'create-issues' not found"
    assert step.get("collect") == "saga_issues", (
        f"collect must be 'saga_issues', got: {step.get('collect')}"
    )


def test_create_issues_prompt_updates_first_issue():
    """Prompt must handle issue #1 by updating the existing issue."""
    recipe = _load_recipe()
    step = _find_step(recipe, "create-issues")
    assert step is not None, "Step 'create-issues' not found"
    prompt = step.get("prompt", "")
    assert "update_issue" in prompt, (
        "Prompt must reference update_issue action for issue #1"
    )


def test_create_issues_prompt_creates_subsequent_issues():
    """Prompt must handle issues #2+ by creating new issues."""
    recipe = _load_recipe()
    step = _find_step(recipe, "create-issues")
    assert step is not None, "Step 'create-issues' not found"
    prompt = step.get("prompt", "")
    assert "create_issue" in prompt, (
        "Prompt must reference create_issue action for issues #2+"
    )


def test_create_issues_prompt_returns_json():
    """Prompt must instruct agent to return JSON with issue_id, issue_number, title."""
    recipe = _load_recipe()
    step = _find_step(recipe, "create-issues")
    assert step is not None, "Step 'create-issues' not found"
    prompt = step.get("prompt", "")
    assert "issue_id" in prompt, "Prompt must mention issue_id in return JSON"
    assert "issue_number" in prompt, "Prompt must mention issue_number in return JSON"
    assert "title" in prompt, "Prompt must mention title in return JSON"


def test_create_issues_parse_json():
    """create-issues must have parse_json: true for JSON output."""
    recipe = _load_recipe()
    step = _find_step(recipe, "create-issues")
    assert step is not None, "Step 'create-issues' not found"
    assert step.get("parse_json") is True, (
        f"parse_json must be true, got: {step.get('parse_json')}"
    )
