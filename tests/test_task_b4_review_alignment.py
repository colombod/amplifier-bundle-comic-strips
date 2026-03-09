"""Tests for task B4: Retry/Compose alignment with primary path overlay review.

Validates that issue-retry.yaml and issue-compose.yaml are aligned with
issue-art.yaml's pattern of dedicated review steps instead of inline
review_asset calls in the composition step.

Acceptance criteria:
1. Both recipes still parse as valid YAML.
2. issue-retry.yaml has review-panel-compositions step with depends_on ['inspect-flagged-panels'].
3. issue-retry.yaml has inspect-flagged-panels step with depends_on ['generate-panels'].
4. issue-retry.yaml composition depends_on is ['review-panel-compositions', 'generate-cover'].
5. issue-compose.yaml has review-panel-compositions step with depends_on ['load-existing-assets'].
6. issue-compose.yaml composition depends_on is ['review-panel-compositions'].
7. Neither file's composition prompt contains inline 'review_asset' calls in WORKFLOW step 2/3.
8. Both files reference {{panel_reviews}} in composition prompt.
9. Verification: both files contain review-panel-compositions step.
10. Structurally identical to issue-art.yaml pattern.
"""

import pathlib

import yaml

RECIPE_DIR = pathlib.Path(__file__).parent.parent / "recipes"
RETRY_PATH = RECIPE_DIR / "issue-retry.yaml"
COMPOSE_PATH = RECIPE_DIR / "issue-compose.yaml"
ART_PATH = RECIPE_DIR / "issue-art.yaml"


def _parse(path):
    return yaml.safe_load(path.read_text())


def _get_steps(data):
    """Return flat list of all steps (handles both staged and flat modes)."""
    steps = []
    if "stages" in data:
        for stage in data["stages"]:
            steps.extend(stage.get("steps", []))
    elif "steps" in data:
        steps.extend(data["steps"])
    return steps


def _find_step(steps, step_id):
    for step in steps:
        if step.get("id") == step_id:
            return step
    return None


# ---------------------------------------------------------------
# AC 1: Both recipes still parse as valid YAML
# ---------------------------------------------------------------
class TestYAMLParseable:
    def test_retry_yaml_is_parseable(self):
        data = _parse(RETRY_PATH)
        assert data is not None
        assert isinstance(data, dict)

    def test_compose_yaml_is_parseable(self):
        data = _parse(COMPOSE_PATH)
        assert data is not None
        assert isinstance(data, dict)


# ---------------------------------------------------------------
# AC 2: issue-retry.yaml has review-panel-compositions step
#        with depends_on ['inspect-flagged-panels']
# ---------------------------------------------------------------
class TestRetryReviewPanelCompositions:
    def test_review_panel_compositions_exists(self):
        data = _parse(RETRY_PATH)
        steps = _get_steps(data)
        step = _find_step(steps, "review-panel-compositions")
        assert step is not None, (
            "review-panel-compositions step not found in issue-retry.yaml"
        )

    def test_review_panel_compositions_depends_on_inspect(self):
        data = _parse(RETRY_PATH)
        steps = _get_steps(data)
        step = _find_step(steps, "review-panel-compositions")
        assert step is not None
        assert step.get("depends_on") == ["inspect-flagged-panels"], (
            f"review-panel-compositions depends_on must be ['inspect-flagged-panels'], "
            f"got {step.get('depends_on')}"
        )

    def test_review_panel_compositions_foreach_panel_results(self):
        data = _parse(RETRY_PATH)
        steps = _get_steps(data)
        step = _find_step(steps, "review-panel-compositions")
        assert step is not None
        assert "panel_results" in step.get("foreach", ""), (
            "review-panel-compositions must foreach over panel_results"
        )

    def test_review_panel_compositions_agent(self):
        data = _parse(RETRY_PATH)
        steps = _get_steps(data)
        step = _find_step(steps, "review-panel-compositions")
        assert step is not None
        assert step.get("agent") == "comic-strips:strip-compositor"

    def test_review_panel_compositions_retry(self):
        data = _parse(RETRY_PATH)
        steps = _get_steps(data)
        step = _find_step(steps, "review-panel-compositions")
        assert step is not None
        assert step.get("retry", {}).get("max_attempts") == 2
        assert step.get("retry", {}).get("initial_delay") == 3

    def test_review_panel_compositions_collects_panel_reviews(self):
        data = _parse(RETRY_PATH)
        steps = _get_steps(data)
        step = _find_step(steps, "review-panel-compositions")
        assert step is not None
        assert step.get("collect") == "panel_reviews"

    def test_review_panel_compositions_timeout(self):
        data = _parse(RETRY_PATH)
        steps = _get_steps(data)
        step = _find_step(steps, "review-panel-compositions")
        assert step is not None
        assert step.get("timeout") == 900


# ---------------------------------------------------------------
# AC 3: issue-retry.yaml has inspect-flagged-panels step
#        with depends_on ['generate-panels']
# ---------------------------------------------------------------
class TestRetryInspectFlaggedPanels:
    def test_inspect_flagged_panels_exists(self):
        data = _parse(RETRY_PATH)
        steps = _get_steps(data)
        step = _find_step(steps, "inspect-flagged-panels")
        assert step is not None, (
            "inspect-flagged-panels step not found in issue-retry.yaml"
        )

    def test_inspect_flagged_panels_depends_on_generate_panels(self):
        data = _parse(RETRY_PATH)
        steps = _get_steps(data)
        step = _find_step(steps, "inspect-flagged-panels")
        assert step is not None
        assert step.get("depends_on") == ["generate-panels"], (
            f"inspect-flagged-panels depends_on must be ['generate-panels'], "
            f"got {step.get('depends_on')}"
        )

    def test_inspect_flagged_panels_agent(self):
        data = _parse(RETRY_PATH)
        steps = _get_steps(data)
        step = _find_step(steps, "inspect-flagged-panels")
        assert step is not None
        assert step.get("agent") == "comic-strips:style-curator"

    def test_inspect_flagged_panels_model_role_fast(self):
        data = _parse(RETRY_PATH)
        steps = _get_steps(data)
        step = _find_step(steps, "inspect-flagged-panels")
        assert step is not None
        assert step.get("model_role") == "fast"

    def test_inspect_flagged_panels_output(self):
        data = _parse(RETRY_PATH)
        steps = _get_steps(data)
        step = _find_step(steps, "inspect-flagged-panels")
        assert step is not None
        assert step.get("output") == "flagged_panel_report"

    def test_inspect_flagged_panels_parse_json(self):
        data = _parse(RETRY_PATH)
        steps = _get_steps(data)
        step = _find_step(steps, "inspect-flagged-panels")
        assert step is not None
        assert step.get("parse_json") is True

    def test_inspect_flagged_panels_timeout(self):
        data = _parse(RETRY_PATH)
        steps = _get_steps(data)
        step = _find_step(steps, "inspect-flagged-panels")
        assert step is not None
        assert step.get("timeout") == 300


# ---------------------------------------------------------------
# AC 4: issue-retry.yaml composition depends_on is
#        ['review-panel-compositions', 'generate-cover']
# ---------------------------------------------------------------
class TestRetryCompositionDependencies:
    def test_composition_depends_on_review_and_cover(self):
        data = _parse(RETRY_PATH)
        steps = _get_steps(data)
        comp = _find_step(steps, "composition")
        assert comp is not None
        comp_deps = sorted(comp.get("depends_on", []))
        assert comp_deps == ["generate-cover", "review-panel-compositions"], (
            f"Composition depends_on must be ['review-panel-compositions', 'generate-cover'], "
            f"got {comp.get('depends_on')}"
        )


# ---------------------------------------------------------------
# AC 5: issue-compose.yaml has review-panel-compositions step
#        with depends_on ['load-existing-assets']
# ---------------------------------------------------------------
class TestComposeReviewPanelCompositions:
    def test_review_panel_compositions_exists(self):
        data = _parse(COMPOSE_PATH)
        steps = _get_steps(data)
        step = _find_step(steps, "review-panel-compositions")
        assert step is not None, (
            "review-panel-compositions step not found in issue-compose.yaml"
        )

    def test_review_panel_compositions_depends_on_load_assets(self):
        data = _parse(COMPOSE_PATH)
        steps = _get_steps(data)
        step = _find_step(steps, "review-panel-compositions")
        assert step is not None
        assert step.get("depends_on") == ["load-existing-assets"], (
            f"review-panel-compositions depends_on must be ['load-existing-assets'], "
            f"got {step.get('depends_on')}"
        )

    def test_review_panel_compositions_foreach_panel_uris(self):
        data = _parse(COMPOSE_PATH)
        steps = _get_steps(data)
        step = _find_step(steps, "review-panel-compositions")
        assert step is not None
        assert "existing_assets.panel_uris" in step.get("foreach", ""), (
            "review-panel-compositions must foreach over existing_assets.panel_uris"
        )

    def test_review_panel_compositions_agent(self):
        data = _parse(COMPOSE_PATH)
        steps = _get_steps(data)
        step = _find_step(steps, "review-panel-compositions")
        assert step is not None
        assert step.get("agent") == "comic-strips:strip-compositor"

    def test_review_panel_compositions_retry(self):
        data = _parse(COMPOSE_PATH)
        steps = _get_steps(data)
        step = _find_step(steps, "review-panel-compositions")
        assert step is not None
        assert step.get("retry", {}).get("max_attempts") == 2
        assert step.get("retry", {}).get("initial_delay") == 3

    def test_review_panel_compositions_collects_panel_reviews(self):
        data = _parse(COMPOSE_PATH)
        steps = _get_steps(data)
        step = _find_step(steps, "review-panel-compositions")
        assert step is not None
        assert step.get("collect") == "panel_reviews"

    def test_review_panel_compositions_timeout(self):
        data = _parse(COMPOSE_PATH)
        steps = _get_steps(data)
        step = _find_step(steps, "review-panel-compositions")
        assert step is not None
        assert step.get("timeout") == 900


# ---------------------------------------------------------------
# AC 6: issue-compose.yaml composition depends_on is
#        ['review-panel-compositions']
# ---------------------------------------------------------------
class TestComposeCompositionDependencies:
    def test_composition_depends_on_review(self):
        data = _parse(COMPOSE_PATH)
        steps = _get_steps(data)
        comp = _find_step(steps, "composition")
        assert comp is not None
        assert comp.get("depends_on") == ["review-panel-compositions"], (
            f"Composition depends_on must be ['review-panel-compositions'], "
            f"got {comp.get('depends_on')}"
        )


# ---------------------------------------------------------------
# AC 7: Neither file's composition prompt contains inline
#        'review_asset' calls in WORKFLOW section
# ---------------------------------------------------------------
class TestNoInlineReviewAsset:
    def _get_workflow_section(self, prompt):
        """Extract the WORKFLOW section from a composition prompt."""
        lines = prompt.split("\n")
        in_workflow = False
        workflow_lines = []
        for line in lines:
            if "WORKFLOW:" in line:
                in_workflow = True
                continue
            if in_workflow:
                workflow_lines.append(line)
        return "\n".join(workflow_lines)

    def test_retry_composition_no_inline_review_asset(self):
        data = _parse(RETRY_PATH)
        steps = _get_steps(data)
        comp = _find_step(steps, "composition")
        assert comp is not None
        workflow = self._get_workflow_section(comp.get("prompt", ""))
        assert "review_asset" not in workflow, (
            "issue-retry.yaml composition WORKFLOW must not contain inline review_asset calls"
        )

    def test_compose_composition_no_inline_review_asset(self):
        data = _parse(COMPOSE_PATH)
        steps = _get_steps(data)
        comp = _find_step(steps, "composition")
        assert comp is not None
        workflow = self._get_workflow_section(comp.get("prompt", ""))
        assert "review_asset" not in workflow, (
            "issue-compose.yaml composition WORKFLOW must not contain inline review_asset calls"
        )


# ---------------------------------------------------------------
# AC 8: Both files reference {{panel_reviews}} in composition prompt
# ---------------------------------------------------------------
class TestPanelReviewsReference:
    def test_retry_composition_references_panel_reviews(self):
        data = _parse(RETRY_PATH)
        steps = _get_steps(data)
        comp = _find_step(steps, "composition")
        assert comp is not None
        assert "panel_reviews" in comp.get("prompt", ""), (
            "issue-retry.yaml composition prompt must reference {{panel_reviews}}"
        )

    def test_compose_composition_references_panel_reviews(self):
        data = _parse(COMPOSE_PATH)
        steps = _get_steps(data)
        comp = _find_step(steps, "composition")
        assert comp is not None
        assert "panel_reviews" in comp.get("prompt", ""), (
            "issue-compose.yaml composition prompt must reference {{panel_reviews}}"
        )


# ---------------------------------------------------------------
# AC 9: Verification script B4 checks pass
#        (both files contain review-panel-compositions)
# ---------------------------------------------------------------
class TestVerificationB4:
    def test_retry_contains_review_panel_compositions(self):
        content = RETRY_PATH.read_text()
        assert "review-panel-compositions" in content

    def test_compose_contains_review_panel_compositions(self):
        content = COMPOSE_PATH.read_text()
        assert "review-panel-compositions" in content


# ---------------------------------------------------------------
# AC 10: Structurally identical to issue-art.yaml pattern
# ---------------------------------------------------------------
class TestStructuralAlignment:
    def test_retry_step_order(self):
        """Expected step order: load-existing-assets, generate-panels, generate-cover,
        inspect-flagged-panels, review-panel-compositions, composition."""
        data = _parse(RETRY_PATH)
        steps = _get_steps(data)
        step_ids = [s["id"] for s in steps]
        expected = [
            "load-existing-assets",
            "generate-panels",
            "generate-cover",
            "inspect-flagged-panels",
            "review-panel-compositions",
            "composition",
        ]
        assert step_ids == expected, (
            f"issue-retry.yaml step order must be {expected}, got {step_ids}"
        )

    def test_compose_step_order(self):
        """Expected step order: load-existing-assets, review-panel-compositions, composition."""
        data = _parse(COMPOSE_PATH)
        steps = _get_steps(data)
        step_ids = [s["id"] for s in steps]
        expected = [
            "load-existing-assets",
            "review-panel-compositions",
            "composition",
        ]
        assert step_ids == expected, (
            f"issue-compose.yaml step order must be {expected}, got {step_ids}"
        )

    def test_compose_uses_flat_steps_not_stages(self):
        """issue-compose.yaml must use top-level 'steps:' not 'stages:'."""
        data = _parse(COMPOSE_PATH)
        assert "steps" in data, "issue-compose.yaml must use top-level 'steps:'"
        assert "stages" not in data, "issue-compose.yaml must NOT use 'stages:'"

    def test_retry_review_prompt_calls_review_asset(self):
        """review-panel-compositions in retry must call comic_create review_asset."""
        data = _parse(RETRY_PATH)
        steps = _get_steps(data)
        step = _find_step(steps, "review-panel-compositions")
        assert step is not None
        prompt = step.get("prompt", "")
        assert "review_asset" in prompt, (
            "review-panel-compositions prompt must call review_asset"
        )

    def test_compose_review_prompt_calls_review_asset(self):
        """review-panel-compositions in compose must call comic_create review_asset."""
        data = _parse(COMPOSE_PATH)
        steps = _get_steps(data)
        step = _find_step(steps, "review-panel-compositions")
        assert step is not None
        prompt = step.get("prompt", "")
        assert "review_asset" in prompt, (
            "review-panel-compositions prompt must call review_asset"
        )

    def test_retry_all_steps_have_required_fields(self):
        """Every step must have id, agent, prompt, and output or collect."""
        data = _parse(RETRY_PATH)
        for step in _get_steps(data):
            sid = step.get("id", "<unknown>")
            assert "id" in step, "Step missing 'id'"
            assert "agent" in step, f"Step '{sid}' missing 'agent'"
            assert "prompt" in step, f"Step '{sid}' missing 'prompt'"
            has_output = "output" in step or "collect" in step
            assert has_output, f"Step '{sid}' missing both 'output' and 'collect'"

    def test_compose_all_steps_have_required_fields(self):
        """Every step must have id, agent, prompt, and output or collect."""
        data = _parse(COMPOSE_PATH)
        for step in _get_steps(data):
            sid = step.get("id", "<unknown>")
            assert "id" in step, "Step missing 'id'"
            assert "agent" in step, f"Step '{sid}' missing 'agent'"
            assert "prompt" in step, f"Step '{sid}' missing 'prompt'"
            has_output = "output" in step or "collect" in step
            assert has_output, f"Step '{sid}' missing both 'output' and 'collect'"
