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

from conftest import EXPECTED_STEP_IDS


# ---------------------------------------------------------------
# Test 1: YAML still parses after modification
# ---------------------------------------------------------------
def test_yaml_still_parses(issue_art_recipe):
    """Recipe YAML must parse without errors after adding new step."""
    assert issue_art_recipe is not None, "Recipe parsed to None"
    assert isinstance(issue_art_recipe, dict), (
        f"Recipe root is {type(issue_art_recipe)}, expected dict"
    )


# ---------------------------------------------------------------
# Test 2: Step count is 5
# ---------------------------------------------------------------
def test_step_count_is_five(issue_art_steps):
    """Issue-art recipe must have exactly 5 steps after adding inspect-flagged-panels."""
    assert len(issue_art_steps) == 5, (
        f"Expected 5 steps, got {len(issue_art_steps)}: "
        f"{[s['id'] for s in issue_art_steps]}"
    )


# ---------------------------------------------------------------
# Test 3: Step order matches expected
# ---------------------------------------------------------------
def test_step_order(issue_art_steps):
    """Steps must appear in the correct order."""
    step_ids = [s["id"] for s in issue_art_steps]
    assert step_ids == EXPECTED_STEP_IDS, (
        f"Expected step order {EXPECTED_STEP_IDS}, got {step_ids}"
    )


# ---------------------------------------------------------------
# Test 4: inspect-flagged-panels depends_on ['generate-panels']
# ---------------------------------------------------------------
def test_inspect_flagged_panels_depends_on_generate_panels(find_step):
    """inspect-flagged-panels must depend on generate-panels."""
    step = find_step("inspect-flagged-panels")
    assert step is not None, "inspect-flagged-panels step not found"
    assert step.get("depends_on") == ["generate-panels"], (
        f"inspect-flagged-panels depends_on must be ['generate-panels'], "
        f"got {step.get('depends_on')}"
    )


# ---------------------------------------------------------------
# Test 5: review-panel-compositions depends_on ['inspect-flagged-panels']
# ---------------------------------------------------------------
def test_review_panel_compositions_depends_on_inspect(find_step):
    """review-panel-compositions must now depend on inspect-flagged-panels (changed)."""
    step = find_step("review-panel-compositions")
    assert step is not None, "review-panel-compositions step not found"
    assert step.get("depends_on") == ["inspect-flagged-panels"], (
        f"review-panel-compositions depends_on must be ['inspect-flagged-panels'], "
        f"got {step.get('depends_on')}"
    )


# ---------------------------------------------------------------
# Test 6: composition depends_on unchanged
# ---------------------------------------------------------------
def test_composition_depends_on_unchanged(find_step):
    """composition must still depend on review-panel-compositions and generate-cover."""
    step = find_step("composition")
    assert step is not None, "composition step not found"
    deps = sorted(step.get("depends_on", []))
    assert deps == ["generate-cover", "review-panel-compositions"], (
        f"composition depends_on must be ['review-panel-compositions', 'generate-cover'], "
        f"got {step.get('depends_on')}"
    )


# ---------------------------------------------------------------
# Test 7: inspect-flagged-panels has model_role: fast
# ---------------------------------------------------------------
def test_inspect_flagged_panels_model_role(find_step):
    """inspect-flagged-panels must have model_role: fast."""
    step = find_step("inspect-flagged-panels")
    assert step is not None, "inspect-flagged-panels step not found"
    assert step.get("model_role") == "fast", (
        f"inspect-flagged-panels model_role must be 'fast', got {step.get('model_role')}"
    )


# ---------------------------------------------------------------
# Test 8: inspect-flagged-panels output and parse_json
# ---------------------------------------------------------------
def test_inspect_flagged_panels_output(find_step):
    """inspect-flagged-panels must have output 'flagged_panel_report' with parse_json: true."""
    step = find_step("inspect-flagged-panels")
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
def test_inspect_flagged_panels_timeout(find_step):
    """inspect-flagged-panels must have timeout: 300 (5 minutes)."""
    step = find_step("inspect-flagged-panels")
    assert step is not None, "inspect-flagged-panels step not found"
    assert step.get("timeout") == 300, (
        f"inspect-flagged-panels timeout must be 300, got {step.get('timeout')}"
    )


# ---------------------------------------------------------------
# Test 10: inspect-flagged-panels agent is style-curator
# ---------------------------------------------------------------
def test_inspect_flagged_panels_agent(find_step):
    """inspect-flagged-panels must use comic-strips:style-curator agent."""
    step = find_step("inspect-flagged-panels")
    assert step is not None, "inspect-flagged-panels step not found"
    assert step.get("agent") == "comic-strips:style-curator", (
        f"inspect-flagged-panels agent must be 'comic-strips:style-curator', "
        f"got {step.get('agent')}"
    )


# ---------------------------------------------------------------
# Test 11: inspect-flagged-panels prompt references key terms
# ---------------------------------------------------------------
def test_inspect_flagged_panels_prompt_content(find_step):
    """inspect-flagged-panels prompt must reference panel_results and flagged."""
    step = find_step("inspect-flagged-panels")
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
def test_full_dependency_chain(find_step):
    """Verify the complete dependency chain as specified."""
    panels = find_step("generate-panels")
    inspect = find_step("inspect-flagged-panels")
    cover = find_step("generate-cover")
    review = find_step("review-panel-compositions")
    comp = find_step("composition")

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
