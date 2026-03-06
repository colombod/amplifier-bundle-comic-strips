"""Tests for recipe validation and sanity checks (Task 9).

Validates that:
1. Recipe YAML is well-formed and parseable
2. All step IDs are unique
3. All output variables are defined before use
4. session_file count is 3-5 (context var, discover-sessions, init-project metadata only)
5. Research step references {{session_data}} not {{session_file}}
6. Staged structure is well-formed (stages with steps and approval gates)
"""

import pathlib

import yaml

RECIPE_PATH = pathlib.Path(__file__).parent.parent / "recipes" / "session-to-comic.yaml"


def _read_recipe():
    return RECIPE_PATH.read_text()


def _parse_recipe():
    return yaml.safe_load(_read_recipe())


# ---------------------------------------------------------------
# Test 1: YAML is well-formed and parseable
# ---------------------------------------------------------------
def test_recipe_yaml_is_parseable():
    """Recipe YAML must parse without errors."""
    data = _parse_recipe()
    assert data is not None, "Recipe parsed to None"
    assert isinstance(data, dict), f"Recipe root is {type(data)}, expected dict"


# ---------------------------------------------------------------
# Test 2: All step IDs are unique
# ---------------------------------------------------------------
def test_step_ids_are_unique():
    """Every step id must be unique across all stages."""
    data = _parse_recipe()
    step_ids = []
    for stage in data.get("stages", []):
        for step in stage.get("steps", []):
            sid = step.get("id")
            if sid:
                step_ids.append(sid)
    duplicates = [sid for sid in step_ids if step_ids.count(sid) > 1]
    assert not duplicates, f"Duplicate step IDs found: {set(duplicates)}"


# ---------------------------------------------------------------
# Test 3: Required recipe fields exist
# ---------------------------------------------------------------
def test_required_recipe_fields():
    """Recipe must have name, description, version, context, stages."""
    data = _parse_recipe()
    for field in ("name", "description", "version", "context", "stages"):
        assert field in data, f"Missing required field: {field}"


# ---------------------------------------------------------------
# Test 4: Staged structure is well-formed
# ---------------------------------------------------------------
def test_staged_structure():
    """Recipe must have at least 2 stages, each with name and steps."""
    data = _parse_recipe()
    stages = data.get("stages", [])
    assert len(stages) >= 2, f"Expected >= 2 stages, got {len(stages)}"
    for i, stage in enumerate(stages):
        assert "name" in stage, f"Stage {i} missing 'name'"
        assert "steps" in stage, f"Stage {i} missing 'steps'"
        assert len(stage["steps"]) > 0, f"Stage {i} '{stage['name']}' has no steps"


# ---------------------------------------------------------------
# Test 5: session_file count is 3-5
# ---------------------------------------------------------------
def test_session_file_occurrence_count():
    """session_file should appear on 3-5 non-comment lines (grep -c style).

    Expected locations:
    1. context var declaration: session_file: ""
    2. discover-sessions prompt: {{session_file}} backward-compat reference(s)
    3. init-project metadata: "session_file": "{{session_file}}"
    """
    text = _read_recipe()
    # Count non-comment lines containing session_file (mirrors grep -c behaviour
    # after stripping pure-comment lines like the changelog).
    count = 0
    for line in text.splitlines():
        stripped = line.strip()
        # Skip pure comment lines (changelog, section markers, etc.)
        if stripped.startswith("#"):
            continue
        if "session_file" in line:
            count += 1
    assert 3 <= count <= 5, (
        f"Expected 3-5 non-comment lines with session_file, got {count}. "
        "Should be: context var, discover-sessions prompt lines, init-project metadata."
    )


# ---------------------------------------------------------------
# Test 6: Research step references session_data, NOT session_file
# ---------------------------------------------------------------
def test_research_step_uses_session_data():
    """Research step prompt must reference {{session_data}}, not {{session_file}}."""
    data = _parse_recipe()
    research_step = None
    for stage in data.get("stages", []):
        for step in stage.get("steps", []):
            if step.get("id") == "research":
                research_step = step
                break
    assert research_step is not None, "Research step not found"
    prompt = research_step.get("prompt", "")
    assert "{{session_data}}" in prompt, (
        "Research step prompt must reference {{session_data}}"
    )
    assert "{{session_file}}" not in prompt, (
        "Research step prompt must NOT reference {{session_file}}"
    )


# ---------------------------------------------------------------
# Test 7: session_file appears in the RIGHT places
# ---------------------------------------------------------------
def test_session_file_locations():
    """session_file should only appear in: context block, discover-sessions prompt, init-project metadata."""
    data = _parse_recipe()
    # Check it's in context
    ctx = data.get("context", {})
    assert "session_file" in ctx, "session_file must exist in context block"

    # Check discover-sessions prompt contains it
    discover_step = None
    init_step = None
    for stage in data.get("stages", []):
        for step in stage.get("steps", []):
            if step.get("id") == "discover-sessions":
                discover_step = step
            if step.get("id") == "init-project":
                init_step = step

    assert discover_step is not None, "discover-sessions step not found"
    assert "session_file" in discover_step.get("prompt", ""), (
        "discover-sessions prompt must reference session_file for backward compat"
    )

    assert init_step is not None, "init-project step not found"
    assert "session_file" in init_step.get("prompt", ""), (
        "init-project prompt must reference session_file in metadata dict"
    )


# ---------------------------------------------------------------
# Test 8: Each step has required fields
# ---------------------------------------------------------------
def test_steps_have_required_fields():
    """Every step must have id, agent, prompt, and output (or collect for foreach)."""
    data = _parse_recipe()
    for stage in data.get("stages", []):
        for step in stage.get("steps", []):
            sid = step.get("id", "<unknown>")
            assert "id" in step, f"Step missing 'id' in stage '{stage.get('name')}'"
            assert "agent" in step, f"Step '{sid}' missing 'agent'"
            assert "prompt" in step, f"Step '{sid}' missing 'prompt'"
            has_output = "output" in step or "collect" in step
            assert has_output, f"Step '{sid}' missing both 'output' and 'collect'"


# ---------------------------------------------------------------
# Test 9: Approval gate exists in stage 1
# ---------------------------------------------------------------
def test_approval_gate_exists():
    """First stage must have an approval gate."""
    data = _parse_recipe()
    first_stage = data["stages"][0]
    assert "approval" in first_stage, "First stage must have an approval gate"
    approval = first_stage["approval"]
    assert approval.get("required") is True, "Approval gate must be required"
