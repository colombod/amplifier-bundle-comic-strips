"""Tests that examples/README.md documents the v8.0.0 saga mode invocation."""

import pathlib

README = pathlib.Path(__file__).resolve().parent.parent / "examples" / "README.md"


def _readme() -> str:
    return README.read_text()


class TestSagaSectionExists:
    """The README must have a '## Saga Mode (v8.0.0)' section at the end."""

    def test_section_heading_present(self):
        assert "## Saga Mode (v8.0.0)" in _readme()

    def test_section_appears_after_naruto(self):
        text = _readme()
        naruto_pos = text.index("naruto-layout-validation-e2e")
        saga_pos = text.index("## Saga Mode (v8.0.0)")
        assert saga_pos > naruto_pos


class TestSagaContextVariables:
    """Documents the key context variables for saga mode."""

    def test_max_issues_documented(self):
        text = _readme()
        assert "max_issues" in text
        # Must mention the default value of 5
        assert "default" in text.lower() and "5" in text

    def test_source_mentioned(self):
        text = _readme()
        # source should be mentioned in the saga section specifically
        saga_section = text[text.index("## Saga Mode (v8.0.0)") :]
        assert "source" in saga_section


class TestSagaInvocationExamples:
    """The saga section must include invocation code blocks."""

    def _saga_section(self) -> str:
        text = _readme()
        return text[text.index("## Saga Mode (v8.0.0)") :]

    def test_multi_issue_example(self):
        section = self._saga_section()
        assert "max_issues=3" in section

    def test_single_issue_example(self):
        section = self._saga_section()
        assert "max_issues=1" in section

    def test_story_hints_example(self):
        section = self._saga_section()
        assert "story_hints=" in section

    def test_character_hints_example(self):
        section = self._saga_section()
        assert "character_hints=" in section


class TestSagaOutputDescription:
    """Documents what the saga output looks like."""

    def _saga_section(self) -> str:
        text = _readme()
        return text[text.index("## Saga Mode (v8.0.0)") :]

    def test_issue_file_naming(self):
        section = self._saga_section()
        assert "issue-001.html" in section
        assert "issue-002.html" in section

    def test_previously_in_recap(self):
        section = self._saga_section()
        assert "Previously" in section

    def test_to_be_continued_teaser(self):
        section = self._saga_section()
        assert "To Be Continued" in section

    def test_shared_characters(self):
        section = self._saga_section()
        assert "shared" in section.lower() or "persist" in section.lower()

    def test_character_evolution(self):
        section = self._saga_section()
        assert "evolve" in section.lower() or "evolution" in section.lower()


class TestIssueRetryRecipe:
    """Documents the issue-retry recipe for recovering failed issues."""

    def _saga_section(self) -> str:
        text = _readme()
        return text[text.index("## Saga Mode (v8.0.0)") :]

    def test_retry_recipe_mentioned(self):
        section = self._saga_section()
        assert "issue-retry" in section

    def test_retry_example_with_project_and_issue(self):
        section = self._saga_section()
        assert "project_id=" in section
        assert "issue_id=" in section
