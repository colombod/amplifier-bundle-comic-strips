"""Tests for task-7: Rewrite Step 3 — saga storyboard in session-to-comic.yaml.

Validates that the storyboard step produces a saga plan with issues[] array
and character_roster[] with per_issue evolution maps.

Acceptance criteria:
  AC1: Step id="storyboard" exists with agent="comic-strips:storyboard-writer"
  AC2: output="storyboard", parse_json=true, timeout=1800
  AC3: Two-phase prompt — Phase 1 delegates to stories:content-strategist and stories:case-study-writer
  AC4: Phase 2 translates narrative into multi-issue saga
  AC5: Saga budget params: max_issues, max_characters, max_pages, panels_per_page
  AC6: Saga planning rules: issue arcs, cliffhangers, recaps, shared character roster, character evolution
  AC7: Cross-project character discovery via comic_character(action='search', style='{{style}}')
  AC8: Smart project naming — suggested_project_name in output
  AC9: Mandatory list_layouts call
  AC10: Output JSON references saga_plan with issues[] array
  AC11: Output JSON references character_roster[] with per_issue field
  AC12: Store result as comic asset
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


def _storyboard_step() -> dict:
    recipe = _load_recipe()
    step = _find_step(recipe, "storyboard")
    assert step is not None, "storyboard step not found in recipe"
    return step


def _storyboard_prompt() -> str:
    return _storyboard_step().get("prompt", "")


# =============================================================================
# AC1 & AC2: STEP BASICS
# =============================================================================


class TestStoryboardStepBasics:
    """AC1 + AC2: Step exists with correct agent, output, parse_json, timeout."""

    def test_step_exists(self):
        """Storyboard step must exist in the recipe."""
        step = _storyboard_step()
        assert step["id"] == "storyboard"

    def test_agent_is_storyboard_writer(self):
        """AC1: Uses comic-strips:storyboard-writer agent."""
        step = _storyboard_step()
        assert step["agent"] == "comic-strips:storyboard-writer"

    def test_output_is_storyboard(self):
        """AC2: output field is 'storyboard'."""
        step = _storyboard_step()
        assert step["output"] == "storyboard"

    def test_parse_json_is_true(self):
        """AC2: parse_json is true."""
        step = _storyboard_step()
        assert step.get("parse_json") is True

    def test_timeout_is_1800(self):
        """AC2: timeout is 1800."""
        step = _storyboard_step()
        assert step.get("timeout") == 1800


# =============================================================================
# AC3: TWO-PHASE PROMPT — DELEGATION
# =============================================================================


class TestTwoPhasePrompt:
    """AC3: Phase 1 delegates narrative creation to stories agents."""

    def test_phase1_label_present(self):
        """Prompt must clearly label Phase 1."""
        prompt = _storyboard_prompt()
        assert "Phase 1" in prompt

    def test_phase2_label_present(self):
        """Prompt must clearly label Phase 2."""
        prompt = _storyboard_prompt()
        assert "Phase 2" in prompt

    def test_delegates_to_content_strategist(self):
        """AC3: Phase 1 delegates to stories:content-strategist."""
        prompt = _storyboard_prompt()
        assert "stories:content-strategist" in prompt

    def test_delegates_to_case_study_writer(self):
        """AC3: Phase 1 delegates to stories:case-study-writer."""
        prompt = _storyboard_prompt()
        assert "stories:case-study-writer" in prompt


# =============================================================================
# AC4: MULTI-ISSUE SAGA TRANSLATION
# =============================================================================


class TestSagaTranslation:
    """AC4: Phase 2 translates narrative into multi-issue saga."""

    def test_mentions_multi_issue(self):
        """Phase 2 must reference multi-issue saga planning."""
        prompt = _storyboard_prompt().lower()
        assert "multi-issue" in prompt or ("issue" in prompt and "saga" in prompt)

    def test_mentions_saga(self):
        """Prompt must use the word 'saga'."""
        prompt = _storyboard_prompt().lower()
        assert "saga" in prompt


# =============================================================================
# AC5: SAGA BUDGET PARAMS
# =============================================================================


class TestSagaBudget:
    """AC5: Saga budget includes max_issues, max_characters, max_pages, panels_per_page."""

    def test_max_issues_in_budget(self):
        """Saga budget must include max_issues."""
        prompt = _storyboard_prompt()
        assert "max_issues" in prompt

    def test_max_characters_in_budget(self):
        """Saga budget must include max_characters."""
        prompt = _storyboard_prompt()
        assert "max_characters" in prompt

    def test_max_pages_in_budget(self):
        """Saga budget must include max_pages."""
        prompt = _storyboard_prompt()
        assert "max_pages" in prompt

    def test_panels_per_page_in_budget(self):
        """Saga budget must include panels_per_page."""
        prompt = _storyboard_prompt()
        assert "panels_per_page" in prompt


# =============================================================================
# AC6: SAGA PLANNING RULES
# =============================================================================


class TestSagaPlanningRules:
    """AC6: Saga planning rules include issue arcs, cliffhangers, recaps, shared roster, evolution."""

    def test_issue_arcs(self):
        """Saga planning must discuss issue arcs."""
        prompt = _storyboard_prompt().lower()
        assert "arc" in prompt

    def test_cliffhangers(self):
        """Saga planning must discuss cliffhangers."""
        prompt = _storyboard_prompt().lower()
        assert "cliffhanger" in prompt

    def test_recaps(self):
        """Saga planning must discuss recaps."""
        prompt = _storyboard_prompt().lower()
        assert "recap" in prompt

    def test_shared_character_roster(self):
        """Saga planning must discuss shared character roster."""
        prompt = _storyboard_prompt().lower()
        assert "character roster" in prompt or "character_roster" in prompt

    def test_character_evolution(self):
        """Saga planning must discuss character evolution."""
        prompt = _storyboard_prompt().lower()
        assert "character evolution" in prompt or "evolution" in prompt


# =============================================================================
# AC7: CROSS-PROJECT CHARACTER DISCOVERY
# =============================================================================


class TestCharacterDiscovery:
    """AC7: Cross-project character discovery via comic_character tool."""

    def test_comic_character_search_call(self):
        """Prompt must include comic_character(action='search') call."""
        prompt = _storyboard_prompt()
        assert "comic_character" in prompt
        assert "action='search'" in prompt or 'action="search"' in prompt

    def test_character_search_uses_style(self):
        """Character search must filter by style."""
        prompt = _storyboard_prompt()
        assert "style=" in prompt and "{{style}}" in prompt


# =============================================================================
# AC8: SMART PROJECT NAMING
# =============================================================================


class TestSmartProjectNaming:
    """AC8: Output includes suggested_project_name."""

    def test_suggested_project_name_in_output(self):
        """Output JSON must include suggested_project_name."""
        prompt = _storyboard_prompt()
        assert "suggested_project_name" in prompt


# =============================================================================
# AC9: MANDATORY LIST_LAYOUTS CALL
# =============================================================================


class TestMandatoryListLayouts:
    """AC9: Prompt includes mandatory list_layouts call."""

    def test_list_layouts_mentioned(self):
        """Prompt must require calling list_layouts."""
        prompt = _storyboard_prompt()
        assert "list_layouts" in prompt


# =============================================================================
# AC10: OUTPUT JSON — saga_plan WITH issues[]
# =============================================================================


class TestSagaPlanOutput:
    """AC10: Output JSON includes saga_plan with issues[] array."""

    def test_saga_plan_in_output(self):
        """Output JSON must include saga_plan."""
        prompt = _storyboard_prompt()
        assert "saga_plan" in prompt

    def test_saga_plan_has_total_issues(self):
        """saga_plan must include total_issues."""
        prompt = _storyboard_prompt()
        assert "total_issues" in prompt

    def test_saga_plan_has_arc_summary(self):
        """saga_plan must include arc_summary."""
        prompt = _storyboard_prompt()
        assert "arc_summary" in prompt

    def test_saga_plan_has_issues_array(self):
        """saga_plan must include issues[] array."""
        prompt = _storyboard_prompt()
        assert "issues" in prompt
        # Must reference issues as an array/list structure
        assert "issue_number" in prompt

    def test_issues_have_title(self):
        """Each issue in issues[] must have title."""
        prompt = _storyboard_prompt()
        # issue title is part of the issues[] structure
        assert "title" in prompt

    def test_issues_have_character_list(self):
        """Each issue in issues[] must have character_list."""
        prompt = _storyboard_prompt()
        assert "character_list" in prompt

    def test_issues_have_panel_list(self):
        """Each issue in issues[] must have panel_list."""
        prompt = _storyboard_prompt()
        assert "panel_list" in prompt

    def test_issues_have_page_layouts(self):
        """Each issue in issues[] must have page_layouts."""
        prompt = _storyboard_prompt()
        assert "page_layouts" in prompt

    def test_issues_have_page_count(self):
        """Each issue in issues[] must have page_count."""
        prompt = _storyboard_prompt()
        assert "page_count" in prompt

    def test_issues_have_panel_count(self):
        """Each issue in issues[] must have panel_count."""
        prompt = _storyboard_prompt()
        assert "panel_count" in prompt

    def test_issues_have_cliffhanger(self):
        """Each issue in issues[] must have cliffhanger field."""
        prompt = _storyboard_prompt()
        # cliffhanger as a per-issue field
        assert "cliffhanger" in prompt

    def test_issues_have_recap(self):
        """Each issue in issues[] must have recap field."""
        prompt = _storyboard_prompt()
        assert "recap" in prompt


# =============================================================================
# AC11: OUTPUT JSON — character_roster[] WITH per_issue
# =============================================================================


class TestCharacterRosterOutput:
    """AC11: Output JSON includes character_roster[] with per_issue evolution maps."""

    def test_character_roster_in_output(self):
        """Output JSON must include character_roster."""
        prompt = _storyboard_prompt()
        assert "character_roster" in prompt

    def test_character_roster_has_name(self):
        """character_roster entries must have name."""
        prompt = _storyboard_prompt()
        # These fields must appear in the context of the character_roster structure
        assert "name" in prompt

    def test_character_roster_has_char_slug(self):
        """character_roster entries must have char_slug."""
        prompt = _storyboard_prompt()
        assert "char_slug" in prompt

    def test_character_roster_has_role(self):
        """character_roster entries must have role."""
        prompt = _storyboard_prompt()
        assert "role" in prompt

    def test_character_roster_has_type(self):
        """character_roster entries must have type."""
        prompt = _storyboard_prompt()
        assert "type" in prompt

    def test_character_roster_has_bundle(self):
        """character_roster entries must have bundle."""
        prompt = _storyboard_prompt()
        assert "bundle" in prompt

    def test_character_roster_has_first_appearance(self):
        """character_roster entries must have first_appearance."""
        prompt = _storyboard_prompt()
        assert "first_appearance" in prompt

    def test_character_roster_has_existing_uri(self):
        """character_roster entries must have existing_uri."""
        prompt = _storyboard_prompt()
        assert "existing_uri" in prompt

    def test_character_roster_has_needs_redesign(self):
        """character_roster entries must have needs_redesign."""
        prompt = _storyboard_prompt()
        assert "needs_redesign" in prompt

    def test_character_roster_has_visual_traits(self):
        """character_roster entries must have visual_traits."""
        prompt = _storyboard_prompt()
        assert "visual_traits" in prompt

    def test_character_roster_has_description(self):
        """character_roster entries must have description."""
        prompt = _storyboard_prompt()
        assert "description" in prompt

    def test_character_roster_has_backstory(self):
        """character_roster entries must have backstory."""
        prompt = _storyboard_prompt()
        assert "backstory" in prompt

    def test_character_roster_has_metadata(self):
        """character_roster entries must have metadata."""
        prompt = _storyboard_prompt()
        assert "metadata" in prompt

    def test_character_roster_has_per_issue(self):
        """character_roster entries must have per_issue evolution map."""
        prompt = _storyboard_prompt()
        assert "per_issue" in prompt


# =============================================================================
# AC12: STORE AS COMIC ASSET
# =============================================================================


class TestStoreAsComicAsset:
    """AC12: Storyboard result is stored as a comic asset."""

    def test_comic_asset_store_call(self):
        """Prompt must include comic_asset(action='store') call."""
        prompt = _storyboard_prompt()
        assert "comic_asset" in prompt
        assert "action='store'" in prompt or 'action="store"' in prompt
