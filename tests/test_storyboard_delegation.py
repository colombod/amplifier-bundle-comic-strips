"""Tests for storyboard-writer stories bundle delegation architecture.

Validates that the storyboard-writer agent instructions include:
  AC1: Phase 1 — delegation to stories:content-strategist for narrative arc
  AC2: Phase 1 — delegation to stories:case-study-writer for narrative prose
  AC3: Phase 2 — comic-specific translation (panels, dialogue, staging)
  AC4: The two-phase structure is clearly documented
  AC5: Existing skills (comic-storytelling, comic-panel-composition) are still loaded in Phase 2
  AC6: Dramatization rules are preserved (no raw data in speech bubbles)
  AC7: Character selection rules are preserved (max 4 main + 2 supporting)
"""

from pathlib import Path

import yaml

AGENT_PATH = Path(__file__).parent.parent / "agents" / "storyboard-writer.md"


def _read_agent_body() -> str:
    """Read the markdown body (everything after the closing --- frontmatter delimiter)."""
    content = AGENT_PATH.read_text()
    # Skip past opening --- and find closing ---
    first_delim = content.index("---")
    second_delim = content.index("---", first_delim + 3)
    return content[second_delim + 3 :]


def _output_format_section() -> str:
    """Extract the Output Format section (bounded to the next ## heading)."""
    body = AGENT_PATH.read_text()
    marker = "## Output Format"
    assert marker in body, f"Section '{marker}' not found in storyboard-writer.md"
    start = body.index(marker)
    next_section = body.find("\n## ", start + len(marker))
    if next_section == -1:
        return body[start:]
    return body[start:next_section]


class TestPhase1NarrativeDelegation:
    """Phase 1: Storyboard-writer delegates narrative creation to stories agents."""

    def test_mentions_content_strategist_delegation(self):
        """AC1: Instructions reference delegating to stories:content-strategist."""
        body = _read_agent_body()
        assert "stories:content-strategist" in body, (
            "Agent body must reference stories:content-strategist for arc selection"
        )

    def test_mentions_case_study_writer_delegation(self):
        """AC2: Instructions reference delegating to stories:case-study-writer."""
        body = _read_agent_body()
        assert "stories:case-study-writer" in body, (
            "Agent body must reference stories:case-study-writer for narrative prose"
        )

    def test_narrative_arc_selection(self):
        """AC1b: Instructions mention narrative arc selection from the strategist."""
        body = _read_agent_body().lower()
        assert "narrative arc" in body or "story arc" in body, (
            "Agent body must discuss narrative/story arc selection"
        )

    def test_challenge_approach_results_structure(self):
        """AC2b: Instructions mention Challenge/Approach/Results prose structure."""
        body = _read_agent_body()
        # case-study-writer produces Challenge → Approach → Results
        assert "Challenge" in body and "Approach" in body and "Results" in body, (
            "Agent body must reference Challenge/Approach/Results narrative structure"
        )


class TestPhase2ComicTranslation:
    """Phase 2: Storyboard-writer does comic-specific translation."""

    def test_phase_structure_documented(self):
        """AC4: Two-phase structure is clearly documented in the instructions."""
        body = _read_agent_body()
        assert "Phase 1" in body and "Phase 2" in body, (
            "Agent body must clearly document Phase 1 and Phase 2"
        )

    def test_skills_still_loaded(self):
        """AC5: comic-storytelling and comic-panel-composition skills are still loaded."""
        body = _read_agent_body()
        assert "comic-storytelling" in body, (
            "Agent body must still reference comic-storytelling skill"
        )
        assert "comic-panel-composition" in body, (
            "Agent body must still reference comic-panel-composition skill"
        )

    def test_panel_mapping_preserved(self):
        """AC3: Comic-specific panel mapping instructions exist."""
        body = _read_agent_body().lower()
        assert "panel" in body, "Agent body must discuss panel layout"
        assert "camera" in body or "camera_angle" in body, (
            "Agent body must discuss camera angles"
        )

    def test_dialogue_transformation(self):
        """AC3b: Instructions discuss transforming prose to comic dialogue."""
        body = _read_agent_body().lower()
        assert "dialogue" in body, "Agent body must discuss dialogue"
        assert "speech bubble" in body or "speech bubbles" in body, (
            "Agent body must discuss speech bubbles"
        )


class TestPreservedRules:
    """Existing rules must be preserved in the rewrite."""

    def test_dramatization_rules_present(self):
        """AC6: Dramatization rules (no raw data in speech bubbles) are preserved."""
        body = _read_agent_body()
        assert "NON-NEGOTIABLE" in body or "Dramatization Rules" in body, (
            "Agent body must preserve dramatization rules section"
        )
        # Check for specific rule about UUIDs
        assert "UUID" in body or "session ID" in body.lower(), (
            "Agent body must warn against raw UUIDs in speech bubbles"
        )

    def test_character_selection_rules_present(self):
        """AC7: Character selection rules (max 4 main + 2 supporting) are preserved."""
        body = _read_agent_body()
        assert "4 main" in body or "3-4 main" in body, (
            "Agent body must preserve max 4 main characters rule"
        )
        assert "supporting" in body.lower(), (
            "Agent body must discuss supporting characters"
        )

    def test_output_format_preserved(self):
        """Output format (storyboard JSON) is preserved."""
        body = _read_agent_body()
        assert "panel_count" in body or "panels" in body, (
            "Agent body must preserve JSON output format with panels"
        )

    def test_max_12_panels_rule(self):
        """The 12-panel maximum is preserved."""
        body = _read_agent_body()
        assert "12 panels" in body, "Agent body must preserve the 12-panel maximum rule"

    def test_page_break_rules(self):
        """Page break rules are preserved."""
        body = _read_agent_body()
        assert "page_break_after" in body or "page break" in body.lower(), (
            "Agent body must preserve page break rules"
        )


class TestFrontmatterDescription:
    """Frontmatter description reflects the two-phase delegation architecture."""

    def test_description_mentions_delegation(self):
        """Description references delegation to stories bundle."""
        content = AGENT_PATH.read_text()
        first = content.index("---")
        second = content.index("---", first + 3)
        frontmatter = yaml.safe_load(content[first + 3 : second])
        desc = frontmatter["meta"]["description"]
        assert "stories" in desc.lower() or "delegate" in desc.lower(), (
            "meta.description should mention stories delegation or delegate"
        )

    def test_description_mentions_two_phases(self):
        """Description references the two-phase process."""
        content = AGENT_PATH.read_text()
        first = content.index("---")
        second = content.index("---", first + 3)
        frontmatter = yaml.safe_load(content[first + 3 : second])
        desc = frontmatter["meta"]["description"].lower()
        assert (
            "phase" in desc
            or "two-phase" in desc
            or ("narrative" in desc and "panel" in desc)
        ), (
            "meta.description should mention the two-phase process or both narrative + panel aspects"
        )


class TestForeachOutputContract:
    """The storyboard-writer must emit character_list and panel_list arrays for recipe foreach loops."""

    def test_storyboard_writer_documents_both_output_arrays(self) -> None:
        """Output Format section must document both character_list and panel_list as top-level keys."""
        section = _output_format_section()
        assert "character_list" in section, (
            "Missing character_list in Output Format section"
        )
        assert "panel_list" in section, "Missing panel_list in Output Format section"

    def test_character_list_entry_has_required_fields(self) -> None:
        """character_list entry schema in Output Format documents all required fields."""
        section = _output_format_section()
        for field in ["name", "role", "type", "bundle", "description"]:
            assert f'"{field}"' in section, (
                f"character_list missing required field: {field}"
            )

    def test_panel_list_entry_has_required_fields(self) -> None:
        """panel_list entry schema must document all required fields.

        'characters_present' is especially critical: panel-artist uses it to
        look up reference images from character_sheet; any name mismatch
        causes a lookup failure at runtime.
        """
        section = _output_format_section()
        for field in [
            "index",
            "size",
            "scene_description",
            "characters_present",
            "emotional_beat",
            "camera_angle",
            "page_break_after",
        ]:
            assert f'"{field}"' in section, (
                f"panel_list missing required field: {field}"
            )

    def test_panel_list_uses_index_not_number(self) -> None:
        """Panel entries must use 'index' (not 'number') consistently."""
        section = _output_format_section()
        assert '"index"' in section, (
            "Panel entries must use 'index' as the panel number key"
        )
        # 'number' may appear in prose but should NOT appear as a JSON field key
        # Check the panel JSON example doesn't use "number": as a field
        assert '"number":' not in section, (
            "Panel entries must not use 'number' — use 'index' consistently"
        )
