"""Tests for Task 17: panel-artist.md embedding status awareness and
semantic character fallback sections.

Validates that the panel-artist agent instructions include:
1. Embedding Status Awareness section with all three status values explained
2. Semantic Character Discovery section with search_by_description workflow
3. Fallback to comic_character(action='search') when embedding unavailable
4. All tool references use valid action names
"""

from pathlib import Path


AGENT_PATH = Path(__file__).parent.parent / "agents" / "panel-artist.md"


def _read_agent() -> str:
    return AGENT_PATH.read_text()


# ---------------------------------------------------------------
# Test 1: Embedding Status Awareness section exists
# ---------------------------------------------------------------
def test_embedding_status_awareness_section_exists() -> None:
    """Agent must have an Embedding Status Awareness section."""
    content = _read_agent()
    assert "Embedding Status Awareness" in content, (
        "Missing 'Embedding Status Awareness' section in panel-artist.md"
    )


# ---------------------------------------------------------------
# Test 2: embedding_status field referenced
# ---------------------------------------------------------------
def test_embedding_status_field_referenced() -> None:
    """Embedding Status Awareness must reference the embedding_status field."""
    content = _read_agent()
    assert "embedding_status" in content, (
        "Missing 'embedding_status' field reference in panel-artist.md"
    )


# ---------------------------------------------------------------
# Test 3: 'embedded' status documented as good
# ---------------------------------------------------------------
def test_embedded_status_documented() -> None:
    """Embedding Status Awareness must document 'embedded' as a good status."""
    content = _read_agent()
    assert "`embedded`" in content, (
        "Missing '`embedded`' status in Embedding Status Awareness table"
    )


# ---------------------------------------------------------------
# Test 4: skipped_circuit_open status documented
# ---------------------------------------------------------------
def test_skipped_circuit_open_status_documented() -> None:
    """Embedding Status Awareness must document 'skipped_circuit_open' status."""
    content = _read_agent()
    assert "skipped_circuit_open" in content, (
        "Missing 'skipped_circuit_open' status in Embedding Status Awareness section"
    )


# ---------------------------------------------------------------
# Test 5: skipped_no_client status documented
# ---------------------------------------------------------------
def test_skipped_no_client_status_documented() -> None:
    """Embedding Status Awareness must document 'skipped_no_client' status."""
    content = _read_agent()
    assert "skipped_no_client" in content, (
        "Missing 'skipped_no_client' status in Embedding Status Awareness section"
    )


# ---------------------------------------------------------------
# Test 6: Semantic Character Discovery section exists
# ---------------------------------------------------------------
def test_semantic_character_discovery_section_exists() -> None:
    """Agent must have a Semantic Character Discovery section."""
    content = _read_agent()
    assert "Semantic Character Discovery" in content, (
        "Missing 'Semantic Character Discovery' section in panel-artist.md"
    )


# ---------------------------------------------------------------
# Test 7: search_by_description action is used
# ---------------------------------------------------------------
def test_search_by_description_action_present() -> None:
    """Semantic Character Discovery must call comic_character with action='search_by_description'."""
    content = _read_agent()
    assert "action='search_by_description'" in content, (
        "Missing comic_character(action='search_by_description') call in panel-artist.md"
    )


# ---------------------------------------------------------------
# Test 8: Fallback to action='search' is documented
# ---------------------------------------------------------------
def test_fallback_to_search_action_documented() -> None:
    """Semantic Character Discovery must fall back to comic_character(action='search') when embedding unavailable."""
    content = _read_agent()
    assert "action='search'" in content, (
        "Missing comic_character(action='search') fallback call in panel-artist.md"
    )


# ---------------------------------------------------------------
# Test 9: Embedding Status Awareness appears after self-review section
# ---------------------------------------------------------------
def test_embedding_status_awareness_after_self_review() -> None:
    """Embedding Status Awareness section must appear after the self-review section."""
    content = _read_agent()
    self_review_pos = content.find("Self-Review")
    embedding_pos = content.find("Embedding Status Awareness")
    assert self_review_pos != -1, "Self-Review section not found"
    assert embedding_pos != -1, "Embedding Status Awareness section not found"
    assert embedding_pos > self_review_pos, (
        "Embedding Status Awareness must appear AFTER Self-Review"
    )


# ---------------------------------------------------------------
# Test 11: Semantic Character Discovery uses description-based search
# ---------------------------------------------------------------
def test_semantic_character_discovery_uses_description() -> None:
    """Semantic Character Discovery must describe searching by character description."""
    content = _read_agent()
    assert "search_by_description" in content, (
        "Semantic Character Discovery must use search_by_description action"
    )


# ---------------------------------------------------------------
# Test 12: Section is marked as Optional Enhancement
# ---------------------------------------------------------------
def test_semantic_character_discovery_is_optional() -> None:
    """Semantic Character Discovery section must be marked as Optional Enhancement."""
    content = _read_agent()
    assert "Optional" in content, (
        "Semantic Character Discovery must be labeled as Optional Enhancement in panel-artist.md"
    )
