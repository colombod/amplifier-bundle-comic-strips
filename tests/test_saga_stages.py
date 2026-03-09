"""Tests for session-to-comic.yaml Stage 2 (character-design) and Stage 3 (per-issue-art).

Task 11: Replace the old art-generation stage with two new stages:
  Stage 2 — character-design: foreach over character_roster with character-designer
  Stage 3 — per-issue-art: foreach over saga_plan.issues invoking issue-art.yaml sub-recipe

Validates:
1.  Recipe has exactly 3 stages
2.  Stage 2 name is 'character-design'
3.  Stage 2 step 'design-characters' foreach over {{storyboard.character_roster}}
4.  design-characters agent is comic-strips:character-designer
5.  design-characters parallel: 2, max_iterations: 20, timeout: 600
6.  design-characters retry: max_attempts: 2, initial_delay: 5
7.  design-characters collects to character_uris
8.  design-characters prompt covers three workflows (reuse, redesign, create new)
9.  design-characters prompt handles per-issue variants
10. Stage 3 name is 'per-issue-art'
11. Stage 3 step 'generate-issues' foreach over {{storyboard.saga_plan.issues}}
12. generate-issues type: recipe, recipe: issue-art.yaml
13. generate-issues on_error: continue
14. generate-issues max_iterations: 20, timeout: 7200
15. generate-issues passes all required context variables
16. generate-issues collects to issue_results
17. Old 'art-generation' stage no longer exists
"""

import pytest
import pathlib

import yaml

pytestmark = pytest.mark.skip(reason="legacy test for pre-v9 recipe")

RECIPE_PATH = pathlib.Path(__file__).parent.parent / "recipes" / "session-to-comic.yaml"


def _parse_recipe():
    return yaml.safe_load(RECIPE_PATH.read_text())


def _find_stage(data, name):
    """Find a stage by name."""
    for stage in data.get("stages", []):
        if stage.get("name") == name:
            return stage
    return None


def _find_step_in_stage(stage, step_id):
    """Find a step by id within a stage."""
    for step in stage.get("steps", []):
        if step.get("id") == step_id:
            return step
    return None


# ---------------------------------------------------------------
# Test 1: Recipe has exactly 3 stages
# ---------------------------------------------------------------
def test_recipe_has_three_stages():
    """Recipe must have exactly 3 stages after restructuring."""
    data = _parse_recipe()
    stages = data.get("stages", [])
    assert len(stages) == 3, f"Expected 3 stages, got {len(stages)}"


# ---------------------------------------------------------------
# Test 2: Old art-generation stage no longer exists
# ---------------------------------------------------------------
def test_old_art_generation_stage_removed():
    """The old 'art-generation' stage must not exist."""
    data = _parse_recipe()
    stage = _find_stage(data, "art-generation")
    assert stage is None, "Old 'art-generation' stage must be removed"


# ---------------------------------------------------------------
# Test 3: Stage 2 exists with name 'character-design'
# ---------------------------------------------------------------
def test_stage2_name_is_character_design():
    """Second stage must be named 'character-design'."""
    data = _parse_recipe()
    stages = data.get("stages", [])
    assert len(stages) >= 2, "Need at least 2 stages"
    assert stages[1]["name"] == "character-design", (
        f"Stage 2 name should be 'character-design', got '{stages[1].get('name')}'"
    )


# ---------------------------------------------------------------
# Test 4: design-characters step exists in Stage 2
# ---------------------------------------------------------------
def test_design_characters_step_exists():
    """Stage 2 must contain a 'design-characters' step."""
    data = _parse_recipe()
    stage = _find_stage(data, "character-design")
    assert stage is not None, "character-design stage not found"
    step = _find_step_in_stage(stage, "design-characters")
    assert step is not None, (
        "design-characters step not found in character-design stage"
    )


# ---------------------------------------------------------------
# Test 5: design-characters iterates over character_roster
# ---------------------------------------------------------------
def test_design_characters_foreach_character_roster():
    """design-characters must foreach over {{storyboard.character_roster}}."""
    data = _parse_recipe()
    stage = _find_stage(data, "character-design")
    step = _find_step_in_stage(stage, "design-characters")
    assert step is not None, "design-characters step not found"
    foreach_val = step.get("foreach", "")
    assert "storyboard.character_roster" in foreach_val, (
        f"Expected foreach over storyboard.character_roster, got: {foreach_val}"
    )


# ---------------------------------------------------------------
# Test 6: design-characters uses correct agent
# ---------------------------------------------------------------
def test_design_characters_agent():
    """design-characters must use comic-strips:character-designer agent."""
    data = _parse_recipe()
    stage = _find_stage(data, "character-design")
    step = _find_step_in_stage(stage, "design-characters")
    assert step is not None
    assert step.get("agent") == "comic-strips:character-designer", (
        f"Expected agent comic-strips:character-designer, got {step.get('agent')}"
    )


# ---------------------------------------------------------------
# Test 7: design-characters parallel, max_iterations, timeout
# ---------------------------------------------------------------
def test_design_characters_execution_params():
    """design-characters must have parallel: 2, max_iterations: 20, timeout: 600."""
    data = _parse_recipe()
    stage = _find_stage(data, "character-design")
    step = _find_step_in_stage(stage, "design-characters")
    assert step is not None
    assert step.get("parallel") == 2, (
        f"parallel should be 2, got {step.get('parallel')}"
    )
    assert step.get("max_iterations") == 20, (
        f"max_iterations should be 20, got {step.get('max_iterations')}"
    )
    assert step.get("timeout") == 600, (
        f"timeout should be 600, got {step.get('timeout')}"
    )


# ---------------------------------------------------------------
# Test 8: design-characters retry config
# ---------------------------------------------------------------
def test_design_characters_retry():
    """design-characters must have retry: max_attempts: 2, initial_delay: 5."""
    data = _parse_recipe()
    stage = _find_stage(data, "character-design")
    step = _find_step_in_stage(stage, "design-characters")
    assert step is not None
    retry = step.get("retry", {})
    assert retry.get("max_attempts") == 2, (
        f"retry.max_attempts should be 2, got {retry.get('max_attempts')}"
    )
    assert retry.get("initial_delay") == 5, (
        f"retry.initial_delay should be 5, got {retry.get('initial_delay')}"
    )


# ---------------------------------------------------------------
# Test 9: design-characters collects to character_uris
# ---------------------------------------------------------------
def test_design_characters_collects_to_character_uris():
    """design-characters must collect results into character_uris."""
    data = _parse_recipe()
    stage = _find_stage(data, "character-design")
    step = _find_step_in_stage(stage, "design-characters")
    assert step is not None
    assert step.get("collect") == "character_uris", (
        f"Expected collect: character_uris, got {step.get('collect')}"
    )


# ---------------------------------------------------------------
# Test 10: design-characters prompt covers three workflows
# ---------------------------------------------------------------
def test_design_characters_prompt_three_workflows():
    """design-characters prompt must handle reuse, redesign, and create-new workflows."""
    data = _parse_recipe()
    stage = _find_stage(data, "character-design")
    step = _find_step_in_stage(stage, "design-characters")
    assert step is not None
    prompt = step.get("prompt", "")
    # Must mention existing_uri for reuse workflow
    assert "existing_uri" in prompt, (
        "Prompt must reference existing_uri for reuse workflow"
    )
    # Must mention needs_redesign for redesign workflow
    assert "needs_redesign" in prompt, (
        "Prompt must reference needs_redesign for redesign workflow"
    )
    # Must handle creating new characters
    assert "new" in prompt.lower() or "create" in prompt.lower(), (
        "Prompt must handle creating new characters"
    )


# ---------------------------------------------------------------
# Test 11: design-characters prompt handles per-issue variants
# ---------------------------------------------------------------
def test_design_characters_prompt_per_issue_variants():
    """design-characters prompt must create per-issue variants."""
    data = _parse_recipe()
    stage = _find_stage(data, "character-design")
    step = _find_step_in_stage(stage, "design-characters")
    assert step is not None
    prompt = step.get("prompt", "")
    assert "per_issue" in prompt, "Prompt must reference per_issue for variant handling"


# ---------------------------------------------------------------
# Test 12: Stage 3 exists with name 'per-issue-art'
# ---------------------------------------------------------------
def test_stage3_name_is_per_issue_art():
    """Third stage must be named 'per-issue-art'."""
    data = _parse_recipe()
    stages = data.get("stages", [])
    assert len(stages) >= 3, "Need at least 3 stages"
    assert stages[2]["name"] == "per-issue-art", (
        f"Stage 3 name should be 'per-issue-art', got '{stages[2].get('name')}'"
    )


# ---------------------------------------------------------------
# Test 13: generate-issues step exists in Stage 3
# ---------------------------------------------------------------
def test_generate_issues_step_exists():
    """Stage 3 must contain a 'generate-issues' step."""
    data = _parse_recipe()
    stage = _find_stage(data, "per-issue-art")
    assert stage is not None, "per-issue-art stage not found"
    step = _find_step_in_stage(stage, "generate-issues")
    assert step is not None, "generate-issues step not found in per-issue-art stage"


# ---------------------------------------------------------------
# Test 14: generate-issues iterates over saga_plan.issues
# ---------------------------------------------------------------
def test_generate_issues_foreach_saga_plan_issues():
    """generate-issues must foreach over {{storyboard.saga_plan.issues}}."""
    data = _parse_recipe()
    stage = _find_stage(data, "per-issue-art")
    step = _find_step_in_stage(stage, "generate-issues")
    assert step is not None
    foreach_val = step.get("foreach", "")
    assert "storyboard.saga_plan.issues" in foreach_val, (
        f"Expected foreach over storyboard.saga_plan.issues, got: {foreach_val}"
    )


# ---------------------------------------------------------------
# Test 15: generate-issues is a recipe-type step
# ---------------------------------------------------------------
def test_generate_issues_is_recipe_type():
    """generate-issues must have type: recipe and recipe: issue-art.yaml."""
    data = _parse_recipe()
    stage = _find_stage(data, "per-issue-art")
    step = _find_step_in_stage(stage, "generate-issues")
    assert step is not None
    assert step.get("type") == "recipe", (
        f"Expected type: recipe, got {step.get('type')}"
    )
    assert step.get("recipe") == "issue-art.yaml", (
        f"Expected recipe: issue-art.yaml, got {step.get('recipe')}"
    )


# ---------------------------------------------------------------
# Test 16: generate-issues on_error: continue
# ---------------------------------------------------------------
def test_generate_issues_on_error_continue():
    """generate-issues must have on_error: continue."""
    data = _parse_recipe()
    stage = _find_stage(data, "per-issue-art")
    step = _find_step_in_stage(stage, "generate-issues")
    assert step is not None
    assert step.get("on_error") == "continue", (
        f"Expected on_error: continue, got {step.get('on_error')}"
    )


# ---------------------------------------------------------------
# Test 17: generate-issues max_iterations and timeout
# ---------------------------------------------------------------
def test_generate_issues_execution_params():
    """generate-issues must have max_iterations: 20, timeout: 7200."""
    data = _parse_recipe()
    stage = _find_stage(data, "per-issue-art")
    step = _find_step_in_stage(stage, "generate-issues")
    assert step is not None
    assert step.get("max_iterations") == 20, (
        f"max_iterations should be 20, got {step.get('max_iterations')}"
    )
    assert step.get("timeout") == 7200, (
        f"timeout should be 7200, got {step.get('timeout')}"
    )


# ---------------------------------------------------------------
# Test 18: generate-issues collects to issue_results
# ---------------------------------------------------------------
def test_generate_issues_collects_to_issue_results():
    """generate-issues must collect results into issue_results."""
    data = _parse_recipe()
    stage = _find_stage(data, "per-issue-art")
    step = _find_step_in_stage(stage, "generate-issues")
    assert step is not None
    assert step.get("collect") == "issue_results", (
        f"Expected collect: issue_results, got {step.get('collect')}"
    )


# ---------------------------------------------------------------
# Test 19: generate-issues passes required context variables
# ---------------------------------------------------------------
def test_generate_issues_context_variables():
    """generate-issues must pass all required context variables to the sub-recipe."""
    data = _parse_recipe()
    stage = _find_stage(data, "per-issue-art")
    step = _find_step_in_stage(stage, "generate-issues")
    assert step is not None
    ctx = step.get("context", {})
    required_vars = [
        "project_id",
        "issue_id",
        "issue_number",
        "issue_storyboard",
        "character_uris",
        "style_uri",
        "style",
        "output_name",
        "saga_context",
        "content_policy_notes",
    ]
    for var in required_vars:
        assert var in ctx, f"Missing context variable: {var}"


# ---------------------------------------------------------------
# Test 20: generate-issues context maps style_uri from style_guide
# ---------------------------------------------------------------
def test_generate_issues_style_uri_from_style_guide():
    """style_uri context variable should map from {{style_guide}}."""
    data = _parse_recipe()
    stage = _find_stage(data, "per-issue-art")
    step = _find_step_in_stage(stage, "generate-issues")
    assert step is not None
    ctx = step.get("context", {})
    style_uri_val = str(ctx.get("style_uri", ""))
    assert "style_guide" in style_uri_val, (
        f"style_uri should reference style_guide, got: {style_uri_val}"
    )


# ---------------------------------------------------------------
# Test 21: generate-issues context maps issue_id from current_issue
# ---------------------------------------------------------------
def test_generate_issues_issue_id_mapping():
    """issue_id context variable should map from the foreach item's issue_id."""
    data = _parse_recipe()
    stage = _find_stage(data, "per-issue-art")
    step = _find_step_in_stage(stage, "generate-issues")
    assert step is not None
    ctx = step.get("context", {})
    issue_id_val = str(ctx.get("issue_id", ""))
    assert "issue_id" in issue_id_val, (
        f"issue_id should reference the foreach item's issue_id, got: {issue_id_val}"
    )
