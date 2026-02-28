"""Tests for Task 4.1: Recipe improvements for session-to-comic v4.0.0.

Acceptance criteria:
  AC1: Recipe version is 4.0.0
  AC2: generate-panels and generate-cover run in parallel
  AC3: Storyboard approval gate exists between storyboard and character-design
  AC4: Model requirements present in character-design, generate-panels, generate-cover
  AC5: Recipe validates against schema (tested via result-validator separately)
  AC6: Composition step depends on both parallel steps completing
"""

import yaml
from pathlib import Path

RECIPE_PATH = Path(__file__).parent.parent / "recipes" / "session-to-comic.yaml"


def _load_recipe() -> dict:
    """Load and parse the recipe YAML."""
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
    """Find a step by its ID across all stages/steps."""
    for step in _get_all_steps(recipe):
        if step.get("id") == step_id:
            return step
    return None


def _get_stages(recipe: dict) -> list[dict]:
    """Get stages from a staged recipe."""
    return recipe.get("stages", [])


def _find_stage_containing_step(recipe: dict, step_id: str) -> dict | None:
    """Find the stage that contains a specific step."""
    for stage in _get_stages(recipe):
        for step in stage.get("steps", []):
            if step.get("id") == step_id:
                return stage
    return None


def _stage_index_of_step(recipe: dict, step_id: str) -> int:
    """Return the index of the stage containing a step, or -1 if not found."""
    for i, stage in enumerate(_get_stages(recipe)):
        for step in stage.get("steps", []):
            if step.get("id") == step_id:
                return i
    return -1


def _get_step_requirements(recipe: dict, step_id: str) -> dict | None:
    """Extract requirements for a step from recipe-level or step-level sources.

    Requirements may live in:
    1. Top-level context.requirements dict keyed by step name (snake_case of step id)
    2. Direct requirements field on the step
    3. Step-level context.requirements
    """
    # Derive the snake_case key from step id (e.g. "character-design" -> "character_design")
    key = step_id.replace("-", "_")

    # Check top-level context.requirements
    ctx = recipe.get("context", {})
    if isinstance(ctx, dict):
        reqs = ctx.get("requirements", {})
        if isinstance(reqs, dict) and key in reqs:
            return reqs[key]

    # Check step-level fields
    step = _find_step(recipe, step_id)
    if step is None:
        return None
    if "requirements" in step:
        return step["requirements"]
    step_ctx = step.get("context", {})
    if isinstance(step_ctx, dict) and "requirements" in step_ctx:
        return step_ctx["requirements"]
    return None


# ============================================
# AC1: Recipe version is 4.0.0
# ============================================


def test_version_is_4_0_0():
    """Recipe version must be bumped to 4.0.0."""
    recipe = _load_recipe()
    assert recipe["version"] == "4.0.0", (
        f"Expected version 4.0.0, got {recipe['version']}"
    )


# ============================================
# AC2: generate-panels and generate-cover run in parallel
# ============================================


def test_parallel_art_generation():
    """generate-panels and generate-cover must be structured for parallel execution.

    Parallel execution is expressed through the dependency graph (fork-join pattern):
    - Both generate-panels and generate-cover depend on character-design (fork)
    - Neither depends on the other (parallel-eligible)
    - Composition depends on both completing (join)

    The recipe engine uses depends_on to determine which steps can run concurrently.
    """
    recipe = _load_recipe()
    panels = _find_step(recipe, "generate-panels")
    cover = _find_step(recipe, "generate-cover")
    composition = _find_step(recipe, "composition")

    assert panels is not None, "generate-panels step not found"
    assert cover is not None, "generate-cover step not found"
    assert composition is not None, "composition step not found"

    # Both must be in the same stage (can run concurrently)
    panels_stage = _find_stage_containing_step(recipe, "generate-panels")
    cover_stage = _find_stage_containing_step(recipe, "generate-cover")
    assert panels_stage is cover_stage, (
        "generate-panels and generate-cover must be in the same stage"
    )

    # Neither depends on the other (parallel-eligible)
    panels_deps = panels.get("depends_on", [])
    cover_deps = cover.get("depends_on", [])
    assert "generate-cover" not in panels_deps, (
        "generate-panels must not depend on generate-cover"
    )
    assert "generate-panels" not in cover_deps, (
        "generate-cover must not depend on generate-panels"
    )

    # Composition joins both (depends on both)
    comp_deps = composition.get("depends_on", [])
    assert "generate-panels" in comp_deps, "composition must depend on generate-panels"
    assert "generate-cover" in comp_deps, "composition must depend on generate-cover"


# ============================================
# AC3: Storyboard approval gate
# ============================================


def test_uses_staged_mode():
    """Recipe must use staged mode (stages key) for approval gates."""
    recipe = _load_recipe()
    assert "stages" in recipe, "Recipe must use staged mode for approval gates"


def test_storyboard_approval_gate_exists():
    """Approval gate must exist on the stage containing storyboard step."""
    recipe = _load_recipe()
    stage = _find_stage_containing_step(recipe, "storyboard")
    assert stage is not None, "No stage contains the storyboard step"
    approval = stage.get("approval", {})
    assert approval.get("required") is True, (
        "Storyboard stage must have approval.required: true"
    )


def test_approval_prompt_references_storyboard():
    """Approval prompt must reference storyboard output for user review."""
    recipe = _load_recipe()
    stage = _find_stage_containing_step(recipe, "storyboard")
    assert stage is not None
    prompt = stage.get("approval", {}).get("prompt", "")
    assert "storyboard" in prompt.lower(), (
        "Approval prompt must reference storyboard output"
    )


def test_character_design_is_after_storyboard_approval():
    """character-design must be in a stage AFTER the storyboard stage."""
    recipe = _load_recipe()
    sb_idx = _stage_index_of_step(recipe, "storyboard")
    cd_idx = _stage_index_of_step(recipe, "character-design")
    assert sb_idx >= 0, "storyboard step not found in any stage"
    assert cd_idx >= 0, "character-design step not found in any stage"
    assert cd_idx > sb_idx, "character-design must be in a later stage than storyboard"


# ============================================
# AC4: Model requirements in step context
# ============================================


def test_character_design_requirements():
    """character-design: needs_reference_images=false, detail_level=high."""
    recipe = _load_recipe()
    reqs = _get_step_requirements(recipe, "character-design")
    assert reqs is not None, "character-design must have requirements in recipe context"
    assert reqs["needs_reference_images"] is False
    assert reqs["detail_level"] == "high"


def test_generate_panels_requirements():
    """generate-panels: needs_reference_images=true, detail_level=medium."""
    recipe = _load_recipe()
    reqs = _get_step_requirements(recipe, "generate-panels")
    assert reqs is not None, "generate-panels must have requirements in recipe context"
    assert reqs["needs_reference_images"] is True
    assert reqs["detail_level"] == "medium"


def test_generate_cover_requirements():
    """generate-cover: needs_reference_images=true, detail_level=high."""
    recipe = _load_recipe()
    reqs = _get_step_requirements(recipe, "generate-cover")
    assert reqs is not None, "generate-cover must have requirements in recipe context"
    assert reqs["needs_reference_images"] is True
    assert reqs["detail_level"] == "high"


# ============================================
# AC6: Composition depends on both parallel steps
# ============================================


def test_composition_depends_on_both_parallel_steps():
    """Composition step must depend on both generate-panels and generate-cover."""
    recipe = _load_recipe()
    step = _find_step(recipe, "composition")
    assert step is not None, "composition step not found"

    prompt = step.get("prompt", "")
    depends = step.get("depends_on", [])

    # Must reference both outputs via depends_on or prompt variables
    has_panels = "panel_results" in prompt or "generate-panels" in depends
    has_cover = "cover_results" in prompt or "generate-cover" in depends

    assert has_panels, (
        "composition must reference panel_results or depend on generate-panels"
    )
    assert has_cover, (
        "composition must reference cover_results or depend on generate-cover"
    )
