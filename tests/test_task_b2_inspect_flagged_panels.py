"""Tests for Task B2: inspect-flagged-panels step in issue-art recipe.

Validates:
1. YAML is still valid after modification
2. Step count is 5 (was 4, added 1)
3. Step order: generate-panels, inspect-flagged-panels, generate-cover,
   review-panel-compositions, composition
4. inspect-flagged-panels depends_on ['generate-panels']
5. review-panel-compositions depends_on ['inspect-flagged-panels'] (changed)
6. composition depends_on ['review-panel-compositions', 'generate-cover'] (unchanged)
7. inspect-flagged-panels has model_role: fast
8. inspect-flagged-panels output is 'flagged_panel_report' with parse_json: true
9. inspect-flagged-panels has timeout: 300
10. inspect-flagged-panels agent is 'comic-strips:style-curator'
11. inspect-flagged-panels prompt references panel_results and flagged
"""

import pathlib

import yaml

RECIPE_PATH = pathlib.Path(__file__).parent.parent / "recipes" / "issue-art.yaml"

EXPECTED_STEP_ORDER = [
    "generate-panels",
    "inspect-flagged-panels",
    "generate-cover",
    "review-panel-compositions",
    "composition",
]


def _parse_recipe():
    return yaml.safe_load(RECIPE_PATH.read_text())


def _get_steps(data):
    """Return flat list of all steps across all stages."""
    steps = []
    for stage in data.get("stages", []):
        steps.extend(stage.get("steps", []))
    return steps


def _find_step(steps, step_id):
    """Find a step by id."""
    for step in steps:
        if step.get("id") == step_id:
            return step
    return None


# ---------------------------------------------------------------
# Test 1: YAML still parses after modification
# ---------------------------------------------------------------
def test_yaml_still_parses():
    """Recipe YAML must parse without errors after adding new step."""
    data = _parse_recipe()
    assert data is not None, "Recipe parsed to None"
    assert isinstance(data, dict), f"Recipe root is {type(data)}, expected dict"


# ---------------------------------------------------------------
# Test 2: Step count is 5
# ---------------------------------------------------------------
def test_step_count_is_five():
    """Issue-art recipe must have exactly 5 steps after adding inspect-flagged-panels."""
    data = _parse_recipe()
    steps = _get_steps(data)
    assert len(steps) == 5, (
        f"Expected 5 steps, got {len(steps)}: {[s['id'] for s in steps]}"
    )


# ---------------------------------------------------------------
# Test 3: Step order matches expected
# ---------------------------------------------------------------
def test_step_order():
    """Steps must appear in the correct order."""
    data = _parse_recipe()
    steps = _get_steps(data)
    step_ids = [s["id"] for s in steps]
    assert step_ids == EXPECTED_STEP_ORDER, (
        f"Expected step order {EXPECTED_STEP_ORDER}, got {step_ids}"
    )


# ---------------------------------------------------------------
# Test 4: inspect-flagged-panels depends_on ['generate-panels']
# ---------------------------------------------------------------
def test_inspect_flagged_panels_depends_on_generate_panels():
    """inspect-flagged-panels must depend on generate-panels."""
    data = _parse_recipe()
    steps = _get_steps(data)
    step = _find_step(steps, "inspect-flagged-panels")
    assert step is not None, "inspect-flagged-panels step not found"
    assert step.get("depends_on") == ["generate-panels"], (
        f"inspect-flagged-panels depends_on must be ['generate-panels'], "
        f"got {step.get('depends_on')}"
    )


# ---------------------------------------------------------------
# Test 5: review-panel-compositions depends_on ['inspect-flagged-panels']
# ---------------------------------------------------------------
def test_review_panel_compositions_depends_on_inspect():
    """review-panel-compositions must now depend on inspect-flagged-panels (changed)."""
    data = _parse_recipe()
    steps = _get_steps(data)
    step = _find_step(steps, "review-panel-compositions")
    assert step is not None, "review-panel-compositions step not found"
    assert step.get("depends_on") == ["inspect-flagged-panels"], (
        f"review-panel-compositions depends_on must be ['inspect-flagged-panels'], "
        f"got {step.get('depends_on')}"
    )


# ---------------------------------------------------------------
# Test 6: composition depends_on unchanged
# ---------------------------------------------------------------
def test_composition_depends_on_unchanged():
    """composition must still depend on review-panel-compositions and generate-cover."""
    data = _parse_recipe()
    steps = _get_steps(data)
    step = _find_step(steps, "composition")
    assert step is not None, "composition step not found"
    deps = sorted(step.get("depends_on", []))
    assert deps == ["generate-cover", "review-panel-compositions"], (
        f"composition depends_on must be ['review-panel-compositions', 'generate-cover'], "
        f"got {step.get('depends_on')}"
    )


# ---------------------------------------------------------------
# Test 7: inspect-flagged-panels has model_role: fast
# ---------------------------------------------------------------
def test_inspect_flagged_panels_model_role():
    """inspect-flagged-panels must have model_role: fast."""
    data = _parse_recipe()
    steps = _get_steps(data)
    step = _find_step(steps, "inspect-flagged-panels")
    assert step is not None, "inspect-flagged-panels step not found"
    assert step.get("model_role") == "fast", (
        f"inspect-flagged-panels model_role must be 'fast', got {step.get('model_role')}"
    )


# ---------------------------------------------------------------
# Test 8: inspect-flagged-panels output and parse_json
# ---------------------------------------------------------------
def test_inspect_flagged_panels_output():
    """inspect-flagged-panels must have output 'flagged_panel_report' with parse_json: true."""
    data = _parse_recipe()
    steps = _get_steps(data)
    step = _find_step(steps, "inspect-flagged-panels")
    assert step is not None, "inspect-flagged-panels step not found"
    assert step.get("output") == "flagged_panel_report", (
        f"inspect-flagged-panels output must be 'flagged_panel_report', "
        f"got {step.get('output')}"
    )
    assert step.get("parse_json") is True, (
        f"inspect-flagged-panels parse_json must be true, got {step.get('parse_json')}"
    )


# ---------------------------------------------------------------
# Test 9: inspect-flagged-panels has timeout: 300
# ---------------------------------------------------------------
def test_inspect_flagged_panels_timeout():
    """inspect-flagged-panels must have timeout: 300 (5 minutes)."""
    data = _parse_recipe()
    steps = _get_steps(data)
    step = _find_step(steps, "inspect-flagged-panels")
    assert step is not None, "inspect-flagged-panels step not found"
    assert step.get("timeout") == 300, (
        f"inspect-flagged-panels timeout must be 300, got {step.get('timeout')}"
    )


# ---------------------------------------------------------------
# Test 10: inspect-flagged-panels agent is style-curator
# ---------------------------------------------------------------
def test_inspect_flagged_panels_agent():
    """inspect-flagged-panels must use comic-strips:style-curator agent."""
    data = _parse_recipe()
    steps = _get_steps(data)
    step = _find_step(steps, "inspect-flagged-panels")
    assert step is not None, "inspect-flagged-panels step not found"
    assert step.get("agent") == "comic-strips:style-curator", (
        f"inspect-flagged-panels agent must be 'comic-strips:style-curator', "
        f"got {step.get('agent')}"
    )


# ---------------------------------------------------------------
# Test 11: inspect-flagged-panels prompt references key terms
# ---------------------------------------------------------------
def test_inspect_flagged_panels_prompt_content():
    """inspect-flagged-panels prompt must reference panel_results and flagged."""
    data = _parse_recipe()
    steps = _get_steps(data)
    step = _find_step(steps, "inspect-flagged-panels")
    assert step is not None, "inspect-flagged-panels step not found"
    prompt = step.get("prompt", "")
    assert "panel_results" in prompt, (
        "inspect-flagged-panels prompt must reference panel_results"
    )
    assert "flagged" in prompt, (
        "inspect-flagged-panels prompt must reference flagged entries"
    )
    # Prompt should instruct returning JSON with required fields
    for field in ["total_panels", "flagged_count", "flagged_panels"]:
        assert field in prompt, (
            f"inspect-flagged-panels prompt must mention '{field}' in output schema"
        )


# ---------------------------------------------------------------
# Test 12: Dependency chain is correct end-to-end
# ---------------------------------------------------------------
def test_full_dependency_chain():
    """Verify the complete dependency chain as specified."""
    data = _parse_recipe()
    steps = _get_steps(data)

    panels = _find_step(steps, "generate-panels")
    inspect = _find_step(steps, "inspect-flagged-panels")
    cover = _find_step(steps, "generate-cover")
    review = _find_step(steps, "review-panel-compositions")
    comp = _find_step(steps, "composition")

    assert panels is not None, "generate-panels step not found"
    assert inspect is not None, "inspect-flagged-panels step not found"
    assert cover is not None, "generate-cover step not found"
    assert review is not None, "review-panel-compositions step not found"
    assert comp is not None, "composition step not found"

    # generate-panels: implicit (no depends_on)
    assert "depends_on" not in panels or panels["depends_on"] == []

    # inspect-flagged-panels: depends on generate-panels
    assert inspect["depends_on"] == ["generate-panels"]

    # generate-cover: depends on [] (parallel)
    assert cover["depends_on"] == []

    # review-panel-compositions: depends on inspect-flagged-panels
    assert review["depends_on"] == ["inspect-flagged-panels"]

    # composition: depends on both review-panel-compositions and generate-cover
    assert sorted(comp["depends_on"]) == ["generate-cover", "review-panel-compositions"]
