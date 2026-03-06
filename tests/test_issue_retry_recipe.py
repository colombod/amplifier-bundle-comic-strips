"""Regression tests for recipes/issue-retry.yaml — surgical single-issue retry recipe.

Validates structural correctness:
1. YAML is well-formed and parseable
2. Required recipe fields exist (name, version, tags)
3. All step IDs are unique and match expected set (4 steps)
4. Expected context variables are declared
5. Step 0 (load-existing-assets) is a style-curator agent with parse_json and timeout
6. Step 1 (generate-panels) foreach iterates over existing_assets.storyboard.panel_list
7. Step 2 (generate-cover) has depends_on: [] and retry
8. Step 3 (composition) depends on generate-panels and generate-cover
9. Uses existing_assets.* references (key difference from issue-art.yaml)
"""

import pathlib

import yaml

RECIPE_PATH = pathlib.Path(__file__).parent.parent / "recipes" / "issue-retry.yaml"

EXPECTED_CONTEXT_VARS = [
    "project_id",
    "issue_id",
    "style",
]

OPTIONAL_CONTEXT_VARS = [
    "output_name",
    "content_policy_notes",
]

EXPECTED_STEP_IDS = [
    "load-existing-assets",
    "generate-panels",
    "generate-cover",
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
# Test 1: YAML is well-formed and parseable
# ---------------------------------------------------------------
def test_yaml_is_parseable():
    """Recipe YAML must parse without errors."""
    data = _parse_recipe()
    assert data is not None, "Recipe parsed to None"
    assert isinstance(data, dict), f"Recipe root is {type(data)}, expected dict"


# ---------------------------------------------------------------
# Test 2: Required recipe fields exist
# ---------------------------------------------------------------
def test_required_recipe_fields():
    """Recipe must have name=issue-retry, version=1.0.0, correct tags."""
    data = _parse_recipe()
    for field in ("name", "description", "version", "tags", "context", "stages"):
        assert field in data, f"Missing required field: {field}"
    assert data["name"] == "issue-retry"
    assert data["version"] == "1.0.0"
    assert sorted(data["tags"]) == sorted(["comic", "retry", "saga", "recovery"])


# ---------------------------------------------------------------
# Test 3: All step IDs are unique and match expected set (4 steps)
# ---------------------------------------------------------------
def test_step_ids_unique_and_expected():
    """Step IDs must be unique and match the expected 4-step set."""
    data = _parse_recipe()
    steps = _get_steps(data)
    step_ids = [s["id"] for s in steps]
    assert len(step_ids) == len(set(step_ids)), (
        f"Duplicate step IDs: {[s for s in step_ids if step_ids.count(s) > 1]}"
    )
    assert sorted(step_ids) == sorted(EXPECTED_STEP_IDS), (
        f"Expected steps {EXPECTED_STEP_IDS}, got {step_ids}"
    )


# ---------------------------------------------------------------
# Test 4: All expected context variables are declared
# ---------------------------------------------------------------
def test_context_variables():
    """Required context vars (project_id, issue_id, style) and optional ones must be declared."""
    data = _parse_recipe()
    ctx = data.get("context", {})
    for var in EXPECTED_CONTEXT_VARS:
        assert var in ctx, f"Missing required context variable: {var}"
    for var in OPTIONAL_CONTEXT_VARS:
        assert var in ctx, f"Missing optional context variable: {var}"


# ---------------------------------------------------------------
# Test 5: Step 0 — load-existing-assets configuration
# ---------------------------------------------------------------
def test_load_existing_assets_step():
    """Step 0 must use style-curator agent, parse_json: true, timeout: 300."""
    data = _parse_recipe()
    steps = _get_steps(data)
    step = _find_step(steps, "load-existing-assets")
    assert step is not None, "load-existing-assets step not found"
    assert step["agent"] == "comic-strips:style-curator", (
        f"Expected agent comic-strips:style-curator, got {step['agent']}"
    )
    assert step.get("parse_json") is True, (
        "load-existing-assets must have parse_json: true"
    )
    assert step.get("timeout") == 300, (
        f"load-existing-assets timeout must be 300, got {step.get('timeout')}"
    )
    # Must have output variable named existing_assets
    assert step.get("output") == "existing_assets", (
        f"load-existing-assets output must be 'existing_assets', got {step.get('output')}"
    )


# ---------------------------------------------------------------
# Test 6: Step 1 — generate-panels foreach configuration
# ---------------------------------------------------------------
def test_generate_panels_step():
    """generate-panels must foreach over existing_assets.storyboard.panel_list."""
    data = _parse_recipe()
    steps = _get_steps(data)
    step = _find_step(steps, "generate-panels")
    assert step is not None, "generate-panels step not found"
    assert step["agent"] == "comic-strips:panel-artist"
    assert "foreach" in step, "generate-panels must have 'foreach'"
    assert "existing_assets.storyboard.panel_list" in step["foreach"], (
        f"foreach must reference existing_assets.storyboard.panel_list, got {step['foreach']}"
    )
    assert step.get("parallel") == 2, "generate-panels parallel must be 2"
    assert step.get("max_iterations") == 60, "generate-panels max_iterations must be 60"
    assert step.get("retry", {}).get("max_attempts") == 2, (
        "generate-panels retry max_attempts must be 2"
    )
    assert step.get("timeout") == 600, "generate-panels timeout must be 600"
    assert "collect" in step, "generate-panels must use 'collect' (not 'output')"
    assert step["collect"] == "panel_results"


# ---------------------------------------------------------------
# Test 7: Step 2 — generate-cover configuration
# ---------------------------------------------------------------
def test_generate_cover_step():
    """generate-cover must have depends_on: [], retry, timeout: 600."""
    data = _parse_recipe()
    steps = _get_steps(data)
    step = _find_step(steps, "generate-cover")
    assert step is not None, "generate-cover step not found"
    assert step["agent"] == "comic-strips:cover-artist"
    assert step.get("depends_on") == [], (
        "generate-cover must have depends_on: [] for parallelism"
    )
    assert step.get("retry", {}).get("max_attempts") == 2, (
        "generate-cover retry max_attempts must be 2"
    )
    assert step.get("timeout") == 600, "generate-cover timeout must be 600"
    assert step.get("output") == "cover_results"


# ---------------------------------------------------------------
# Test 8: Step 3 — composition configuration
# ---------------------------------------------------------------
def test_composition_step():
    """composition must depend on generate-panels and generate-cover, timeout: 2400."""
    data = _parse_recipe()
    steps = _get_steps(data)
    step = _find_step(steps, "composition")
    assert step is not None, "composition step not found"
    assert step["agent"] == "comic-strips:strip-compositor"
    comp_deps = sorted(step.get("depends_on", []))
    assert comp_deps == ["generate-cover", "generate-panels"], (
        f"Composition depends_on must be [generate-panels, generate-cover], got {comp_deps}"
    )
    assert step.get("timeout") == 2400, "composition timeout must be 2400"
    assert step.get("output") == "final_output"


# ---------------------------------------------------------------
# Test 9: Recipe uses existing_assets.* references
# ---------------------------------------------------------------
def test_uses_existing_assets_references():
    """Key difference from issue-art.yaml: prompts reference existing_assets.* not parent-passed context."""
    data = _parse_recipe()
    steps = _get_steps(data)
    # The panels step must foreach over existing_assets
    panels = _find_step(steps, "generate-panels")
    assert panels is not None, "generate-panels step not found"
    assert "existing_assets" in panels.get("foreach", ""), (
        "generate-panels foreach must reference existing_assets"
    )
    # Other steps should also reference existing_assets in their prompts
    cover = _find_step(steps, "generate-cover")
    assert cover is not None, "generate-cover step not found"
    comp = _find_step(steps, "composition")
    assert comp is not None, "composition step not found"
    cover_prompt = cover.get("prompt", "")
    assert "existing_assets" in cover_prompt, (
        "Cover step prompt must reference existing_assets"
    )
    comp_prompt = comp.get("prompt", "")
    # Composition uses panel_results and cover_results (from step outputs), not existing_assets directly
    # But it may reference existing_assets for storyboard/style info
    assert "existing_assets" in comp_prompt or "panel_results" in comp_prompt, (
        "Composition step prompt must reference existing_assets or panel_results"
    )


# ---------------------------------------------------------------
# Test 10: Every step has required fields
# ---------------------------------------------------------------
def test_steps_have_required_fields():
    """Every step must have id, agent, prompt, and output or collect."""
    data = _parse_recipe()
    for step in _get_steps(data):
        sid = step.get("id", "<unknown>")
        assert "id" in step, "Step missing 'id'"
        assert "agent" in step, f"Step '{sid}' missing 'agent'"
        assert "prompt" in step, f"Step '{sid}' missing 'prompt'"
        has_output = "output" in step or "collect" in step
        assert has_output, f"Step '{sid}' missing both 'output' and 'collect'"


# ---------------------------------------------------------------
# Test 11: load-existing-assets prompt mentions key assets
# ---------------------------------------------------------------
def test_load_existing_assets_prompt_content():
    """Step 0 prompt must instruct loading storyboard, character list, and style guide."""
    data = _parse_recipe()
    steps = _get_steps(data)
    step = _find_step(steps, "load-existing-assets")
    assert step is not None, "load-existing-assets step not found"
    prompt = step.get("prompt", "")
    assert "storyboard" in prompt.lower(), "Prompt must mention storyboard"
    assert "character" in prompt.lower(), "Prompt must mention characters"
    assert "style" in prompt.lower(), "Prompt must mention style guide"
