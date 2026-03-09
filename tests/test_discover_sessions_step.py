"""Tests for the discover-sessions step (Step 0a) in session-to-comic.yaml.

Validates that:
1. discover-sessions step exists in the recipe
2. It appears between init-project and research steps (in order)
3. It uses agent stories:story-researcher
4. It has output "session_data"
5. It has timeout 600
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


def _step_ids(recipe: dict) -> list[str]:
    """Return ordered list of step IDs."""
    return [s.get("id", "") for s in _get_all_steps(recipe)]


def _find_step(recipe: dict, step_id: str) -> dict | None:
    for step in _get_all_steps(recipe):
        if step.get("id") == step_id:
            return step
    return None


def test_discover_sessions_step_exists():
    """discover-sessions step must exist in the recipe."""
    recipe = _load_recipe()
    step = _find_step(recipe, "discover-sessions")
    assert step is not None, "Step 'discover-sessions' not found in recipe"


def test_step_order_init_discover_research():
    """Steps must appear in order: init-project, discover-sessions, research."""
    recipe = _load_recipe()
    ids = _step_ids(recipe)
    assert "init-project" in ids, "init-project step not found"
    assert "discover-sessions" in ids, "discover-sessions step not found"
    assert "research" in ids, "research step not found"

    idx_init = ids.index("init-project")
    idx_discover = ids.index("discover-sessions")
    idx_research = ids.index("research")

    assert idx_init < idx_discover < idx_research, (
        f"Expected order init-project({idx_init}) < discover-sessions({idx_discover}) < research({idx_research})"
    )


def test_discover_sessions_agent():
    """discover-sessions must use agent stories:story-researcher."""
    recipe = _load_recipe()
    step = _find_step(recipe, "discover-sessions")
    assert step is not None, "Step not found"
    assert step.get("agent") == "stories:story-researcher", (
        f"Expected agent 'stories:story-researcher', got {step.get('agent')!r}"
    )


def test_discover_sessions_output():
    """discover-sessions must have output 'session_data'."""
    recipe = _load_recipe()
    step = _find_step(recipe, "discover-sessions")
    assert step is not None, "Step not found"
    assert step.get("output") == "session_data", (
        f"Expected output 'session_data', got {step.get('output')!r}"
    )


def test_discover_sessions_timeout():
    """discover-sessions must have timeout 600."""
    recipe = _load_recipe()
    step = _find_step(recipe, "discover-sessions")
    assert step is not None, "Step not found"
    assert step.get("timeout") == 600, (
        f"Expected timeout 600, got {step.get('timeout')!r}"
    )
