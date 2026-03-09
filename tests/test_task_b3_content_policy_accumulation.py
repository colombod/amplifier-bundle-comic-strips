"""Tests for Task B3: content_policy_lesson accumulation in generate-panels step.

Validates:
1. YAML still parses as valid after modification
2. 'content_policy_lesson' appears at least 2 times in the raw file (instruction + example)
3. 'content_policy_notes' is still referenced in the file (existing context var)
4. The accumulation instruction is in the generate-panels step prompt, before collect
5. The generate-panels step prompt contains the JSON example with content_policy_lesson field
6. The generate-panels step still has collect: "panel_results"
"""

import pathlib

import yaml

_ISSUE_ART_PATH = pathlib.Path(__file__).parent.parent / "recipes" / "issue-art.yaml"


# ---------------------------------------------------------------
# Test 1: YAML still parses after modification
# ---------------------------------------------------------------
def test_yaml_still_parses(issue_art_recipe):
    """Recipe YAML must parse without errors after adding accumulation instruction."""
    assert issue_art_recipe is not None, "Recipe parsed to None"
    assert isinstance(issue_art_recipe, dict), (
        f"Recipe root is {type(issue_art_recipe)}, expected dict"
    )


# ---------------------------------------------------------------
# Test 2: content_policy_lesson appears at least 2 times
# ---------------------------------------------------------------
def test_content_policy_lesson_appears_at_least_twice():
    """content_policy_lesson must appear at least 2 times (instruction + JSON example)."""
    raw = _ISSUE_ART_PATH.read_text()
    count = raw.count("content_policy_lesson")
    assert count >= 2, (
        f"'content_policy_lesson' must appear at least 2 times, found {count}"
    )


# ---------------------------------------------------------------
# Test 3: content_policy_notes still referenced
# ---------------------------------------------------------------
def test_content_policy_notes_still_referenced():
    """content_policy_notes must still be referenced in the file (existing context var)."""
    raw = _ISSUE_ART_PATH.read_text()
    assert "content_policy_notes" in raw, (
        "'content_policy_notes' must still be referenced in the file"
    )


# ---------------------------------------------------------------
# Test 4: Accumulation instruction is in generate-panels prompt
# ---------------------------------------------------------------
def test_accumulation_instruction_in_generate_panels_prompt(find_step):
    """The content_policy_lesson accumulation instruction must be in the generate-panels prompt."""
    step = find_step("generate-panels")
    assert step is not None, "generate-panels step not found"
    prompt = step.get("prompt", "")
    assert "CONTENT POLICY ACCUMULATION" in prompt, (
        "generate-panels prompt must contain 'CONTENT POLICY ACCUMULATION' instruction"
    )
    assert "content_policy_lesson" in prompt, (
        "generate-panels prompt must contain 'content_policy_lesson' field reference"
    )


# ---------------------------------------------------------------
# Test 5: JSON example with content_policy_lesson field is present
# ---------------------------------------------------------------
def test_json_example_in_generate_panels_prompt(find_step):
    """The generate-panels prompt must include a JSON example with content_policy_lesson."""
    step = find_step("generate-panels")
    assert step is not None, "generate-panels step not found"
    prompt = step.get("prompt", "")
    # The JSON example should include the content_policy_lesson field with a value
    assert '"content_policy_lesson"' in prompt, (
        "generate-panels prompt must include a JSON example with '\"content_policy_lesson\"' key"
    )
    # Should also have the example value about combat scenes
    assert "Close-up combat scenes" in prompt or "moderation block" in prompt.lower(), (
        "generate-panels prompt must include an example content_policy_lesson value"
    )


# ---------------------------------------------------------------
# Test 6: generate-panels step still has collect: "panel_results"
# ---------------------------------------------------------------
def test_generate_panels_still_collects_panel_results(find_step):
    """generate-panels step must still have collect: 'panel_results'."""
    step = find_step("generate-panels")
    assert step is not None, "generate-panels step not found"
    assert step.get("collect") == "panel_results", (
        f"generate-panels collect must be 'panel_results', got {step.get('collect')}"
    )


# ---------------------------------------------------------------
# Test 7: Accumulation instruction appears BEFORE collect in raw YAML
# ---------------------------------------------------------------
def test_accumulation_before_collect_in_raw_yaml():
    """The CONTENT POLICY ACCUMULATION block must appear before the collect line in raw YAML."""
    raw = _ISSUE_ART_PATH.read_text()
    accumulation_pos = raw.find("CONTENT POLICY ACCUMULATION")
    # Find the collect: "panel_results" that belongs to generate-panels
    collect_pos = raw.find('collect: "panel_results"')
    assert accumulation_pos != -1, (
        "'CONTENT POLICY ACCUMULATION' not found in file"
    )
    assert collect_pos != -1, (
        "'collect: \"panel_results\"' not found in file"
    )
    assert accumulation_pos < collect_pos, (
        "CONTENT POLICY ACCUMULATION must appear before collect: \"panel_results\" in the file"
    )


# ---------------------------------------------------------------
# Test 8: Instruction mentions omitting field if no moderation block
# ---------------------------------------------------------------
def test_omit_or_null_instruction_present(find_step):
    """Prompt must mention omitting field or setting null when no moderation block."""
    step = find_step("generate-panels")
    assert step is not None, "generate-panels step not found"
    prompt = step.get("prompt", "")
    assert "omit" in prompt.lower() or "null" in prompt.lower(), (
        "generate-panels prompt must instruct to omit field or set null when no moderation block"
    )