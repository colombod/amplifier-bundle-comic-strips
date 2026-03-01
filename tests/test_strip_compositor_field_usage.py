"""
Tests that strip-compositor reads the correct fields from character sheet entries.

character-designer outputs:
  - visual_traits     — key visual characteristics
  - distinctive_features — unique identifying features
  - team_markers      — bundle-affiliation visual elements
  - reference_image   — file path to generated PNG

It does NOT output 'description'. That was the original storyboard field.
strip-compositor must read the structured fields that character-designer actually produces.
"""

from pathlib import Path

STRIP_COMPOSITOR_PATH = Path(__file__).parent.parent / "agents" / "strip-compositor.md"


def test_strip_compositor_reads_visual_traits_from_character_sheet() -> None:
    """Strip-compositor Process step must reference visual_traits and distinctive_features."""
    body = STRIP_COMPOSITOR_PATH.read_text()
    # Scope to the Process section (bounded to the next top-level ## heading)
    marker = "## Process"
    assert marker in body, f"Section '{marker}' not found in strip-compositor.md"
    start = body.index(marker)
    next_section = body.find("\n## ", start + len(marker))
    process_section = body[start:next_section] if next_section != -1 else body[start:]
    # Both fields must be referenced in the Process section (where character data is read)
    assert "visual_traits" in process_section, (
        "Process step must reference 'visual_traits' from character_sheet entries"
    )
    assert "distinctive_features" in process_section, (
        "Process step must reference 'distinctive_features' from character_sheet entries"
    )


def test_strip_compositor_character_intro_does_not_rely_on_description_field():
    """The Character Intro Page Assembly section must NOT instruct reading 'description'.

    The 'description' field does not exist in character-designer output.
    Using it would silently produce empty/None values on the character intro page.
    """
    content = STRIP_COMPOSITOR_PATH.read_text()

    # Find the Character Intro Page Assembly section
    assembly_section_start = content.find("## Character Intro Page Assembly")
    assert assembly_section_start != -1, (
        "Expected to find '## Character Intro Page Assembly' section in strip-compositor.md"
    )

    # Extract from that section to end of file (or next ## section)
    assembly_section = content[assembly_section_start:]
    next_section = assembly_section.find("\n## ", 1)
    if next_section != -1:
        assembly_section = assembly_section[:next_section]

    # The assembly section should NOT instruct reading a bare 'description' field
    # It should use visual_traits and/or distinctive_features instead
    assert (
        "visual_traits" in assembly_section
        or "distinctive_features" in assembly_section
    ), (
        "The 'Character Intro Page Assembly' section must reference visual_traits "
        "or distinctive_features (the actual character-designer output fields), "
        "not 'description' which only exists on storyboard entries."
    )
    # Negative guard: the HTML template must not use {character_description}
    # Note: "description" appears in line 499 as a prohibition text — use the
    # template variable form to avoid false failures on the prohibition text itself
    assert "{character_description}" not in assembly_section, (
        "Assembly section uses {character_description} template variable — "
        "use visual_traits/distinctive_features instead"
    )
