"""Test B5: Verify model_role: fast annotations on mechanical saga-plan steps."""

import yaml
from pathlib import Path

RECIPE_PATH = Path(__file__).parent.parent / "recipes" / "saga-plan.yaml"

# Exactly these 7 mechanical steps MUST have model_role: fast
FAST_STEPS = [
    "check-existing",
    "init-project",
    "lookup-existing-characters",
    "store-storyboard",
    "validate-storyboard",
    "create-issues",
    "prepare-review",
]

# Exactly these 4 creative/research steps must NOT have model_role
CREATIVE_STEPS = [
    "discover-sessions",
    "research",
    "style-curation",
    "storyboard",
]

TOTAL_STEPS = 11  # 7 mechanical + 4 creative


def _load_steps():
    """Load and return all steps from the saga-plan recipe."""
    with open(RECIPE_PATH) as f:
        recipe = yaml.safe_load(f)
    steps = recipe["stages"][0]["steps"]
    return steps


def test_yaml_parses():
    """AC1: recipes/saga-plan.yaml still parses as valid YAML."""
    with open(RECIPE_PATH) as f:
        recipe = yaml.safe_load(f)
    assert recipe is not None
    assert "stages" in recipe


def test_step_count_unchanged():
    """AC2: Step count unchanged (no steps lost or added)."""
    steps = _load_steps()
    assert len(steps) == TOTAL_STEPS, f"Expected {TOTAL_STEPS} steps, got {len(steps)}"


def test_mechanical_steps_have_model_role_fast():
    """AC3: Exactly 7 steps have model_role: fast."""
    steps = _load_steps()
    steps_with_fast = [s["id"] for s in steps if s.get("model_role") == "fast"]
    assert sorted(steps_with_fast) == sorted(FAST_STEPS), (
        f"Expected fast steps {sorted(FAST_STEPS)}, got {sorted(steps_with_fast)}"
    )


def test_creative_steps_have_no_model_role():
    """AC4: Exactly 4 steps have NO model_role."""
    steps = _load_steps()
    steps_without_role = [s["id"] for s in steps if "model_role" not in s]
    assert sorted(steps_without_role) == sorted(CREATIVE_STEPS), (
        f"Expected creative steps {sorted(CREATIVE_STEPS)}, got {sorted(steps_without_role)}"
    )


def test_no_unexpected_model_roles():
    """No step should have a model_role other than 'fast'."""
    steps = _load_steps()
    for step in steps:
        role = step.get("model_role")
        if role is not None:
            assert role == "fast", (
                f"Step '{step['id']}' has unexpected model_role '{role}'"
            )


def test_model_role_count_totals():
    """7 with model_role + 4 without = 11 total."""
    steps = _load_steps()
    with_role = [s for s in steps if "model_role" in s]
    without_role = [s for s in steps if "model_role" not in s]
    assert len(with_role) == 7, (
        f"Expected 7 steps with model_role, got {len(with_role)}"
    )
    assert len(without_role) == 4, (
        f"Expected 4 steps without model_role, got {len(without_role)}"
    )
