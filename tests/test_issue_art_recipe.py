"""Regression tests for recipes/issue-art.yaml sub-recipe.

Validates structural correctness that recipe validation alone may not catch:
1. YAML is well-formed and parseable
2. Required recipe fields exist
3. All step IDs are unique
4. Expected context variables are declared
5. Dependency graph is correct (panels + cover parallel, composition waits for both)
6. Every step has required fields (id, agent, prompt, output/collect)
7. Foreach step has required foreach configuration
8. Error sentinel is defined in cover step and handled in composition step
"""

import pathlib

import yaml

RECIPE_PATH = pathlib.Path(__file__).parent.parent / "recipes" / "issue-art.yaml"

EXPECTED_CONTEXT_VARS = [
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

EXPECTED_STEP_IDS = [
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
    """Recipe must have name, description, version, tags, context, stages."""
    data = _parse_recipe()
    for field in ("name", "description", "version", "tags", "context", "stages"):
        assert field in data, f"Missing required field: {field}"
    assert data["name"] == "issue-art"
    assert data["version"] == "1.0.0"


# ---------------------------------------------------------------
# Test 3: All step IDs are unique and match expected set
# ---------------------------------------------------------------
def test_step_ids_unique_and_expected():
    """Step IDs must be unique and match the expected set."""
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
    """All 10 context variables from the parent recipe contract must be declared."""
    data = _parse_recipe()
    ctx = data.get("context", {})
    for var in EXPECTED_CONTEXT_VARS:
        assert var in ctx, f"Missing context variable: {var}"


# ---------------------------------------------------------------
# Test 5: Dependency graph is correct
# ---------------------------------------------------------------
def test_dependency_graph():
    """Dependency chain: panels -> inspect -> review -> composition; cover parallel."""
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

    # Panels has no explicit depends_on (first step, implicitly independent)
    assert "depends_on" not in panels or panels["depends_on"] == []

    # Inspect depends on panels
    assert inspect.get("depends_on") == ["generate-panels"]

    # Cover explicitly declares no dependencies to run in parallel
    assert cover.get("depends_on") == [], (
        "Cover must have depends_on: [] for parallelism"
    )

    # Review depends on inspect (changed from generate-panels)
    assert review.get("depends_on") == ["inspect-flagged-panels"]

    # Composition waits for review and cover
    comp_deps = sorted(comp.get("depends_on", []))
    assert comp_deps == ["generate-cover", "review-panel-compositions"], (
        f"Composition depends_on must be [review-panel-compositions, generate-cover], got {comp_deps}"
    )


# ---------------------------------------------------------------
# Test 6: Every step has required fields
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
# Test 7: Foreach step has correct configuration
# ---------------------------------------------------------------
def test_foreach_step_configuration():
    """generate-panels must have foreach, as, parallel, and collect."""
    data = _parse_recipe()
    panels = _find_step(_get_steps(data), "generate-panels")
    assert panels is not None, "generate-panels step not found"
    assert "foreach" in panels, "generate-panels must have 'foreach'"
    assert "as" in panels, "generate-panels must have 'as' (iteration variable)"
    assert panels.get("parallel") == 2, "generate-panels parallel must be 2"
    assert "collect" in panels, "generate-panels must use 'collect' (not 'output')"


# ---------------------------------------------------------------
# Test 8: Cover failure sentinel defined and handled
# ---------------------------------------------------------------
def test_cover_failure_sentinel_contract():
    """Cover step must define COVER_GENERATION_FAILED; composition must handle it."""
    data = _parse_recipe()
    steps = _get_steps(data)
    cover = _find_step(steps, "generate-cover")
    comp = _find_step(steps, "composition")
    assert cover is not None, "generate-cover step not found"
    assert comp is not None, "composition step not found"

    assert "COVER_GENERATION_FAILED" in cover.get("prompt", ""), (
        "Cover step must define COVER_GENERATION_FAILED sentinel"
    )
    assert "COVER_GENERATION_FAILED" in comp.get("prompt", ""), (
        "Composition step must handle COVER_GENERATION_FAILED sentinel"
    )
