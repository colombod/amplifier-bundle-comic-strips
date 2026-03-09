"""Tests for pipeline-flow.dot diagram updates (v7.7.0 / discover_sessions)."""

import pytest
from pathlib import Path

pytestmark = pytest.mark.skip(reason="legacy test for pre-v9 recipe")

DOT_FILE = (
    Path(__file__).resolve().parent.parent / "docs" / "diagrams" / "pipeline-flow.dot"
)


def _read_dot() -> str:
    return DOT_FILE.read_text()


# --- Step 1: version label ---


def test_version_is_v7_7_0():
    content = _read_dot()
    assert "Comic Generation Pipeline v7.7.0" in content, "Title should show v7.7.0"
    assert "v7.6.0" not in content, "Old version v7.6.0 should not remain"


# --- Step 2: input node uses {{source}} ---


def test_input_node_shows_source_template():
    content = _read_dot()
    assert "{{source}}" in content, "Input node should reference {{source}}"
    # Old label should be gone
    assert "<B>events.jsonl</B>" not in content, (
        "Old events.jsonl label should be replaced"
    )
    assert "Amplifier session log" not in content, "Old subtitle should be replaced"


def test_input_node_multiline_description():
    content = _read_dot()
    assert "project name, session ID(s)," in content
    assert "file path(s), or description" in content


# --- Step 3: discover_sessions node ---


def test_discover_sessions_node_exists():
    content = _read_dot()
    assert "discover_sessions [" in content, "discover_sessions node must exist"


def test_discover_sessions_label():
    content = _read_dot()
    assert "0a. Discover Sessions" in content
    assert "stories:story-researcher" in content
    assert "resolves {{source}} to session data" in content


# --- Step 4: edge chain ---


def test_edge_chain_includes_discover_sessions():
    content = _read_dot()
    assert ("init -> discover_sessions -> research") in content, (
        "Edge chain must include discover_sessions between init and research"
    )
    # Old chain should not exist
    # Check that "init -> research" without discover_sessions isn't present
    # (but it IS present as part of the longer chain, so we check for exact old line)
    assert "init -> research -> style_curation" not in content, (
        "Old direct init->research chain should be replaced"
    )


# --- Step 5: discover_data annotation ---


def test_discover_data_annotation_exists():
    content = _read_dot()
    assert "discover_data [" in content, "discover_data annotation node must exist"


def test_discover_data_annotation_content():
    content = _read_dot()
    assert "Session discovery:" in content
    # "discover-sessions" (hyphenated) only appears in the annotation node,
    # not in the node id discover_sessions (underscored).
    assert "discover-sessions" in content
    assert "{{session_data}} URI" in content
