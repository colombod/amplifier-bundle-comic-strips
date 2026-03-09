"""Tests for the comic-design interactive mode file."""

import os

import yaml

MODE_DIR = os.path.join(os.path.dirname(__file__), "..", "modes")
MODE_FILE = os.path.join(MODE_DIR, "comic-design.md")


def _parse_frontmatter(filepath: str) -> dict:
    """Parse YAML frontmatter from a markdown file."""
    with open(filepath) as f:
        text = f.read()
    parts = text.split("---")
    assert len(parts) >= 3, "File must have YAML frontmatter delimited by ---"
    data = yaml.safe_load(parts[1])
    assert data is not None, "YAML frontmatter must not be empty"
    return data


def _get_body(filepath: str) -> str:
    """Get the body content after YAML frontmatter."""
    with open(filepath) as f:
        text = f.read()
    parts = text.split("---", 2)
    assert len(parts) >= 3, "File must have YAML frontmatter delimited by ---"
    return parts[2]


# --- AC 1: File exists ---
class TestFileExists:
    def test_comic_design_md_exists(self):
        assert os.path.isfile(MODE_FILE), (
            f"modes/comic-design.md must exist at {MODE_FILE}"
        )


# --- AC 2: YAML parses correctly ---
class TestYAMLParsing:
    def test_yaml_parses(self):
        data = _parse_frontmatter(MODE_FILE)
        assert isinstance(data, dict)


# --- AC 3: mode.name is 'comic-design' ---
class TestModeName:
    def test_mode_name(self):
        data = _parse_frontmatter(MODE_FILE)
        assert data["mode"]["name"] == "comic-design"


# --- AC 4: mode.default_action is 'block' ---
class TestDefaultAction:
    def test_default_action_is_block(self):
        data = _parse_frontmatter(MODE_FILE)
        assert data["mode"]["default_action"] == "block"


# --- AC 5: mode.allow_clear is False ---
class TestAllowClear:
    def test_allow_clear_is_false(self):
        data = _parse_frontmatter(MODE_FILE)
        assert data["mode"]["allow_clear"] is False


# --- AC 6: mode.allowed_transitions is ['comic-plan', 'comic-brainstorm'] ---
class TestAllowedTransitions:
    def test_allowed_transitions(self):
        data = _parse_frontmatter(MODE_FILE)
        transitions = data["mode"]["allowed_transitions"]
        assert set(transitions) == {"comic-plan", "comic-brainstorm"}


# --- AC 7: mode.tools.safe includes comic_asset but NOT comic_create ---
class TestToolsSafe:
    def test_comic_asset_in_safe(self):
        data = _parse_frontmatter(MODE_FILE)
        safe = data["mode"]["tools"]["safe"]
        assert "comic_asset" in safe, "comic_asset must be in tools.safe"

    def test_comic_create_not_in_safe(self):
        data = _parse_frontmatter(MODE_FILE)
        safe = data["mode"]["tools"]["safe"]
        assert "comic_create" not in safe, "comic_create must NOT be in tools.safe"


# --- AC 8: comic_create NOT in safe or warn (blocked) ---
class TestComicCreateBlocked:
    def test_comic_create_not_in_safe_or_warn(self):
        data = _parse_frontmatter(MODE_FILE)
        tools = data["mode"]["tools"]
        safe = tools.get("safe", [])
        warn = tools.get("warn", [])
        assert "comic_create" not in safe, "comic_create must NOT be in safe"
        assert "comic_create" not in warn, "comic_create must NOT be in warn"


# --- AC 9: Verification script passes comic-design checks ---
# The verification script checks are structurally covered by tests above:
# - file exists, YAML parses, required keys, default_action=block,
#   allow_clear=false, comic_create blocked
# We also verify all required YAML keys that the script checks.
class TestVerificationScriptCompatibility:
    def test_required_keys_present(self):
        data = _parse_frontmatter(MODE_FILE)
        m = data["mode"]
        for key in ["name", "default_action", "allowed_transitions", "allow_clear"]:
            assert key in m, f"mode.{key} is required"
        assert "tools" in m and "safe" in m["tools"], "mode.tools.safe is required"


# --- Spec content requirements ---
class TestBodyContent:
    def test_critical_section_exists(self):
        body = _get_body(MODE_FILE)
        assert "<CRITICAL>" in body
        assert "comic_create" in body.lower() or "comic_create blocked" in body

    def test_hard_gate_section_exists(self):
        body = _get_body(MODE_FILE)
        assert "<HARD-GATE>" in body

    def test_anti_rationalization_table(self):
        body = _get_body(MODE_FILE)
        # Table should have at least 5 entries (rows with |)
        table_rows = [
            line
            for line in body.split("\n")
            if line.strip().startswith("|")
            and "---" not in line
            and "Your Excuse" not in line
        ]
        assert len(table_rows) >= 5, (
            f"Anti-Rationalization Table must have >= 5 entries, found {len(table_rows)}"
        )

    def test_spec_safe_tools_list(self):
        """Verify the full safe tools list from the spec."""
        data = _parse_frontmatter(MODE_FILE)
        safe = data["mode"]["tools"]["safe"]
        expected = [
            "read_file",
            "glob",
            "grep",
            "delegate",
            "comic_project",
            "comic_character",
            "comic_asset",
            "comic_style",
            "load_skill",
            "web_search",
            "web_fetch",
        ]
        assert set(safe) == set(expected), (
            f"Safe tools mismatch. Expected: {sorted(expected)}, Got: {sorted(safe)}"
        )
