"""Tests for image_requirements sections in style pack markdown files."""

import re
from pathlib import Path

import pytest
import yaml

STYLES_DIR = Path(__file__).parent.parent / "context" / "styles"

# Expected values per spec
EXPECTED = {
    "manga.md": {
        "style_category": "manga-lineart",
        "detail_level": "medium",
        "text_avoidance": "critical",
    },
    "superhero.md": {
        "style_category": "superhero",
        "detail_level": "high",
        "text_avoidance": "good",
    },
    "indie.md": {
        "style_category": "indie",
        "detail_level": "high",
        "text_avoidance": "good",
    },
    "newspaper.md": {
        "style_category": "cartoon",
        "detail_level": "low",
        "text_avoidance": "fair",
    },
    "ligne-claire.md": {
        "style_category": "ligne-claire",
        "detail_level": "high",
        "text_avoidance": "excellent",
    },
    "retro-americana.md": {
        "style_category": "illustration",
        "detail_level": "medium",
        "text_avoidance": "fair",
    },
}

ALL_STYLE_FILES = list(EXPECTED.keys())


def _read_style(filename: str) -> str:
    """Read a style pack file and return its content."""
    path = STYLES_DIR / filename
    assert path.exists(), f"Style file not found: {path}"
    return path.read_text()


def _extract_image_requirements(content: str) -> dict | None:
    """Extract the image_requirements YAML block from markdown content."""
    # Find the ## Image Requirements section
    match = re.search(
        r"^## Image Requirements\s*\n(.*)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        return None

    section_content = match.group(1)

    # Extract YAML code block
    yaml_match = re.search(
        r"```ya?ml\s*\n(.*?)```",
        section_content,
        re.DOTALL,
    )
    if not yaml_match:
        return None

    return yaml.safe_load(yaml_match.group(1))


class TestImageRequirementsSectionExists:
    """AC1: All 6 style pack files have '## Image Requirements' section."""

    @pytest.mark.parametrize("filename", ALL_STYLE_FILES)
    def test_section_exists(self, filename: str):
        content = _read_style(filename)
        assert "## Image Requirements" in content, (
            f"{filename} missing '## Image Requirements' section"
        )


class TestImageRequirementsYAMLBlock:
    """AC2: Each contains a YAML code block with image_requirements key."""

    @pytest.mark.parametrize("filename", ALL_STYLE_FILES)
    def test_yaml_block_with_key(self, filename: str):
        content = _read_style(filename)
        parsed = _extract_image_requirements(content)
        assert parsed is not None, (
            f"{filename} has no parseable YAML block in Image Requirements"
        )
        assert "image_requirements" in parsed, (
            f"{filename} YAML block missing 'image_requirements' key"
        )


# Build parametrize args: (filename, field, expected_value) for AC3-AC8
_VALUE_TEST_CASES = [
    (filename, field, value)
    for filename, fields in EXPECTED.items()
    for field, value in fields.items()
]


class TestStylePackValues:
    """AC3-AC8: Each style pack has correct image_requirements values."""

    @pytest.mark.parametrize(
        ("filename", "field", "expected_value"),
        _VALUE_TEST_CASES,
        ids=[f"{f}-{k}" for f, fields in EXPECTED.items() for k in fields],
    )
    def test_field_value(self, filename: str, field: str, expected_value: str):
        content = _read_style(filename)
        parsed = _extract_image_requirements(content)
        assert parsed is not None, (
            f"{filename} has no parseable YAML block in Image Requirements"
        )
        actual = parsed["image_requirements"][field]
        assert actual == expected_value, (
            f"{filename}: expected {field}='{expected_value}', got '{actual}'"
        )


class TestGrepDiscoverability:
    """AC9: grep for 'image_requirements' finds all 6 files."""

    def test_all_six_files_contain_image_requirements(self):
        found = []
        for filename in ALL_STYLE_FILES:
            content = _read_style(filename)
            if "image_requirements" in content:
                found.append(filename)
        assert sorted(found) == sorted(ALL_STYLE_FILES), (
            f"Expected all 6 files to contain 'image_requirements', "
            f"but only found in: {found}"
        )


class TestSectionPlacement:
    """Image Requirements section should come after AmpliVerse Branding."""

    @pytest.mark.parametrize("filename", ALL_STYLE_FILES)
    def test_after_ampliverse_branding(self, filename: str):
        content = _read_style(filename)
        branding_pos = content.find("## AmpliVerse Branding")
        image_req_pos = content.find("## Image Requirements")
        assert branding_pos >= 0, f"{filename} missing AmpliVerse Branding section"
        assert image_req_pos >= 0, f"{filename} missing Image Requirements section"
        assert image_req_pos > branding_pos, (
            f"{filename}: Image Requirements should come after AmpliVerse Branding"
        )
