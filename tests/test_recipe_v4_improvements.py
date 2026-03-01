"""Tests for recipe improvements for session-to-comic.
Updated for v5: foreach loop structure validation added.

Acceptance criteria verified:
  AC1: Recipe version is 5.0.0 or later
  AC2: generate-panels and generate-cover run in parallel
  AC3: Storyboard approval gate exists between storyboard and character-design
  AC4: Model requirements present in character-design, generate-panels, generate-cover
  AC5: Recipe validates against schema (tested via result-validator separately)
  AC6: Composition step depends on both parallel steps completing
"""

import functools

import yaml
from pathlib import Path

RECIPE_PATH = Path(__file__).parent.parent / "recipes" / "session-to-comic.yaml"


@functools.cache
def _load_recipe() -> dict:
    """Load and parse the recipe YAML once (cached across all callers)."""
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


def _parse_flat_requirements(flat_str: str) -> dict:
    """Parse a flat requirements string like 'needs_reference_images=true, detail_level=high'.

    Returns a dict with typed values: 'true'/'false' become bools, rest stay as strings.
    """
    result = {}
    for pair in flat_str.split(","):
        pair = pair.strip()
        if "=" not in pair:
            continue
        k, v = pair.split("=", 1)
        k, v = k.strip(), v.strip()
        if v.lower() == "true":
            result[k] = True
        elif v.lower() == "false":
            result[k] = False
        else:
            result[k] = v
    return result


def _get_step_requirements(recipe: dict, step_id: str) -> dict | None:
    """Extract requirements for a step from recipe-level or step-level sources.

    Requirements may live in:
    1. Top-level context flat string: '{step_key}_requirements' (v4.0.3+ flat format)
    2. Top-level context.requirements nested dict keyed by snake_case of step id (v4.0.0)
    3. Direct requirements field on the step
    4. Step-level context.requirements

    This multi-location search is intentional: the recipe format allows authors
    to place requirements at any of these levels for flexibility.
    """
    # Derive the snake_case key from step id (e.g. "character-design" -> "character_design")
    key = step_id.replace("-", "_")

    ctx = recipe.get("context", {})
    if isinstance(ctx, dict):
        # v4.0.3+ flat string format: '{key}_requirements' at top-level context
        flat_key = f"{key}_requirements"
        if flat_key in ctx:
            val = ctx[flat_key]
            if isinstance(val, str):
                return _parse_flat_requirements(val)
            if isinstance(val, dict):
                return val

        # v4.0.0 nested dict format: context.requirements.{key}
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
# AC1: Recipe version is 5.0.0 or later
# ============================================


def test_version_is_5_or_later():
    """Recipe version must be 5 or later (v5 introduced foreach loops)."""
    recipe = _load_recipe()
    parts = recipe["version"].split(".")
    major = int(parts[0])
    assert major >= 5, f"Expected major version >= 5, got {recipe['version']}"


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


def test_character_foreach_is_after_storyboard_approval():
    """Character design/foreach step must be in a stage AFTER the storyboard stage."""
    recipe = _load_recipe()
    sb_idx = _stage_index_of_step(recipe, "storyboard")
    assert sb_idx >= 0, "storyboard step not found in any stage"

    # Try known step IDs for character design (v4: character-design, v5: design-characters)
    cd_idx = _stage_index_of_step(recipe, "character-design")
    if cd_idx < 0:
        cd_idx = _stage_index_of_step(recipe, "design-characters")

    # Fallback: scan all stages for a foreach step with 'character' in foreach value
    if cd_idx < 0:
        for i, stage in enumerate(_get_stages(recipe)):
            for step in stage.get("steps", []):
                foreach_val = step.get("foreach", "")
                if "character" in foreach_val:
                    cd_idx = i
                    break
            if cd_idx >= 0:
                break

    assert cd_idx >= 0, "character design step (or foreach) not found in any stage"
    assert cd_idx > sb_idx, "character design must be in a later stage than storyboard"


# ============================================
# AC4: Model requirements in step context
# ============================================


def test_character_design_requirements():
    """character-design: needs_reference_images=false, detail_level=high."""
    recipe = _load_recipe()
    # Try v4 step id first, then v5 step id
    reqs = _get_step_requirements(recipe, "character-design")
    if reqs is None:
        reqs = _get_step_requirements(recipe, "design-characters")

    if reqs is not None:
        needs_reference_images = reqs["needs_reference_images"]
        detail_level = reqs["detail_level"]
    else:
        # v5 fallback: individual typed keys in top-level context
        ctx = recipe.get("context", {})
        needs_reference_images = ctx.get("character_design_needs_reference_images")
        detail_level = ctx.get("character_design_detail_level")
        assert needs_reference_images is not None, (
            "character design requirements not found in recipe (tried step reqs and direct context keys)"
        )

    assert needs_reference_images is False
    assert detail_level == "high"


def test_generate_panels_requirements():
    """generate-panels: needs_reference_images=true, detail_level=medium."""
    recipe = _load_recipe()
    reqs = _get_step_requirements(recipe, "generate-panels")

    if reqs is not None:
        needs_reference_images = reqs["needs_reference_images"]
        detail_level = reqs["detail_level"]
    else:
        # v5 fallback: individual typed keys in top-level context
        ctx = recipe.get("context", {})
        needs_reference_images = ctx.get("generate_panels_needs_reference_images")
        detail_level = ctx.get("generate_panels_detail_level")
        assert needs_reference_images is not None, (
            "generate-panels requirements not found in recipe (tried step reqs and direct context keys)"
        )

    assert needs_reference_images is True
    assert detail_level == "medium"


def test_generate_cover_requirements():
    """generate-cover: needs_reference_images=true, detail_level=high."""
    recipe = _load_recipe()
    reqs = _get_step_requirements(recipe, "generate-cover")

    if reqs is not None:
        needs_reference_images = reqs["needs_reference_images"]
        detail_level = reqs["detail_level"]
    else:
        # v5 fallback: individual typed keys in top-level context
        ctx = recipe.get("context", {})
        needs_reference_images = ctx.get("generate_cover_needs_reference_images")
        detail_level = ctx.get("generate_cover_detail_level")
        assert needs_reference_images is not None, (
            "generate-cover requirements not found in recipe (tried step reqs and direct context keys)"
        )

    assert needs_reference_images is True
    assert detail_level == "high"


# ============================================
# AC6: Composition depends on both parallel steps
# ============================================


def test_composition_depends_on_both_parallel_steps():
    """Composition step must explicitly depend on both parallel art generation steps.

    Note: test_parallel_art_generation validates the full fork-join graph structure.
    This test isolates the AC6 acceptance criterion for traceability.
    """
    recipe = _load_recipe()
    step = _find_step(recipe, "composition")
    assert step is not None, "composition step not found"

    depends = step.get("depends_on", [])
    assert "generate-panels" in depends, "composition must depend on generate-panels"
    assert "generate-cover" in depends, "composition must depend on generate-cover"


# ============================================
# AC7: Storyboard step prompt references stories delegation
# ============================================


def test_storyboard_step_mentions_delegation():
    """Storyboard step prompt should reference stories bundle delegation."""
    recipe = _load_recipe()
    step = _find_step(recipe, "storyboard")
    assert step is not None, "storyboard step not found"
    prompt = step.get("prompt", "")
    assert "stories:content-strategist" in prompt or "delegate" in prompt.lower(), (
        "Storyboard step prompt should reference delegation to stories agents"
    )


# ============================================
# V5: Foreach structure validation
# ============================================


class TestRecipeV5ForeachStructure:
    """Validate the v5 foreach loop structure introduced in session-to-comic v5.0.0."""

    def test_recipe_version_is_5_or_later(self):
        """Recipe version must be 5.0.0 or later."""
        recipe = _load_recipe()
        parts = recipe["version"].split(".")
        major = int(parts[0])
        assert major >= 5, f"Expected major version >= 5, got {recipe['version']}"

    def test_character_foreach_exists(self):
        """A foreach step with 'character' in the foreach value must exist."""
        recipe = _load_recipe()
        all_steps = _get_all_steps(recipe)
        character_foreach = [
            step for step in all_steps if "character" in step.get("foreach", "")
        ]
        assert len(character_foreach) > 0, (
            "No foreach step with 'character' in foreach value found in recipe"
        )

    def test_panel_foreach_exists(self):
        """A foreach step with 'panel' in the foreach value must exist."""
        recipe = _load_recipe()
        all_steps = _get_all_steps(recipe)
        panel_foreach = [
            step for step in all_steps if "panel" in step.get("foreach", "")
        ]
        assert len(panel_foreach) > 0, (
            "No foreach step with 'panel' in foreach value found in recipe"
        )

    def test_character_foreach_uses_single_item_agent(self):
        """Character foreach step must use comic-strips:character-designer agent."""
        recipe = _load_recipe()
        all_steps = _get_all_steps(recipe)
        character_foreach_steps = [
            step for step in all_steps if "character" in step.get("foreach", "")
        ]
        assert len(character_foreach_steps) > 0, "No character foreach step found"
        step = character_foreach_steps[0]
        assert step.get("agent") == "comic-strips:character-designer", (
            f"Character foreach step must use comic-strips:character-designer, "
            f"got {step.get('agent')}"
        )

    def test_panel_foreach_uses_single_item_agent(self):
        """Panel foreach step must use comic-strips:panel-artist agent."""
        recipe = _load_recipe()
        all_steps = _get_all_steps(recipe)
        panel_foreach_steps = [
            step for step in all_steps if "panel" in step.get("foreach", "")
        ]
        assert len(panel_foreach_steps) > 0, "No panel foreach step found"
        step = panel_foreach_steps[0]
        assert step.get("agent") == "comic-strips:panel-artist", (
            f"Panel foreach step must use comic-strips:panel-artist, "
            f"got {step.get('agent')}"
        )

    def test_approval_gate_still_present(self):
        """Storyboard stage must still have approval.required: true."""
        recipe = _load_recipe()
        stage = _find_stage_containing_step(recipe, "storyboard")
        assert stage is not None, "No stage contains the storyboard step"
        approval = stage.get("approval", {})
        assert approval.get("required") is True, (
            "Storyboard stage must have approval.required: true"
        )

    def test_composition_still_depends_on_panels_and_cover(self):
        """Composition step must still depend on both generate-panels and generate-cover."""
        recipe = _load_recipe()
        step = _find_step(recipe, "composition")
        assert step is not None, "composition step not found"
        depends = step.get("depends_on", [])
        assert "generate-panels" in depends, (
            "composition must depend on generate-panels"
        )
        assert "generate-cover" in depends, "composition must depend on generate-cover"

    def test_character_foreach_uses_dot_notation_source(self):
        """Character foreach source uses dot notation: {{storyboard.character_list}}."""
        recipe = _load_recipe()
        all_steps = _get_all_steps(recipe)
        character_foreach = [
            step for step in all_steps if "character" in step.get("foreach", "")
        ]
        assert character_foreach, "No character foreach step found"
        foreach_source = character_foreach[0].get("foreach", "")
        assert "storyboard.character_list" in foreach_source, (
            f"Expected 'storyboard.character_list' in foreach source, got: {foreach_source}"
        )

    def test_panel_foreach_uses_dot_notation_source(self):
        """Panel foreach source uses dot notation: {{storyboard.panel_list}}."""
        recipe = _load_recipe()
        all_steps = _get_all_steps(recipe)
        panel_foreach = [
            step for step in all_steps if "panel" in step.get("foreach", "")
        ]
        assert panel_foreach, "No panel foreach step found"
        foreach_source = panel_foreach[0].get("foreach", "")
        assert "storyboard.panel_list" in foreach_source, (
            f"Expected 'storyboard.panel_list' in foreach source, got: {foreach_source}"
        )
