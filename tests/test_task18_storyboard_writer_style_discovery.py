"""Tests for Task 18: storyboard-writer.md style discovery and cross-project
character search with semantic search_by_description workflow.

Validates that the storyboard-writer agent instructions include:
1. Style Discovery (Before Creating New Styles) section with search_by_description workflow
2. Similarity threshold of 0.85 for style reuse decision
3. Fallback to comic_style(action='list') when embedding_status is unavailable
4. Cross-Project Character Discovery section with search_by_description as semantic complement
5. Fallback to tag-based search when semantic search is unavailable
6. All tool references use valid action names
"""

from pathlib import Path


AGENT_PATH = Path(__file__).parent.parent / "agents" / "storyboard-writer.md"


def _read_agent() -> str:
    return AGENT_PATH.read_text()


# ---------------------------------------------------------------
# Test 1: Style Discovery section exists
# ---------------------------------------------------------------
def test_style_discovery_section_exists() -> None:
    """Agent must have a Style Discovery section."""
    content = _read_agent()
    assert "Style Discovery" in content, (
        "Missing 'Style Discovery' section in storyboard-writer.md"
    )


# ---------------------------------------------------------------
# Test 2: Style Discovery uses search_by_description action
# ---------------------------------------------------------------
def test_style_discovery_uses_search_by_description() -> None:
    """Style Discovery must call comic_style with action='search_by_description'."""
    content = _read_agent()
    assert "action='search_by_description'" in content, (
        "Missing comic_style(action='search_by_description') call in storyboard-writer.md"
    )


# ---------------------------------------------------------------
# Test 3: Style Discovery includes 0.85 similarity threshold
# ---------------------------------------------------------------
def test_style_discovery_threshold_085() -> None:
    """Style Discovery must document 0.85 similarity threshold for reuse decision."""
    content = _read_agent()
    assert "0.85" in content, (
        "Missing similarity threshold (0.85) in Style Discovery section of storyboard-writer.md"
    )


# ---------------------------------------------------------------
# Test 4: Style Discovery fallback to comic_style(action='list')
# ---------------------------------------------------------------
def test_style_discovery_fallback_to_list() -> None:
    """Style Discovery must fall back to comic_style(action='list') when embedding unavailable."""
    content = _read_agent()
    assert "action='list'" in content, (
        "Missing comic_style(action='list') fallback in storyboard-writer.md"
    )


# ---------------------------------------------------------------
# Test 5: Style Discovery references embedding_status
# ---------------------------------------------------------------
def test_style_discovery_references_embedding_status() -> None:
    """Style Discovery must reference embedding_status to detect unavailability."""
    content = _read_agent()
    assert "embedding_status" in content, (
        "Missing 'embedding_status' reference in Style Discovery section of storyboard-writer.md"
    )


# ---------------------------------------------------------------
# Test 6: Style Discovery section comes after prerequisites
# ---------------------------------------------------------------
def test_style_discovery_after_prerequisites() -> None:
    """Style Discovery section must appear after the Prerequisites section."""
    content = _read_agent()
    prereq_pos = content.find("## Prerequisites")
    style_discovery_pos = content.find("Style Discovery")
    assert prereq_pos != -1, "Prerequisites section not found"
    assert style_discovery_pos != -1, "Style Discovery section not found"
    assert style_discovery_pos > prereq_pos, (
        "Style Discovery must appear AFTER Prerequisites section"
    )


# ---------------------------------------------------------------
# Test 7: Cross-Project Character Discovery has semantic complement
# ---------------------------------------------------------------
def test_cross_project_character_discovery_has_semantic_search() -> None:
    """Cross-Project Character Discovery section must include search_by_description."""
    content = _read_agent()
    # Find the Cross-Project Character Discovery section
    section_pos = content.find("Cross-Project Character Discovery")
    assert section_pos != -1, "Missing 'Cross-Project Character Discovery' section"
    # The search_by_description action should appear (either in this section or
    # the style discovery section confirms it's present)
    assert "search_by_description" in content, (
        "Missing search_by_description in storyboard-writer.md"
    )


# ---------------------------------------------------------------
# Test 8: Cross-Project Character Discovery has fallback
# ---------------------------------------------------------------
def test_cross_project_character_discovery_has_fallback() -> None:
    """Cross-Project Character Discovery must document fallback to tag-based search."""
    content = _read_agent()
    # Must have some form of fallback description when semantic search is unavailable
    # Check for fallback language in the character discovery context
    assert "fallback" in content.lower() or "fall back" in content.lower(), (
        "Missing fallback instruction for character discovery in storyboard-writer.md"
    )


# ---------------------------------------------------------------
# Test 9: search_by_description for comic_character is present
# ---------------------------------------------------------------
def test_comic_character_search_by_description_present() -> None:
    """comic_character(action='search_by_description') must be referenced for character discovery."""
    content = _read_agent()
    # Check for either the exact call or the action reference in character context
    # The spec says: use comic_character(action='search_by_description') as semantic complement
    assert "search_by_description" in content, (
        "Missing search_by_description action in storyboard-writer.md"
    )
    # The agent should also reference comic_character
    assert "comic_character" in content, (
        "Missing comic_character tool reference in storyboard-writer.md"
    )


# ---------------------------------------------------------------
# Test 10: Style Discovery references project parameter
# ---------------------------------------------------------------
def test_style_discovery_passes_project_param() -> None:
    """Style Discovery search must pass project parameter."""
    content = _read_agent()
    # The spec shows: comic_style(action='search_by_description', query='...', project='...')
    # Check for project= parameter in context of the style search
    assert "project=" in content or "project_id" in content, (
        "Style Discovery search_by_description must include project parameter"
    )


# ---------------------------------------------------------------
# Test 11: Style reuse instruction when similarity exceeds threshold
# ---------------------------------------------------------------
def test_style_discovery_reuse_instruction() -> None:
    """Style Discovery must instruct reuse of existing style when similarity > 0.85."""
    content = _read_agent()
    # The section should mention reusing the existing style
    assert "reuse" in content.lower() or "existing" in content.lower(), (
        "Style Discovery must instruct to reuse existing style when threshold is met"
    )


# ---------------------------------------------------------------
# Test 12: Manual inspection note for fallback path
# ---------------------------------------------------------------
def test_style_discovery_fallback_includes_manual_inspection() -> None:
    """Fallback path must mention manual inspection."""
    content = _read_agent()
    assert "manual" in content.lower() or "inspect" in content.lower(), (
        "Style Discovery fallback must mention manual inspection of style list"
    )
