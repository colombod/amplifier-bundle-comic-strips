"""Tests for session-to-comic.yaml context variable updates.

Validates that:
1. `source` context variable exists on the line after `context:`
2. `session_file` context variable exists with deprecated comment
3. Usage comments show new `source=` syntax
4. Usage comments include deprecated `session_file=` example
"""

import pathlib

RECIPE_PATH = pathlib.Path(__file__).parent.parent / "recipes" / "session-to-comic.yaml"


def _read_recipe_lines():
    return RECIPE_PATH.read_text().splitlines()


def test_source_is_first_context_variable():
    """source: '' must appear on the line immediately after 'context:'."""
    lines = _read_recipe_lines()
    for i, line in enumerate(lines):
        if line.strip() == "context:":
            next_line = lines[i + 1].strip()
            assert next_line.startswith("source:"), (
                f"Expected 'source:' on line after 'context:', got: {next_line!r}"
            )
            break
    else:
        raise AssertionError("'context:' block not found in recipe")


def test_session_file_follows_source():
    """session_file: '' must appear after source: '' in context block."""
    lines = _read_recipe_lines()
    source_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("source:") and "context" not in line:
            source_idx = i
            break
    assert source_idx is not None, "'source:' not found in recipe"
    next_line = lines[source_idx + 1].strip()
    assert next_line.startswith("session_file:"), (
        f"Expected 'session_file:' after 'source:', got: {next_line!r}"
    )


def test_session_file_has_deprecated_comment():
    """session_file line must have a 'Deprecated' comment."""
    lines = _read_recipe_lines()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("session_file:") and "Deprecated" in line:
            return  # Found it
    raise AssertionError("session_file with 'Deprecated' comment not found")


def test_source_has_required_comment():
    """source line must have a 'Required' comment."""
    lines = _read_recipe_lines()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("source:") and "Required" in line:
            return  # Found it
    raise AssertionError("source with 'Required' comment not found")


def test_usage_comments_show_source_syntax():
    """Usage comments must show source= syntax."""
    text = RECIPE_PATH.read_text()
    assert "source=comic-strip-bundle" in text, (
        "Missing source=comic-strip-bundle usage example"
    )
    assert "source=./my-session.jsonl" in text, (
        "Missing source=./my-session.jsonl usage example"
    )


def test_usage_comments_show_deprecated_session_file():
    """Usage comments must include a deprecated session_file= example."""
    text = RECIPE_PATH.read_text()
    assert "session_file=./events.jsonl" in text, (
        "Missing deprecated session_file= usage example"
    )
    assert "deprecated" in text.lower(), "Missing 'deprecated' note in usage comments"


def test_context_has_both_source_and_session_file():
    """Context block must contain both source and session_file keys (text check)."""
    lines = _read_recipe_lines()
    in_context = False
    found_source = False
    found_session_file = False
    for line in lines:
        if line.strip() == "context:":
            in_context = True
            continue
        if in_context:
            stripped = line.strip()
            # End of context block when we hit a non-indented non-comment line
            if stripped and not stripped.startswith("#") and not line.startswith(" "):
                break
            if stripped.startswith("source:"):
                found_source = True
            if stripped.startswith("session_file:"):
                found_session_file = True
    assert found_source, "'source:' not found in context block"
    assert found_session_file, "'session_file:' not found in context block"
