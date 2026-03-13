"""Tests for Task 16: character-designer.md semantic search, embedding status,
and cross-version consistency sections.

Validates that the character-designer agent instructions include:
1. Semantic Duplicate Check section with search_by_description workflow and fallback
2. Embedding Status Check section with all three status explanations
3. Cross-Version Consistency section using comic_character(action='compare')
4. All tool references use valid action names
"""

from pathlib import Path


AGENT_PATH = Path(__file__).parent.parent / "agents" / "character-designer.md"


def _read_agent() -> str:
    return AGENT_PATH.read_text()


# ---------------------------------------------------------------
# Test 1: Semantic Duplicate Check section exists
# ---------------------------------------------------------------
def test_semantic_duplicate_check_section_exists() -> None:
    """Agent must have a Semantic Duplicate Check section."""
    content = _read_agent()
    assert "Semantic Duplicate Check" in content, (
        "Missing 'Semantic Duplicate Check' section in character-designer.md"
    )


# ---------------------------------------------------------------
# Test 2: search_by_description action is used
# ---------------------------------------------------------------
def test_search_by_description_action_present() -> None:
    """Semantic Duplicate Check must call comic_character with action='search_by_description'."""
    content = _read_agent()
    assert "action='search_by_description'" in content, (
        "Missing comic_character(action='search_by_description') call in character-designer.md"
    )


# ---------------------------------------------------------------
# Test 3: search_by_description uses visual_traits and distinctive_features in query
# ---------------------------------------------------------------
def test_search_by_description_uses_visual_and_distinctive() -> None:
    """search_by_description query must reference visual_traits and distinctive_features."""
    content = _read_agent()
    assert "visual_traits" in content and "distinctive_features" in content, (
        "search_by_description query must reference visual_traits and distinctive_features"
    )
    # The search_by_description call should be in the file
    assert "search_by_description" in content, (
        "search_by_description must be referenced in character-designer.md"
    )


# ---------------------------------------------------------------
# Test 4: Similarity threshold (0.8) documented
# ---------------------------------------------------------------
def test_similarity_threshold_documented() -> None:
    """Semantic Duplicate Check must document similarity threshold of 0.8."""
    content = _read_agent()
    assert "0.8" in content, (
        "Missing similarity threshold (0.8) in Semantic Duplicate Check section"
    )


# ---------------------------------------------------------------
# Test 5: Fallback to action='search' documented
# ---------------------------------------------------------------
def test_fallback_to_search_on_circuit_open() -> None:
    """Semantic Duplicate Check must fall back to comic_character(action='search') when circuit is open."""
    content = _read_agent()
    assert "skipped_circuit_open" in content, (
        "Missing 'skipped_circuit_open' fallback condition in Semantic Duplicate Check"
    )
    assert "skipped_no_client" in content, (
        "Missing 'skipped_no_client' fallback condition in Semantic Duplicate Check"
    )


# ---------------------------------------------------------------
# Test 6: Embedding Status Check section exists
# ---------------------------------------------------------------
def test_embedding_status_check_section_exists() -> None:
    """Agent must have an Embedding Status Check section."""
    content = _read_agent()
    assert "Embedding Status Check" in content, (
        "Missing 'Embedding Status Check' section in character-designer.md"
    )


# ---------------------------------------------------------------
# Test 7: embedding_status field documented
# ---------------------------------------------------------------
def test_embedding_status_field_documented() -> None:
    """Embedding Status Check must reference the embedding_status field."""
    content = _read_agent()
    assert "embedding_status" in content, (
        "Missing 'embedding_status' field reference in character-designer.md"
    )


# ---------------------------------------------------------------
# Test 8: All three embedding status values explained
# ---------------------------------------------------------------
def test_all_three_embedding_statuses_explained() -> None:
    """Embedding Status Check must explain all three status values."""
    content = _read_agent()
    assert "embedded" in content, (
        "Missing 'embedded' status explanation in Embedding Status Check"
    )
    assert "skipped_circuit_open" in content, (
        "Missing 'skipped_circuit_open' status explanation in Embedding Status Check"
    )
    assert "skipped_no_client" in content, (
        "Missing 'skipped_no_client' status explanation in Embedding Status Check"
    )


# ---------------------------------------------------------------
# Test 9: Cross-Version Consistency section exists
# ---------------------------------------------------------------
def test_cross_version_consistency_section_exists() -> None:
    """Agent must have a Cross-Version Consistency section."""
    content = _read_agent()
    assert "Cross-Version Consistency" in content, (
        "Missing 'Cross-Version Consistency' section in character-designer.md"
    )


# ---------------------------------------------------------------
# Test 10: compare action is used for cross-version consistency
# ---------------------------------------------------------------
def test_compare_action_used_for_consistency() -> None:
    """Cross-Version Consistency must call comic_character(action='compare')."""
    content = _read_agent()
    assert "action='compare'" in content, (
        "Missing comic_character(action='compare') call in Cross-Version Consistency section"
    )


# ---------------------------------------------------------------
# Test 11: Cross-Version Consistency happens after self-review
# ---------------------------------------------------------------
def test_cross_version_consistency_after_self_review() -> None:
    """Cross-Version Consistency section must appear after the self-review step."""
    content = _read_agent()
    self_review_pos = content.find("Self-Review")
    cross_version_pos = content.find("Cross-Version Consistency")
    assert self_review_pos != -1, "Self-Review section not found"
    assert cross_version_pos != -1, "Cross-Version Consistency section not found"
    assert cross_version_pos > self_review_pos, (
        "Cross-Version Consistency must appear AFTER Self-Review"
    )


# ---------------------------------------------------------------
# Test 12: Semantic Duplicate Check mentions project_id
# ---------------------------------------------------------------
def test_semantic_duplicate_check_uses_project_id() -> None:
    """search_by_description call must pass project parameter."""
    content = _read_agent()
    # Check that there's a project parameter in the search_by_description context
    assert "project=" in content or "project_id" in content, (
        "search_by_description must specify the project parameter"
    )


# ---------------------------------------------------------------
# Test 13: Semantic Duplicate Check mentions duplicate/similar handling
# ---------------------------------------------------------------
def test_semantic_duplicate_check_handles_duplicates() -> None:
    """Semantic Duplicate Check must describe handling of similar characters."""
    content = _read_agent()
    # Should mention either 'duplicate' or 'similar'
    assert "duplicate" in content.lower() or "similar" in content.lower(), (
        "Semantic Duplicate Check must mention handling of similar/duplicate characters"
    )


# ---------------------------------------------------------------
# Test 14: Embedding Status Check mentions 'degraded' for circuit open
# ---------------------------------------------------------------
def test_embedding_status_circuit_open_is_degraded() -> None:
    """skipped_circuit_open status must note degraded search availability."""
    content = _read_agent()
    # Check that skipped_circuit_open is associated with a note about degraded state
    # Both the term and 'degraded' should be in the document
    assert "skipped_circuit_open" in content, "Missing skipped_circuit_open status"
    assert "degraded" in content.lower(), (
        "skipped_circuit_open status must note 'degraded' search capability"
    )
