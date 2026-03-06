"""Tests for Task 14: character-designer.md cross-project discovery and per-issue variants.

Validates that the character-designer agent instructions include:
1.  Cross-project discovery step calling comic_character(action='search')
2.  Per-issue variant creation workflow with needs_new_variant
3.  Versioned variant URIs (?v=2, ?v=3)
4.  Evolution tracking metadata (evolution, issue_number, base_variant_uri)
5.  4-case decision matrix (reuse / redesign / new / per-issue variant)
6.  Per-issue variant stored under same character slug with version
7.  Panel-artist receives correct variant URI per issue
8.  Input section documents per_issue field on character_item
9.  Cross-project search happens BEFORE the existing-character check
10. char_slug field documented in input
"""

from pathlib import Path


AGENT_PATH = Path(__file__).parent.parent / "agents" / "character-designer.md"


def _read_agent() -> str:
    return AGENT_PATH.read_text()


# ---------------------------------------------------------------
# Test 1: Cross-project discovery step exists
# ---------------------------------------------------------------
def test_cross_project_discovery_search_call() -> None:
    """Agent must call comic_character(action='search') for cross-project discovery."""
    content = _read_agent()
    assert "comic_character(action='search'" in content, (
        "Missing comic_character(action='search') call for cross-project discovery"
    )


# ---------------------------------------------------------------
# Test 2: Cross-project discovery mentions style parameter
# ---------------------------------------------------------------
def test_cross_project_discovery_style_param() -> None:
    """Cross-project search must filter by style."""
    content = _read_agent()
    # The search call should include a style parameter
    assert "action='search'" in content and "style=" in content, (
        "Cross-project search must include style parameter"
    )


# ---------------------------------------------------------------
# Test 3: Cross-project discovery step comes BEFORE existing check
# ---------------------------------------------------------------
def test_cross_project_discovery_before_existing_check() -> None:
    """Cross-project discovery must appear before the existing_uri check."""
    content = _read_agent()
    search_pos = content.find("action='search'")
    existing_check_heading = content.find("Check for Existing Character")
    assert search_pos != -1, "Cross-project discovery section not found"
    assert existing_check_heading != -1, "Existing character check section not found"
    assert search_pos < existing_check_heading, (
        "Cross-project discovery must appear BEFORE the existing character check"
    )


# ---------------------------------------------------------------
# Test 4: Per-issue variant creation workflow
# ---------------------------------------------------------------
def test_per_issue_variant_workflow_section() -> None:
    """Agent must have a per-issue variant creation workflow section."""
    content = _read_agent()
    assert "needs_new_variant" in content, (
        "Missing needs_new_variant flag for per-issue variant creation"
    )
    assert "per_issue" in content, (
        "Missing per_issue field reference for variant creation"
    )


# ---------------------------------------------------------------
# Test 5: Versioned variant URIs
# ---------------------------------------------------------------
def test_versioned_variant_uris() -> None:
    """Variants must use versioned URIs (?v=2, ?v=3 etc)."""
    content = _read_agent()
    assert "?v=" in content, "Missing versioned variant URI format (?v=2, ?v=3)"


# ---------------------------------------------------------------
# Test 6: Evolution tracking metadata
# ---------------------------------------------------------------
def test_evolution_tracking_metadata() -> None:
    """Each variant must store evolution metadata."""
    content = _read_agent()
    assert "evolution" in content.lower(), "Missing 'evolution' in variant metadata"
    assert "base_variant_uri" in content, "Missing base_variant_uri in variant metadata"
    assert "issue_number" in content, "Missing issue_number in variant metadata"


# ---------------------------------------------------------------
# Test 7: 4-case decision matrix
# ---------------------------------------------------------------
def test_four_case_decision_matrix() -> None:
    """Decision matrix must have 4 cases: reuse, redesign, new, per-issue variant."""
    content = _read_agent()
    # Case 1: reuse
    assert "existing_uri" in content and "needs_redesign" in content, (
        "Decision matrix missing reuse case (existing_uri + needs_redesign)"
    )
    # Case 4: per-issue variant
    assert "needs_new_variant" in content, (
        "Decision matrix missing Case 4 (per-issue variant with needs_new_variant)"
    )
    # Should explicitly reference 4 cases
    assert "Case 4" in content or "case 4" in content.lower(), (
        "Decision matrix must explicitly include Case 4 for per-issue variants"
    )


# ---------------------------------------------------------------
# Test 8: Variant stored under same character slug
# ---------------------------------------------------------------
def test_variant_stored_under_same_slug() -> None:
    """Per-issue variants are stored as new versions under the same character slug."""
    content = _read_agent()
    # Should mention storing variants under the same slug
    assert "char_slug" in content or "character slug" in content.lower(), (
        "Must document that variants are stored under the same character slug"
    )


# ---------------------------------------------------------------
# Test 9: Panel-artist receives variant URI per issue
# ---------------------------------------------------------------
def test_panel_artist_variant_uri() -> None:
    """Agent must mention that panel-artist receives the correct variant URI."""
    content = _read_agent()
    assert "panel-artist" in content.lower() and "variant" in content.lower(), (
        "Must mention panel-artist receiving the correct variant URI per issue"
    )


# ---------------------------------------------------------------
# Test 10: Input section documents per_issue and char_slug fields
# ---------------------------------------------------------------
def test_input_documents_per_issue_field() -> None:
    """Input section must document the per_issue field on character_item."""
    content = _read_agent()
    # Find the Input section
    input_section_start = content.find("## Input")
    assert input_section_start != -1, "Input section not found"
    # Find the next major section after Input
    next_section = content.find("\n## ", input_section_start + 1)
    if next_section == -1:
        input_section = content[input_section_start:]
    else:
        input_section = content[input_section_start:next_section]
    assert "per_issue" in input_section, (
        "Input section must document the per_issue field"
    )
    assert "char_slug" in input_section, (
        "Input section must document the char_slug field"
    )


# ---------------------------------------------------------------
# Test 11: Decision matrix explicitly lists all 4 cases
# ---------------------------------------------------------------
def test_decision_matrix_case_labels() -> None:
    """Decision matrix must have labeled Case 1 through Case 4."""
    content = _read_agent()
    for case_num in range(1, 5):
        pattern = f"Case {case_num}"
        assert pattern in content, f"Decision matrix missing labeled '{pattern}'"
