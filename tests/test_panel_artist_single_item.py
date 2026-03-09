import pytest
from pathlib import Path

pytestmark = pytest.mark.skip(reason="legacy test for pre-v9 recipe")


def _read_panel_artist() -> str:
    return (Path(__file__).parent.parent / "agents" / "panel-artist.md").read_text()


def test_panel_artist_accepts_single_panel_item() -> None:
    """Agent instructions reference {{panel_item}} as the input variable."""
    content = _read_panel_artist()
    assert "{{panel_item}}" in content, (
        "Missing {{panel_item}} input variable reference"
    )


def test_panel_artist_accepts_character_sheet_input() -> None:
    """Agent instructions reference {{character_sheet}} for reference image lookup."""
    content = _read_panel_artist()
    assert "{{character_sheet}}" in content, (
        "Missing {{character_sheet}} input variable reference"
    )


def test_panel_artist_accepts_style_guide_input() -> None:
    """Agent instructions reference {{style_guide}}."""
    content = _read_panel_artist()
    assert "{{style_guide}}" in content, (
        "Missing {{style_guide}} input variable reference"
    )


def test_panel_artist_has_no_internal_loop() -> None:
    """Agent instructions do not contain 'for each panel' internal loop language."""
    content = _read_panel_artist()
    assert "for each panel" not in content.lower(), (
        "Agent still contains an internal panel loop — should be single-item"
    )
    assert "for every panel" not in content.lower(), (
        "Agent still contains an internal panel loop — should be single-item"
    )


def test_panel_artist_retains_self_review_loop() -> None:
    """Agent retains explicit 3-attempt cap for per-panel quality-control self-review."""
    content = _read_panel_artist()
    content_lower = content.lower()
    assert "max 3 attempts" in content_lower or "maximum 3 attempts" in content_lower, (
        "Missing explicit 3-attempt cap for quality-control self-review"
    )
    assert "attempt" in content_lower, "Missing attempt/retry language for self-review"


def test_panel_artist_outputs_single_panel_result() -> None:
    """Output is a single panel result JSON object with required fields."""
    content = _read_panel_artist()
    assert "single panel result" in content.lower(), (
        "Output section must specify a single panel result JSON object"
    )
    assert '"index"' in content, "Output missing index field"
    assert '"path"' in content, "Output missing path field"
    assert '"passed_review"' in content, "Output missing passed_review field"
    assert '"flagged"' in content, "Output missing flagged field"
    assert '"attempts"' in content, "Output missing attempts field"
    assert '"size"' in content, "Output missing size field"
