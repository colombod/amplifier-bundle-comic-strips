"""Tests for recipe improvements for session-to-comic.

Updated through v8: saga stages, sub-recipe delegation, URI protocol.
"""

import functools

import pytest
import yaml
from pathlib import Path

RECIPE_PATH = Path(__file__).parent.parent / "recipes" / "session-to-comic.yaml"


@functools.lru_cache(maxsize=1)
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


def _find_foreach_step(recipe: dict, keyword: str) -> dict | None:
    """Find the first step whose foreach value contains keyword (case-insensitive)."""
    for step in _get_all_steps(recipe):
        if keyword in step.get("foreach", "").lower():
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
    """Per-issue art generation is handled via sub-recipe invocation.

    In v8+, generate-panels, generate-cover, and composition moved to issue-art.yaml.
    The parent recipe now has a generate-issues step that invokes the sub-recipe
    for each issue. Parallel panel/cover execution is validated by test_issue_art_recipe.py.
    This test validates the parent recipe's sub-recipe delegation pattern.
    """
    recipe = _load_recipe()
    generate_issues = _find_step(recipe, "generate-issues")
    assert generate_issues is not None, "generate-issues step not found"

    # Sub-recipe invocation pattern
    assert generate_issues.get("type") == "recipe", (
        "generate-issues must be a recipe-type step"
    )
    assert generate_issues.get("recipe") == "issue-art.yaml", (
        "generate-issues must invoke issue-art.yaml sub-recipe"
    )


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
    """character-design requirements were removed in v7.0.0 (URI protocol migration).

    In v7+, image generation is handled internally by comic_create tool calls.
    The old needs_reference_images/detail_level context vars are no longer needed.
    This test now validates that design-characters exists and uses the correct agent.
    """
    recipe = _load_recipe()
    step = _find_step(recipe, "design-characters")
    assert step is not None, "design-characters step not found"
    assert step.get("agent") == "comic-strips:character-designer"


def test_generate_panels_requirements():
    """generate-panels moved to issue-art.yaml sub-recipe in v8.0.0.

    Panel generation is now handled per-issue by the issue-art.yaml sub-recipe,
    invoked via the generate-issues foreach step. Panel requirements are validated
    by test_issue_art_recipe.py.
    """
    recipe = _load_recipe()
    # generate-panels should NOT be in the parent recipe
    step = _find_step(recipe, "generate-panels")
    assert step is None, (
        "generate-panels should be in issue-art.yaml, not session-to-comic.yaml"
    )


def test_generate_cover_requirements():
    """generate-cover moved to issue-art.yaml sub-recipe in v8.0.0.

    Cover generation is now handled per-issue by the issue-art.yaml sub-recipe,
    invoked via the generate-issues foreach step. Cover requirements are validated
    by test_issue_art_recipe.py.
    """
    recipe = _load_recipe()
    # generate-cover should NOT be in the parent recipe
    step = _find_step(recipe, "generate-cover")
    assert step is None, (
        "generate-cover should be in issue-art.yaml, not session-to-comic.yaml"
    )


# ============================================
# AC6: Composition depends on both parallel steps
# ============================================


def test_composition_depends_on_both_parallel_steps():
    """Composition moved to issue-art.yaml sub-recipe in v8.0.0.

    The fork-join pattern (panels + cover → composition) is now inside
    issue-art.yaml. This is validated by test_issue_art_recipe.py.
    In the parent recipe, per-issue art is handled by generate-issues.
    """
    recipe = _load_recipe()
    # composition should NOT be in the parent recipe
    step = _find_step(recipe, "composition")
    assert step is None, (
        "composition should be in issue-art.yaml, not session-to-comic.yaml"
    )
    # generate-issues handles per-issue art via sub-recipe
    gen_issues = _find_step(recipe, "generate-issues")
    assert gen_issues is not None, "generate-issues step not found"


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

    @pytest.fixture
    def recipe(self) -> dict:
        """Load the recipe once per test."""
        return _load_recipe()

    def test_character_foreach_exists(self, recipe) -> None:
        """Recipe has a foreach step iterating over storyboard.character_roster."""
        step = _find_foreach_step(recipe, "character")
        assert step is not None, (
            "No character foreach step found — expected foreach over storyboard.character_roster"
        )

    def test_panel_foreach_exists(self, recipe) -> None:
        """Panel foreach moved to issue-art.yaml sub-recipe in v8.0.0.

        The parent recipe now has generate-issues (foreach over saga_plan.issues)
        which invokes issue-art.yaml. Panel foreach is validated by test_issue_art_recipe.py.
        """
        # Verify generate-issues exists as the replacement
        step = _find_step(recipe, "generate-issues")
        assert step is not None, (
            "generate-issues step not found — expected foreach over saga_plan.issues"
        )
        assert "saga_plan.issues" in step.get("foreach", ""), (
            "generate-issues must foreach over saga_plan.issues"
        )

    def test_character_foreach_uses_correct_agent(self, recipe) -> None:
        """Character foreach step dispatches to comic-strips:character-designer."""
        step = _find_foreach_step(recipe, "character")
        assert step is not None, "No character foreach step found"
        assert step.get("agent") == "comic-strips:character-designer", (
            f"Character foreach uses wrong agent: {step.get('agent')}"
        )

    def test_panel_foreach_uses_correct_agent(self, recipe) -> None:
        """Panel foreach moved to issue-art.yaml in v8.0.0.

        Validate that generate-issues uses recipe type instead.
        """
        step = _find_step(recipe, "generate-issues")
        assert step is not None, "generate-issues step not found"
        assert step.get("type") == "recipe", (
            "generate-issues must be a recipe-type step (panels are in sub-recipe)"
        )

    def test_character_foreach_uses_dot_notation_source(self, recipe) -> None:
        """Character foreach source uses dot notation: {{storyboard.character_roster}}.

        Changed from character_list to character_roster in v8.0.0 to iterate
        over the shared saga character roster instead of per-issue character lists.
        """
        step = _find_foreach_step(recipe, "character")
        assert step is not None, "No character foreach step found"
        foreach_source = step.get("foreach", "")
        assert "storyboard.character_roster" in foreach_source, (
            f"Expected 'storyboard.character_roster' in foreach source, got: {foreach_source}"
        )

    def test_panel_foreach_uses_dot_notation_source(self, recipe) -> None:
        """Panel foreach moved to issue-art.yaml in v8.0.0.

        The parent recipe now iterates over saga_plan.issues instead.
        """
        step = _find_step(recipe, "generate-issues")
        assert step is not None, "generate-issues step not found"
        foreach_source = step.get("foreach", "")
        assert "storyboard.saga_plan.issues" in foreach_source, (
            f"Expected 'storyboard.saga_plan.issues' in foreach source, got: {foreach_source}"
        )


# ============================================
# V5: Runtime-correctness properties (C1 + C2)
# ============================================


class TestRecipeV5RuntimeCorrectness:
    """Validate runtime-correctness properties added in C1 and C2.

    These properties prevent silent failures:
    - parse_json: true enables dot-notation access to storyboard fields
    - parse_json: true on collect steps ensures structured objects, not raw strings
    - parallel: 2 bounds concurrent execution
    - max_iterations guards against runaway loops in the expensive art stage
    """

    @pytest.fixture
    def recipe(self) -> dict:
        return _load_recipe()

    def test_storyboard_step_has_parse_json_true(self, recipe) -> None:
        """Storyboard step must have parse_json: true for dot-notation access to character_list/panel_list."""
        step = _find_step(recipe, "storyboard")
        assert step is not None, "storyboard step not found"
        assert step.get("parse_json") is True, (
            "storyboard step requires parse_json: true — without it, "
            "{{storyboard.character_list}} resolves as a raw string, not an object"
        )

    def test_design_characters_collect_has_no_parse_json(self, recipe) -> None:
        """design-characters collects URI strings — parse_json not needed.

        In v7+, character design returns comic:// URI strings, not JSON objects.
        parse_json was removed as URIs are plain strings.
        """
        step = _find_foreach_step(recipe, "character")
        assert step is not None, "No character foreach step found"
        # URI strings don't need parse_json — it's either absent or False
        assert step.get("parse_json") is not True, (
            "design-characters should not have parse_json: true — URIs are plain strings"
        )

    def test_generate_panels_in_sub_recipe(self, recipe) -> None:
        """generate-panels moved to issue-art.yaml sub-recipe in v8.0.0.

        Panel generation is now per-issue via sub-recipe invocation.
        Validated by test_issue_art_recipe.py.
        """
        step = _find_step(recipe, "generate-issues")
        assert step is not None, "generate-issues step not found"
        assert step.get("recipe") == "issue-art.yaml"

    def test_design_characters_has_parallel_execution(self, recipe) -> None:
        """design-characters must have parallel: 2 for bounded concurrent execution."""
        step = _find_foreach_step(recipe, "character")
        assert step is not None, "No character foreach step found"
        assert step.get("parallel") == 2, (
            f"design-characters should have parallel: 2, got: {step.get('parallel')}"
        )

    def test_generate_issues_has_on_error_continue(self, recipe) -> None:
        """generate-issues must have on_error: continue for fault tolerance."""
        step = _find_step(recipe, "generate-issues")
        assert step is not None, "generate-issues step not found"
        assert step.get("on_error") == "continue", (
            f"generate-issues should have on_error: continue, got: {step.get('on_error')}"
        )

    def test_design_characters_has_max_iterations_guard(self, recipe) -> None:
        """design-characters must have max_iterations: 20 (saga roster ceiling).

        Increased from 6 to 20 in v8.0.0 to support saga-wide character rosters.
        """
        step = _find_foreach_step(recipe, "character")
        assert step is not None, "No character foreach step found"
        assert step.get("max_iterations") == 20, (
            f"design-characters should have max_iterations: 20, got: {step.get('max_iterations')}"
        )

    def test_generate_issues_has_max_iterations_guard(self, recipe) -> None:
        """generate-issues must have max_iterations: 20 (saga issue ceiling)."""
        step = _find_step(recipe, "generate-issues")
        assert step is not None, "generate-issues step not found"
        assert step.get("max_iterations") == 20, (
            f"generate-issues should have max_iterations: 20, got: {step.get('max_iterations')}"
        )
