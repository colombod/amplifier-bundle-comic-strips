import pytest
from pathlib import Path

pytestmark = pytest.mark.skip(reason="legacy test for pre-v9 recipe")


def _read_character_designer() -> str:
    return (
        Path(__file__).parent.parent / "agents" / "character-designer.md"
    ).read_text()


def test_character_designer_accepts_single_character_item() -> None:
    """Agent instructions reference {{character_item}} as the input variable."""
    content = _read_character_designer()
    assert "{{character_item}}" in content, (
        "Missing {{character_item}} input variable reference"
    )


def test_character_designer_accepts_style_guide_input() -> None:
    """Agent instructions reference {{style_guide}} as the second input variable."""
    content = _read_character_designer()
    assert "{{style_guide}}" in content, (
        "Missing {{style_guide}} input variable reference"
    )


def test_character_designer_has_no_internal_loop() -> None:
    """Agent instructions do not contain any internal character loop language."""
    content = _read_character_designer()
    assert "for each character" not in content.lower(), (
        "Agent still contains an internal character loop — should be single-item"
    )
    assert "for every character" not in content.lower(), (
        "Agent still contains an internal character loop — should be single-item"
    )


def test_character_designer_outputs_single_entry_not_array() -> None:
    """Output format is a single JSON object, not a characters[] array."""
    content = _read_character_designer()
    assert '{"characters":' not in content and '"characters": [' not in content, (
        "Output format contains a characters[] array; should be a single entry"
    )
    assert "single character sheet entry" in content.lower(), (
        "Output section should describe a single character sheet entry"
    )


def test_character_designer_output_fields() -> None:
    """Output JSON documents all 4 synthesized fields that downstream agents depend on."""
    content = _read_character_designer()
    for field in [
        "visual_traits",
        "team_markers",
        "distinctive_features",
        "reference_image",
    ]:
        assert f'"{field}"' in content, (
            f"Output contract missing required field: {field!r}"
        )
