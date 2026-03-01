from pathlib import Path

PANEL_ARTIST_PATH = Path(__file__).parent.parent / "agents" / "panel-artist.md"


def test_standard_panel_maps_to_landscape() -> None:
    """standard panel size must map to landscape aspect ratio (not square)."""
    content = PANEL_ARTIST_PATH.read_text()
    # The Size Mapping table must map standard to landscape
    assert "standard" in content and "landscape" in content, (
        "Size Mapping must contain both 'standard' and 'landscape'"
    )
    # Find the table and verify the mapping
    lines = content.splitlines()
    standard_lines = [
        line for line in lines if "standard" in line.lower() and "|" in line
    ]
    assert standard_lines, "Size Mapping table must have a 'standard' row"
    standard_row = standard_lines[0]
    assert "landscape" in standard_row, (
        f"standard panel must map to 'landscape', got: {standard_row.strip()}"
    )
    assert "square" not in standard_row, (
        f"standard panel must NOT map to 'square', got: {standard_row.strip()}"
    )
