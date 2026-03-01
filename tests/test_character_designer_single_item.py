from pathlib import Path


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


def test_character_designer_has_no_internal_loop() -> None:
    """Agent instructions do not contain 'for each character' or 'for EACH character' loops."""
    content = _read_character_designer()
    assert "for each character" not in content.lower(), (
        "Agent still contains an internal character loop — should be single-item"
    )
    assert "for EACH selected character" not in content, (
        "Agent still contains an internal character loop — should be single-item"
    )


def test_character_designer_outputs_single_entry_not_array() -> None:
    """Output format is a single JSON object, not a characters[] array."""
    content = _read_character_designer()
    # Should NOT describe output as a wrapped array
    assert '"characters":' not in content or "single" in content.lower(), (
        "Output format appears to be a characters[] array; should be a single entry"
    )
    # Should describe single entry output
    assert (
        "single" in content.lower()
        or "one character" in content.lower()
        or "{{character_item}}" in content
    ), "No indication this agent handles a single character"
