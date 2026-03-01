from pathlib import Path


def _read_panel_artist() -> str:
    return (Path(__file__).parent.parent / "agents" / "panel-artist.md").read_text()


def _single_item_section(content: str) -> str:
    """Use full content — panel-artist is entirely single-item scoped."""
    return content


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
    """Agent retains 3-attempt self-review per panel (quality control, not iteration)."""
    content = _read_panel_artist()
    assert "3" in content or "three" in content.lower(), (
        "Missing 3-attempt self-review loop (per-panel quality control must be retained)"
    )
    assert "attempt" in content.lower(), (
        "Missing attempt/retry language for self-review"
    )


def test_panel_artist_outputs_single_panel_result() -> None:
    """Output is a single panel result JSON object."""
    content = _read_panel_artist()
    assert "single" in content.lower() or "{{panel_item}}" in content, (
        "No indication this agent handles a single panel"
    )
    assert '"index"' in content, "Output missing index field"
    assert '"path"' in content, "Output missing path field"
    assert '"passed_review"' in content, "Output missing passed_review field"
    assert '"flagged"' in content, "Output missing flagged field"
