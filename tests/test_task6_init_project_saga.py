"""Tests for task-6: init-project saga restructure + smart naming.

Validates two changes to session-to-comic.yaml:
1. init-project step creates project + placeholder first issue with v8.0.0 metadata,
   using max_issues instead of saga_issue/previous_issue_id, and default title 'Saga Planning'.
2. discover-sessions step includes smart project naming instructions with
   'suggested_project_name' field.
"""

import pytest
import functools
import pathlib

import yaml

pytestmark = pytest.mark.skip(reason="legacy test for pre-v9 recipe")

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


# =============================================================================
# INIT-PROJECT STEP TESTS
# =============================================================================


class TestInitProjectSaga:
    """Tests for init-project step restructured for saga support."""

    def test_init_project_metadata_has_max_issues(self):
        """init-project prompt must include max_issues in metadata."""
        recipe = _load_recipe()
        step = _find_step(recipe, "init-project")
        assert step is not None, "init-project step not found"
        prompt = step.get("prompt", "")
        assert "max_issues" in prompt, (
            "init-project prompt must include 'max_issues' in metadata"
        )

    def test_init_project_metadata_no_saga_issue(self):
        """init-project prompt must NOT include saga_issue in metadata."""
        recipe = _load_recipe()
        step = _find_step(recipe, "init-project")
        assert step is not None, "init-project step not found"
        prompt = step.get("prompt", "")
        assert "saga_issue" not in prompt, (
            "init-project prompt must NOT include 'saga_issue' — replaced by max_issues"
        )

    def test_init_project_metadata_no_previous_issue_id(self):
        """init-project prompt must NOT include previous_issue_id in metadata."""
        recipe = _load_recipe()
        step = _find_step(recipe, "init-project")
        assert step is not None, "init-project step not found"
        prompt = step.get("prompt", "")
        assert "previous_issue_id" not in prompt, (
            "init-project prompt must NOT include 'previous_issue_id' — replaced by max_issues"
        )

    def test_init_project_default_title_saga_planning(self):
        """init-project default issue_title must be 'Saga Planning'."""
        recipe = _load_recipe()
        step = _find_step(recipe, "init-project")
        assert step is not None, "init-project step not found"
        prompt = step.get("prompt", "")
        assert "Saga Planning" in prompt, (
            "init-project default issue_title must be 'Saga Planning', not 'Comic Strip'"
        )
        assert '"Comic Strip"' not in prompt and "'Comic Strip'" not in prompt, (
            "init-project must NOT use old default 'Comic Strip'"
        )

    def test_init_project_created_by_v8(self):
        """init-project created_by must reference v8.0.0."""
        recipe = _load_recipe()
        step = _find_step(recipe, "init-project")
        assert step is not None, "init-project step not found"
        prompt = step.get("prompt", "")
        assert "v8.0.0" in prompt, "init-project created_by must reference v8.0.0"
        assert "v7.7.0" not in prompt, (
            "init-project must NOT reference old v7.7.0 version"
        )

    def test_init_project_creates_project_and_placeholder_issue(self):
        """init-project prompt must describe creating project + placeholder first issue."""
        recipe = _load_recipe()
        step = _find_step(recipe, "init-project")
        assert step is not None, "init-project step not found"
        prompt = step.get("prompt", "")
        # The prompt should mention creating project and a placeholder/first issue
        assert "project" in prompt.lower(), (
            "init-project prompt must mention creating a project"
        )
        assert "placeholder" in prompt.lower() or "first issue" in prompt.lower(), (
            "init-project prompt must mention creating a placeholder or first issue"
        )


# =============================================================================
# DISCOVER-SESSIONS SMART NAMING TESTS
# =============================================================================


class TestDiscoverSessionsSmartNaming:
    """Tests for smart project naming in discover-sessions step."""

    def test_discover_sessions_has_smart_naming_paragraph(self):
        """discover-sessions prompt must include smart project naming instructions."""
        recipe = _load_recipe()
        step = _find_step(recipe, "discover-sessions")
        assert step is not None, "discover-sessions step not found"
        prompt = step.get("prompt", "")
        # Must mention smart naming or project naming logic
        assert "project name" in prompt.lower() or "project naming" in prompt.lower(), (
            "discover-sessions prompt must include smart project naming instructions"
        )

    def test_discover_sessions_has_suggested_project_name_field(self):
        """discover-sessions prompt must reference 'suggested_project_name' field."""
        recipe = _load_recipe()
        step = _find_step(recipe, "discover-sessions")
        assert step is not None, "discover-sessions step not found"
        prompt = step.get("prompt", "")
        assert "suggested_project_name" in prompt, (
            "discover-sessions prompt must include 'suggested_project_name' field"
        )

    def test_smart_naming_triggers_on_empty_or_default(self):
        """Smart naming instructions must mention triggering when project_name is empty or 'comic-project'."""
        recipe = _load_recipe()
        step = _find_step(recipe, "discover-sessions")
        assert step is not None, "discover-sessions step not found"
        prompt = step.get("prompt", "")
        assert "comic-project" in prompt, (
            "Smart naming must mention the default 'comic-project' name as a trigger condition"
        )

    def test_smart_naming_after_do_not_extract_before_store(self):
        """Smart naming paragraph must be between 'DO NOT extract' and 'Store the consolidated' lines."""
        recipe = _load_recipe()
        step = _find_step(recipe, "discover-sessions")
        assert step is not None, "discover-sessions step not found"
        prompt = step.get("prompt", "")
        do_not_idx = prompt.find("DO NOT extract comic-specific structures")
        store_idx = prompt.find("Store the consolidated research")
        suggested_idx = prompt.find("suggested_project_name")
        assert do_not_idx >= 0, "Could not find 'DO NOT extract' line in prompt"
        assert store_idx >= 0, "Could not find 'Store the consolidated' line in prompt"
        assert suggested_idx >= 0, "Could not find 'suggested_project_name' in prompt"
        assert do_not_idx < suggested_idx < store_idx, (
            f"Smart naming (at {suggested_idx}) must be between "
            f"'DO NOT extract' (at {do_not_idx}) and 'Store the consolidated' (at {store_idx})"
        )
