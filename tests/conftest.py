"""Shared fixtures for issue-art recipe tests."""

import pathlib

import pytest
import yaml

_ISSUE_ART_PATH = pathlib.Path(__file__).parent.parent / "recipes" / "issue-art.yaml"

EXPECTED_STEP_IDS = [
    "generate-panels",
    "inspect-flagged-panels",
    "generate-cover",
    "review-panel-compositions",
    "composition",
]


@pytest.fixture(scope="module")
def issue_art_recipe():
    """Parse issue-art.yaml once per test module."""
    return yaml.safe_load(_ISSUE_ART_PATH.read_text())


@pytest.fixture(scope="module")
def issue_art_steps(issue_art_recipe):
    """Flat list of all steps across all stages."""
    steps = []
    for stage in issue_art_recipe.get("stages", []):
        steps.extend(stage.get("steps", []))
    return steps


@pytest.fixture(scope="module")
def find_step(issue_art_steps):
    """Return a lookup function: find_step(step_id) -> dict | None."""

    def _find(step_id):
        for step in issue_art_steps:
            if step.get("id") == step_id:
                return step
        return None

    return _find
