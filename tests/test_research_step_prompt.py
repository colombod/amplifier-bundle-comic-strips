"""Tests for the research step prompt in session-to-comic.yaml.

Validates that:
1. Research step prompt references {{session_data}} (not {{session_file}})
2. Research step prompt includes comic_asset(action='get', uri='{{session_data}}', include='full') call
3. The 'Extract structured data for comic strip creation:' line follows the comic_asset line
"""

import functools
import pathlib

import yaml

RECIPE_PATH = pathlib.Path(__file__).parent.parent / "recipes" / "session-to-comic.yaml"


@functools.cache
def _load_recipe() -> dict:
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
    for step in _get_all_steps(recipe):
        if step.get("id") == step_id:
            return step
    return None


def test_research_prompt_references_session_data():
    """Research step prompt must reference {{session_data}}, not {{session_file}}."""
    recipe = _load_recipe()
    step = _find_step(recipe, "research")
    assert step is not None, "Step 'research' not found in recipe"
    prompt = step.get("prompt", "")
    assert "{{session_data}}" in prompt, (
        f"Research prompt must reference '{{{{session_data}}}}', but it doesn't.\n"
        f"First 200 chars: {prompt[:200]!r}"
    )


def test_research_prompt_does_not_reference_session_file():
    """Research step prompt must NOT reference {{session_file}} directly."""
    recipe = _load_recipe()
    step = _find_step(recipe, "research")
    assert step is not None, "Step 'research' not found in recipe"
    prompt = step.get("prompt", "")
    assert "{{session_file}}" not in prompt, (
        "Research prompt must not reference '{{session_file}}' - "
        "it should use '{{session_data}}' instead"
    )


def test_research_prompt_includes_comic_asset_get():
    """Research step prompt must include comic_asset get call for session_data."""
    recipe = _load_recipe()
    step = _find_step(recipe, "research")
    assert step is not None, "Step 'research' not found in recipe"
    prompt = step.get("prompt", "")
    expected = "comic_asset(action='get', uri='{{session_data}}', include='full')"
    assert expected in prompt, (
        f"Research prompt must include:\n  {expected}\n"
        f"First 400 chars of prompt: {prompt[:400]!r}"
    )


def test_research_prompt_structure():
    """Research prompt must have session_data reference, comic_asset call, then Extract line in order."""
    recipe = _load_recipe()
    step = _find_step(recipe, "research")
    assert step is not None, "Step 'research' not found in recipe"
    prompt = step.get("prompt", "")

    # Find positions of key elements
    session_data_pos = prompt.find("{{session_data}}")
    comic_asset_pos = prompt.find("comic_asset(action='get'")
    extract_pos = prompt.find("Extract structured data for comic strip creation:")

    assert session_data_pos >= 0, "Missing {{session_data}} reference"
    assert comic_asset_pos >= 0, "Missing comic_asset call"
    assert extract_pos >= 0, "Missing 'Extract structured data' line"

    assert session_data_pos < comic_asset_pos < extract_pos, (
        f"Elements must appear in order: session_data({session_data_pos}) < "
        f"comic_asset({comic_asset_pos}) < extract({extract_pos})"
    )
