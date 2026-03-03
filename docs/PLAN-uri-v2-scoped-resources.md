# URI v2: Scoped Resources Implementation Plan

> **Execution:** Use the subagent-driven-development workflow to implement this plan.

**Goal:** Replace the fixed 4-segment `comic://` URI scheme with scope-aware formats — 3-segment for project-scoped resources (characters, styles) and 5-segment for issue-scoped resources (panels, covers, etc.) — so the URI honestly reflects the data model.

**Architecture:** The `ComicURI` dataclass gets `issue: str | None` (None for project-scoped), the parser handles two routing paths based on the second segment, and all builders/services/tools/agents/recipes update to produce and consume the new format. The storyboard becomes the cast binding with versioned project-scoped character URIs.

**Tech Stack:** Python 3.13, pytest + pytest-asyncio, YAML recipe files, Markdown agent instructions.

**Design Document:** `docs/DESIGN-uri-v2-scoped-resources.md`

---

## Migration Map (Reference)

| v1 URI | v2 URI |
|--------|--------|
| `comic://proj/issue-001/character/explorer` | `comic://proj/characters/explorer` |
| `comic://proj/issue-001/character/explorer?v=2` | `comic://proj/characters/explorer?v=2` |
| `comic://proj/issue-001/style/manga` | `comic://proj/styles/manga` |
| `comic://proj/issue-001/panel/panel_01` | `comic://proj/issues/issue-001/panels/panel_01` |
| `comic://proj/issue-001/cover/cover` | `comic://proj/issues/issue-001/covers/cover` |
| `comic://proj/issue-001/storyboard/main` | `comic://proj/issues/issue-001/storyboards/main` |
| `comic://proj/issue-001/research/data` | `comic://proj/issues/issue-001/research/data` |
| `comic://proj/issue-001/final/comic` | `comic://proj/issues/issue-001/finals/comic` |
| `comic://proj/issue-001/avatar/logo` | `comic://proj/issues/issue-001/avatars/logo` |
| `comic://proj/issue-001/qa_screenshot/check` | `comic://proj/issues/issue-001/qa_screenshots/check` |

---

## WP-1: Update ComicURI Core (Tasks 1.1 + 1.2)

This is the foundation. Everything else depends on it.

### Task 1.1: Update `ComicURI` dataclass, constants, parser, and formatter

**Files:**
- Modify: `modules/tool-comic-assets/amplifier_module_comic_assets/comic_uri.py`
- Modify: `modules/tool-comic-assets/tests/test_comic_uri.py`

**Step 1: Rewrite all existing tests to expect v2 URI format**

Replace the entire contents of `modules/tool-comic-assets/tests/test_comic_uri.py` with:

```python
"""Tests for the comic:// URI protocol (v2: scope-aware)."""
from __future__ import annotations

import pytest

from amplifier_module_comic_assets.comic_uri import (
    ISSUE_SCOPED_TYPES,
    PROJECT_SCOPED_TYPES,
    ComicURI,
    InvalidComicURI,
    parse_comic_uri,
)


class TestComicURIParsing:
    """Parse comic:// URIs into ComicURI dataclass."""

    # --- Project-scoped (3 segments after scheme) ---

    def test_parse_project_scoped_character(self) -> None:
        uri = parse_comic_uri("comic://my-project/characters/explorer")
        assert uri.project == "my-project"
        assert uri.asset_type == "characters"
        assert uri.name == "explorer"
        assert uri.issue is None
        assert uri.version is None

    def test_parse_project_scoped_style(self) -> None:
        uri = parse_comic_uri("comic://my-project/styles/manga")
        assert uri.project == "my-project"
        assert uri.asset_type == "styles"
        assert uri.name == "manga"
        assert uri.issue is None

    def test_parse_project_scoped_with_version(self) -> None:
        uri = parse_comic_uri("comic://my-project/characters/explorer?v=2")
        assert uri.project == "my-project"
        assert uri.asset_type == "characters"
        assert uri.name == "explorer"
        assert uri.issue is None
        assert uri.version == 2

    # --- Issue-scoped (5 segments after scheme) ---

    def test_parse_issue_scoped_panel(self) -> None:
        uri = parse_comic_uri("comic://my-project/issues/issue-001/panels/panel_01")
        assert uri.project == "my-project"
        assert uri.issue == "issue-001"
        assert uri.asset_type == "panels"
        assert uri.name == "panel_01"
        assert uri.version is None

    def test_parse_issue_scoped_cover(self) -> None:
        uri = parse_comic_uri("comic://my-project/issues/the-revenge/covers/cover")
        assert uri.project == "my-project"
        assert uri.issue == "the-revenge"
        assert uri.asset_type == "covers"
        assert uri.name == "cover"

    def test_parse_issue_scoped_with_version(self) -> None:
        uri = parse_comic_uri("comic://my-project/issues/issue-001/panels/panel_01?v=3")
        assert uri.project == "my-project"
        assert uri.issue == "issue-001"
        assert uri.asset_type == "panels"
        assert uri.name == "panel_01"
        assert uri.version == 3

    def test_parse_all_project_scoped_types(self) -> None:
        for atype in PROJECT_SCOPED_TYPES:
            uri = parse_comic_uri(f"comic://p/{atype}/n")
            assert uri.asset_type == atype
            assert uri.issue is None

    def test_parse_all_issue_scoped_types(self) -> None:
        for atype in ISSUE_SCOPED_TYPES:
            uri = parse_comic_uri(f"comic://p/issues/i/{atype}/n")
            assert uri.asset_type == atype
            assert uri.issue == "i"

    # --- Error cases ---

    def test_parse_rejects_wrong_scheme(self) -> None:
        with pytest.raises(InvalidComicURI, match="scheme"):
            parse_comic_uri("http://proj/characters/name")

    def test_parse_rejects_unknown_project_scoped_type(self) -> None:
        with pytest.raises(InvalidComicURI, match="Cannot parse"):
            parse_comic_uri("comic://proj/bogus/name")

    def test_parse_rejects_unknown_issue_scoped_type(self) -> None:
        with pytest.raises(InvalidComicURI, match="Unknown issue-scoped type"):
            parse_comic_uri("comic://proj/issues/i/bogus/name")

    def test_parse_rejects_empty_project(self) -> None:
        with pytest.raises(InvalidComicURI, match="project"):
            parse_comic_uri("comic:///characters/name")

    def test_parse_rejects_empty_name_project_scoped(self) -> None:
        with pytest.raises(InvalidComicURI, match="empty"):
            parse_comic_uri("comic://proj/characters/")

    def test_parse_rejects_empty_issue_segment(self) -> None:
        with pytest.raises(InvalidComicURI, match="empty"):
            parse_comic_uri("comic://proj/issues//panels/name")

    def test_parse_rejects_invalid_version(self) -> None:
        with pytest.raises(InvalidComicURI, match="version"):
            parse_comic_uri("comic://proj/characters/name?v=abc")

    def test_parse_rejects_too_few_segments(self) -> None:
        with pytest.raises(InvalidComicURI, match="Cannot parse"):
            parse_comic_uri("comic://proj/only")

    def test_parse_rejects_issues_with_too_few_segments(self) -> None:
        with pytest.raises(InvalidComicURI, match="Cannot parse"):
            parse_comic_uri("comic://proj/issues/i/panels")


class TestComicURIFormatting:
    """Format ComicURI dataclass back to string."""

    def test_format_project_scoped(self) -> None:
        uri = ComicURI(project="my-proj", asset_type="characters", name="explorer")
        assert str(uri) == "comic://my-proj/characters/explorer"

    def test_format_project_scoped_with_version(self) -> None:
        uri = ComicURI(project="p", asset_type="characters", name="explorer", version=3)
        assert str(uri) == "comic://p/characters/explorer?v=3"

    def test_format_issue_scoped(self) -> None:
        uri = ComicURI(project="my-proj", issue="issue-001", asset_type="panels", name="panel_01")
        assert str(uri) == "comic://my-proj/issues/issue-001/panels/panel_01"

    def test_format_issue_scoped_with_version(self) -> None:
        uri = ComicURI(project="p", issue="i", asset_type="covers", name="cover", version=2)
        assert str(uri) == "comic://p/issues/i/covers/cover?v=2"

    def test_roundtrip_project_scoped(self) -> None:
        original = "comic://my-comic/characters/explorer?v=2"
        assert str(parse_comic_uri(original)) == original

    def test_roundtrip_issue_scoped(self) -> None:
        original = "comic://my-comic/issues/issue-001/panels/panel_01?v=3"
        assert str(parse_comic_uri(original)) == original


class TestComicURIProperties:
    """Scope and version properties."""

    def test_is_project_scoped(self) -> None:
        uri = ComicURI(project="p", asset_type="characters", name="n")
        assert uri.is_project_scoped is True
        assert uri.is_issue_scoped is False

    def test_is_issue_scoped(self) -> None:
        uri = ComicURI(project="p", issue="i", asset_type="panels", name="n")
        assert uri.is_project_scoped is False
        assert uri.is_issue_scoped is True

    def test_is_latest_when_no_version(self) -> None:
        uri = ComicURI(project="p", asset_type="characters", name="n")
        assert uri.is_latest is True

    def test_is_not_latest_when_version_set(self) -> None:
        uri = ComicURI(project="p", asset_type="characters", name="n", version=1)
        assert uri.is_latest is False


class TestComicURIBuilders:
    """Convenience class methods for building URIs from components."""

    def test_for_asset(self) -> None:
        uri = ComicURI.for_asset("proj", "issue-001", "panels", "panel_01", version=2)
        assert str(uri) == "comic://proj/issues/issue-001/panels/panel_01?v=2"
        assert uri.issue == "issue-001"

    def test_for_asset_latest(self) -> None:
        uri = ComicURI.for_asset("proj", "issue-001", "covers", "cover")
        assert uri.version is None
        assert str(uri) == "comic://proj/issues/issue-001/covers/cover"

    def test_for_character(self) -> None:
        uri = ComicURI.for_character("proj", "explorer")
        assert uri.asset_type == "characters"
        assert uri.issue is None
        assert str(uri) == "comic://proj/characters/explorer"

    def test_for_character_with_version(self) -> None:
        uri = ComicURI.for_character("proj", "explorer", version=2)
        assert str(uri) == "comic://proj/characters/explorer?v=2"

    def test_for_style(self) -> None:
        uri = ComicURI.for_style("proj", "manga")
        assert uri.asset_type == "styles"
        assert uri.issue is None
        assert str(uri) == "comic://proj/styles/manga"

    def test_for_style_with_version(self) -> None:
        uri = ComicURI.for_style("proj", "manga", version=1)
        assert str(uri) == "comic://proj/styles/manga?v=1"


class TestComicURIRepr:
    """ComicURI has a custom __repr__."""

    def test_repr_project_scoped(self) -> None:
        uri = ComicURI(project="my-proj", asset_type="characters", name="explorer")
        assert repr(uri) == "ComicURI('comic://my-proj/characters/explorer')"

    def test_repr_issue_scoped_with_version(self) -> None:
        uri = ComicURI(project="p", issue="i", asset_type="covers", name="cover", version=3)
        assert repr(uri) == "ComicURI('comic://p/issues/i/covers/cover?v=3')"
```

**Step 2: Run tests to verify they fail**

```bash
cd modules/tool-comic-assets && python -m pytest tests/test_comic_uri.py -v
```

Expected: Multiple FAIL (old parser rejects 3-segment and 5-segment URIs, old builders have wrong signatures).

**Step 3: Rewrite `comic_uri.py` with v2 implementation**

Replace the entire contents of `modules/tool-comic-assets/amplifier_module_comic_assets/comic_uri.py` with:

```python
"""comic:// URI protocol — universal asset identifier (v2: scope-aware).

Project-scoped format (characters, styles):
    comic://project/collection/name[?v=N]

Issue-scoped format (panels, covers, storyboards, etc.):
    comic://project/issues/issue-name/collection/name[?v=N]

When version is absent, resolution defaults to latest.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

# -- Scope-aware type constants -----------------------------------------------

PROJECT_SCOPED_TYPES = frozenset({"characters", "styles"})

ISSUE_SCOPED_TYPES = frozenset({
    "panels",
    "covers",
    "storyboards",
    "research",
    "finals",
    "avatars",
    "qa_screenshots",
})

ALL_URI_TYPES = PROJECT_SCOPED_TYPES | ISSUE_SCOPED_TYPES

# Mapping from v1 singular types (used in service layer) to v2 plural URI types.
_SINGULAR_TO_PLURAL: dict[str, str] = {
    "character": "characters",
    "style": "styles",
    "panel": "panels",
    "cover": "covers",
    "storyboard": "storyboards",
    "research": "research",
    "final": "finals",
    "avatar": "avatars",
    "qa_screenshot": "qa_screenshots",
}

_PLURAL_TO_SINGULAR: dict[str, str] = {v: k for k, v in _SINGULAR_TO_PLURAL.items()}


def pluralize_type(singular: str) -> str:
    """Convert a v1 singular asset type to v2 plural collection name."""
    return _SINGULAR_TO_PLURAL.get(singular, singular)


def singularize_type(plural: str) -> str:
    """Convert a v2 plural collection name to v1 singular asset type."""
    return _PLURAL_TO_SINGULAR.get(plural, plural)


class InvalidComicURI(ValueError):
    """Raised when a string cannot be parsed as a valid comic:// URI."""


@dataclass(frozen=True, slots=True)
class ComicURI:
    """Parsed comic:// URI (v2: scope-aware).

    Attributes:
        project: Project identifier (slugified).
        asset_type: Pluralized collection name ("characters", "panels", etc.).
        name: Asset name within the collection.
        issue: Issue identifier, or None for project-scoped resources.
        version: Explicit version, or None for latest.
    """

    project: str
    asset_type: str
    name: str
    issue: str | None = None
    version: int | None = None

    @property
    def is_project_scoped(self) -> bool:
        """True for project-level resources (characters, styles)."""
        return self.issue is None

    @property
    def is_issue_scoped(self) -> bool:
        """True for issue-level resources (panels, covers, etc.)."""
        return self.issue is not None

    @property
    def is_latest(self) -> bool:
        """True when no explicit version is pinned."""
        return self.version is None

    def __str__(self) -> str:
        if self.issue is None:
            base = f"comic://{self.project}/{self.asset_type}/{self.name}"
        else:
            base = f"comic://{self.project}/issues/{self.issue}/{self.asset_type}/{self.name}"
        if self.version is not None:
            return f"{base}?v={self.version}"
        return base

    def __repr__(self) -> str:
        return f"ComicURI('{self}')"

    @classmethod
    def for_asset(
        cls,
        project: str,
        issue: str,
        asset_type: str,
        name: str,
        version: int | None = None,
    ) -> ComicURI:
        """Build a URI for an issue-scoped asset.

        ``asset_type`` accepts both singular ("panel") and plural ("panels").
        """
        plural = pluralize_type(asset_type)
        return cls(project=project, issue=issue, asset_type=plural, name=name, version=version)

    @classmethod
    def for_character(
        cls, project: str, name: str, *, version: int | None = None
    ) -> ComicURI:
        """Build a project-scoped character URI. No issue segment."""
        return cls(project=project, asset_type="characters", name=name, version=version)

    @classmethod
    def for_style(
        cls, project: str, name: str, *, version: int | None = None
    ) -> ComicURI:
        """Build a project-scoped style URI. No issue segment."""
        return cls(project=project, asset_type="styles", name=name, version=version)


def parse_comic_uri(raw: str) -> ComicURI:
    """Parse a comic:// URI string into a ``ComicURI``.

    Handles two formats:
    - Project-scoped: ``comic://project/collection/name[?v=N]`` (2 path segments)
    - Issue-scoped: ``comic://project/issues/issue/collection/name[?v=N]`` (4 path segments)

    Raises:
        InvalidComicURI: On any malformed input.
    """
    parsed = urlparse(raw)

    if parsed.scheme != "comic":
        raise InvalidComicURI(
            f"Invalid scheme '{parsed.scheme}' — expected 'comic' in: {raw}"
        )

    project = parsed.netloc
    if not project:
        raise InvalidComicURI(f"Missing project in URI: {raw}")

    # Parse path segments (netloc = project, path = /seg1/seg2/...)
    segments = parsed.path.split("/")[1:]  # drop leading empty string

    # Parse version from query string
    version: int | None = None
    if parsed.query:
        qs = parse_qs(parsed.query)
        v_values = qs.get("v")
        if v_values:
            try:
                version = int(v_values[0])
            except (ValueError, IndexError):
                raise InvalidComicURI(
                    f"Invalid version parameter — expected integer in: {raw}"
                )

    # Route 1: Project-scoped — comic://project/collection/name
    if len(segments) == 2 and segments[0] in PROJECT_SCOPED_TYPES:
        asset_type, name = segments
        if not name:
            raise InvalidComicURI(f"URI has empty name segment in: {raw}")
        return ComicURI(
            project=project, asset_type=asset_type, name=name, version=version
        )

    # Route 2: Issue-scoped — comic://project/issues/issue/collection/name
    if len(segments) == 4 and segments[0] == "issues":
        _, issue, asset_type, name = segments
        if not issue:
            raise InvalidComicURI(f"URI has empty issue segment in: {raw}")
        if not name:
            raise InvalidComicURI(f"URI has empty name segment in: {raw}")
        if asset_type not in ISSUE_SCOPED_TYPES:
            raise InvalidComicURI(
                f"Unknown issue-scoped type: '{asset_type}'. "
                f"Valid: {sorted(ISSUE_SCOPED_TYPES)}"
            )
        return ComicURI(
            project=project, issue=issue, asset_type=asset_type,
            name=name, version=version,
        )

    raise InvalidComicURI(f"Cannot parse URI: '{raw}'")
```

**Step 4: Update `__init__.py` exports**

In `modules/tool-comic-assets/amplifier_module_comic_assets/__init__.py`, add the new constants to the import line at line 33:

Change:
```python
from .comic_uri import ComicURI, InvalidComicURI, parse_comic_uri  # noqa: E402
```
To:
```python
from .comic_uri import (  # noqa: E402
    ALL_URI_TYPES,
    ISSUE_SCOPED_TYPES,
    PROJECT_SCOPED_TYPES,
    ComicURI,
    InvalidComicURI,
    parse_comic_uri,
    pluralize_type,
    singularize_type,
)
```

And add the new names to `__all__`:
```python
__all__ = [
    "mount",
    "ComicProjectTool",
    "ComicCharacterTool",
    "ComicAssetTool",
    "ComicStyleTool",
    "PathTraversalError",
    "ComicURI",
    "InvalidComicURI",
    "parse_comic_uri",
    "PROJECT_SCOPED_TYPES",
    "ISSUE_SCOPED_TYPES",
    "ALL_URI_TYPES",
    "pluralize_type",
    "singularize_type",
]
```

**Step 5: Run tests to verify they pass**

```bash
cd modules/tool-comic-assets && python -m pytest tests/test_comic_uri.py -v
```

Expected: All PASS.

**Step 6: Commit**

```bash
git add modules/tool-comic-assets/amplifier_module_comic_assets/comic_uri.py \
       modules/tool-comic-assets/amplifier_module_comic_assets/__init__.py \
       modules/tool-comic-assets/tests/test_comic_uri.py
git commit -m "feat(uri): implement v2 scope-aware comic:// URI protocol

Project-scoped: comic://project/collection/name[?v=N]
Issue-scoped: comic://project/issues/issue/collection/name[?v=N]

- ComicURI.issue is now Optional[str] (None for project-scoped)
- for_character/for_style no longer accept issue param
- for_asset accepts both singular and plural type names
- Parser routes on second segment: known project type → 3-seg, 'issues' → 5-seg
- All type names pluralized in URIs (panel→panels, character→characters, etc.)
- Helper functions: pluralize_type(), singularize_type()"
```

---

## WP-2: Update Service Layer (Task 2.1)

### Task 2.1: Update URI generation in service methods + fix tests

**Files:**
- Modify: `modules/tool-comic-assets/amplifier_module_comic_assets/service.py`
- Modify: `modules/tool-comic-assets/tests/test_service_uris.py`

**Step 1: Update tests to expect v2 URIs**

Replace the entire contents of `modules/tool-comic-assets/tests/test_service_uris.py` with:

```python
"""Tests for URI fields in service responses (v2: scope-aware)."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio(loop_scope="function")
async def test_store_asset_returns_uri(service, sample_png) -> None:
    await service.create_issue("test-proj", "Issue 1")
    result = await service.store_asset(
        "test-proj", "issue-001", "panel", "panel_01",
        source_path=sample_png,
    )
    assert "uri" in result
    assert result["uri"] == "comic://test-proj/issues/issue-001/panels/panel_01?v=1"


@pytest.mark.asyncio(loop_scope="function")
async def test_list_assets_returns_uris(service, sample_png) -> None:
    await service.create_issue("test-proj", "Issue 1")
    await service.store_asset("test-proj", "issue-001", "panel", "panel_01", source_path=sample_png)
    result = await service.list_assets("test-proj", "issue-001")
    assert len(result) == 1
    assert "uri" in result[0]
    assert result[0]["uri"].startswith("comic://test-proj/issues/issue-001/panels/panel_01")


@pytest.mark.asyncio(loop_scope="function")
async def test_store_character_returns_project_scoped_uri(service, sample_png) -> None:
    await service.create_issue("test-proj", "Issue 1")
    result = await service.store_character(
        "test-proj", "issue-001", "Explorer", "manga",
        role="hero", character_type="main", bundle="foundation",
        visual_traits="tall", team_markers="badge",
        distinctive_features="scar", source_path=sample_png,
    )
    assert "uri" in result
    # v2: project-scoped — no issue in URI
    assert result["uri"].startswith("comic://test-proj/characters/explorer")
    assert "issue-001" not in result["uri"]


@pytest.mark.asyncio(loop_scope="function")
async def test_store_style_returns_project_scoped_uri(service) -> None:
    await service.create_issue("test-proj", "Issue 1")
    result = await service.store_style(
        "test-proj", "issue-001", "manga", {"palette": "vibrant"},
    )
    assert "uri" in result
    # v2: project-scoped — no issue in URI
    assert result["uri"].startswith("comic://test-proj/styles/manga")
    assert "issue-001" not in result["uri"]


@pytest.mark.asyncio(loop_scope="function")
async def test_get_asset_returns_uri(service, sample_png) -> None:
    await service.create_issue("test-proj", "Issue 1")
    await service.store_asset("test-proj", "issue-001", "panel", "panel_01", source_path=sample_png)
    result = await service.get_asset("test-proj", "issue-001", "panel", "panel_01")
    assert "uri" in result
    assert result["uri"].startswith("comic://test-proj/issues/issue-001/panels/panel_01")


@pytest.mark.asyncio(loop_scope="function")
async def test_get_character_returns_project_scoped_uri(service, sample_png) -> None:
    await service.create_issue("test-proj", "Issue 1")
    await service.store_character(
        "test-proj", "issue-001", "Explorer", "manga",
        role="hero", character_type="main", bundle="foundation",
        visual_traits="tall", team_markers="badge",
        distinctive_features="scar", source_path=sample_png,
    )
    result = await service.get_character("test-proj", "Explorer")
    assert "uri" in result
    assert result["uri"].startswith("comic://test-proj/characters/explorer")
    assert "issue-001" not in result["uri"]


@pytest.mark.asyncio(loop_scope="function")
async def test_list_characters_returns_project_scoped_uris(service, sample_png) -> None:
    await service.create_issue("test-proj", "Issue 1")
    await service.store_character(
        "test-proj", "issue-001", "Explorer", "manga",
        role="hero", character_type="main", bundle="foundation",
        visual_traits="tall", team_markers="badge",
        distinctive_features="scar", source_path=sample_png,
    )
    result = await service.list_characters("test-proj")
    assert len(result) == 1
    assert "uri" in result[0]
    assert "characters/explorer" in result[0]["uri"]
    assert "issue" not in result[0]["uri"]


@pytest.mark.asyncio(loop_scope="function")
async def test_get_style_returns_project_scoped_uri(service) -> None:
    await service.create_issue("test-proj", "Issue 1")
    await service.store_style("test-proj", "issue-001", "manga", {"palette": "vibrant"})
    result = await service.get_style("test-proj", "manga")
    assert "uri" in result
    assert result["uri"].startswith("comic://test-proj/styles/manga")
    assert "issue-001" not in result["uri"]


@pytest.mark.asyncio(loop_scope="function")
async def test_list_styles_returns_project_scoped_uris(service) -> None:
    await service.create_issue("test-proj", "Issue 1")
    await service.store_style("test-proj", "issue-001", "manga", {"palette": "vibrant"})
    result = await service.list_styles("test-proj")
    assert len(result) == 1
    assert "uri" in result[0]
    assert "styles/manga" in result[0]["uri"]
    assert "issue" not in result[0]["uri"]
```

**Step 2: Run tests to verify they fail**

```bash
cd modules/tool-comic-assets && python -m pytest tests/test_service_uris.py -v
```

Expected: FAIL (old service produces `comic://proj/issue-001/character/...` instead of `comic://proj/characters/...`).

**Step 3: Update `service.py` URI generation**

Make these changes in `modules/tool-comic-assets/amplifier_module_comic_assets/service.py`:

1. **`store_character` (line 443):** Change:
   ```python
   uri = ComicURI.for_character(project_id, issue_id, char_slug, version=version)
   ```
   To:
   ```python
   uri = ComicURI.for_character(project_id, char_slug, version=version)
   ```

2. **`get_character` (lines 525-528):** Change:
   ```python
   result["uri"] = str(
       ComicURI.for_character(
           project_id, design.origin_issue_id, char_slug, version=design.version
       )
   )
   ```
   To:
   ```python
   result["uri"] = str(
       ComicURI.for_character(project_id, char_slug, version=design.version)
   )
   ```

3. **`list_characters` (lines 600-606):** Change the entire `if origin_issue_id:` block:
   ```python
   if origin_issue_id:
       entry["uri"] = str(
           ComicURI.for_character(
               project_id, origin_issue_id, char_slug,
               version=latest_style_version,
           )
       )
   ```
   To (always emit URI, no issue dependency):
   ```python
   entry["uri"] = str(
       ComicURI.for_character(
           project_id, char_slug, version=latest_style_version,
       )
   )
   ```

4. **`store_style` (line 1142):** Change:
   ```python
   uri = ComicURI.for_style(project_id, issue_id, style_slug, version=version)
   ```
   To:
   ```python
   uri = ComicURI.for_style(project_id, style_slug, version=version)
   ```

5. **`get_style` (lines 1181-1184):** Change:
   ```python
   result["uri"] = str(
       ComicURI.for_style(
           project_id, style_obj.origin_issue_id, style_slug, version=style_obj.version
       )
   )
   ```
   To:
   ```python
   result["uri"] = str(
       ComicURI.for_style(project_id, style_slug, version=style_obj.version)
   )
   ```

6. **`list_styles` (lines 1225-1231):** Change the `if origin_issue_id_for_style:` block:
   ```python
   if origin_issue_id_for_style:
       style_entry["uri"] = str(
           ComicURI.for_style(
               project_id, origin_issue_id_for_style, style_slug,
               version=latest_version,
           )
       )
   ```
   To (always emit URI):
   ```python
   style_entry["uri"] = str(
       ComicURI.for_style(project_id, style_slug, version=latest_version)
   )
   ```

Note: `store_asset`, `get_asset`, `list_assets` use `ComicURI.for_asset(project_id, issue_id, asset_type, name, ...)` which already accepts singular types and `for_asset` now pluralizes them internally via the updated `comic_uri.py`. No code changes needed for these methods.

**Step 4: Run tests to verify they pass**

```bash
cd modules/tool-comic-assets && python -m pytest tests/test_service_uris.py tests/test_comic_uri.py -v
```

Expected: All PASS.

**Step 5: Run full tool-comic-assets test suite for regressions**

```bash
cd modules/tool-comic-assets && python -m pytest -v
```

Expected: Some tests in `test_uri_input.py` may fail (they use v1 URI format). That's expected and handled in WP-3.

**Step 6: Commit**

```bash
git add modules/tool-comic-assets/amplifier_module_comic_assets/service.py \
       modules/tool-comic-assets/tests/test_service_uris.py
git commit -m "feat(service): emit project-scoped URIs for characters and styles

- store_character/get_character/list_characters: URI is comic://project/characters/name
- store_style/get_style/list_styles: URI is comic://project/styles/name
- Issue-scoped assets (store_asset/get_asset/list_assets) auto-pluralize via for_asset
- list_characters/list_styles always emit URI (no longer conditional on origin_issue_id)"
```

---

## WP-3: Update `_parse_uri_params` + URI Input Tests (Task 3.1)

### Task 3.1: Handle both URI formats in CRUD tool dispatch

**Files:**
- Modify: `modules/tool-comic-assets/amplifier_module_comic_assets/__init__.py` (the `_parse_uri_params` function)
- Modify: `modules/tool-comic-assets/tests/test_uri_input.py`

**Step 1: Rewrite URI input tests for v2 format**

Replace the entire contents of `modules/tool-comic-assets/tests/test_uri_input.py` with:

```python
"""Tests for URI input support on comic_style, comic_asset, comic_character (v2).

All three CRUD tools accept `uri` as an alternative to decomposed params.
v2 URIs use project-scoped and issue-scoped formats.
"""
from __future__ import annotations

import base64
import json

import pytest

from amplifier_module_comic_assets import (
    ComicAssetTool,
    ComicCharacterTool,
    ComicProjectTool,
    ComicStyleTool,
)

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
_PNG_B64 = base64.b64encode(_PNG).decode("ascii")

_CHAR_STORE_PARAMS = dict(
    role="protagonist",
    character_type="main",
    bundle="comic-strips",
    visual_traits="tall, blue eyes",
    team_markers="hero badge",
    distinctive_features="scar",
)


async def _setup_project(service, project: str = "uri_test_proj", title: str = "I1"):
    """Create a project+issue, return (project_id, issue_id)."""
    tool = ComicProjectTool(service)
    r = await tool.execute({"action": "create_issue", "project": project, "title": title})
    data = json.loads(r.output)
    return data["project_id"], data["issue_id"]


# ---------------------------------------------------------------------------
# comic_asset: get via issue-scoped URI
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_comic_asset_get_via_uri(service) -> None:
    """comic_asset(action='get', uri='comic://proj/issues/issue-001/panels/panel_01')."""
    pid, iid = await _setup_project(service, "asset_uri_proj", "I1")
    tool = ComicAssetTool(service)

    store = await tool.execute(
        {
            "action": "store",
            "project": pid,
            "issue": iid,
            "type": "panel",
            "name": "panel_01",
            "data": _PNG_B64,
        }
    )
    assert store.success is True

    # Retrieve via v2 issue-scoped URI
    uri = f"comic://{pid}/issues/{iid}/panels/panel_01"
    result = await tool.execute({"action": "get", "uri": uri})

    assert result.success is True
    data = json.loads(result.output)
    assert data["name"] == "panel_01"


# ---------------------------------------------------------------------------
# comic_character: get via project-scoped URI
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_comic_character_get_via_uri(service) -> None:
    """comic_character(action='get', uri='comic://proj/characters/explorer')."""
    pid, iid = await _setup_project(service, "char_uri_proj", "I1")
    tool = ComicCharacterTool(service)

    store = await tool.execute(
        {
            "action": "store",
            "project": pid,
            "issue": iid,
            "name": "explorer",
            "style": "manga",
            "data": _PNG_B64,
            **_CHAR_STORE_PARAMS,
        }
    )
    assert store.success is True

    # Retrieve via v2 project-scoped URI (no issue in URI)
    uri = f"comic://{pid}/characters/explorer"
    result = await tool.execute({"action": "get", "uri": uri})

    assert result.success is True
    data = json.loads(result.output)
    assert data["name"] == "explorer"


# ---------------------------------------------------------------------------
# comic_style: get via project-scoped URI
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_comic_style_get_via_uri(service) -> None:
    """comic_style(action='get', uri='comic://proj/styles/manga')."""
    pid, iid = await _setup_project(service, "style_uri_proj", "I1")
    tool = ComicStyleTool(service)

    store = await tool.execute(
        {
            "action": "store",
            "project": pid,
            "issue": iid,
            "name": "manga",
            "definition": {"palette": "vibrant", "line_weight": "medium"},
        }
    )
    assert store.success is True

    # Retrieve via v2 project-scoped URI
    uri = f"comic://{pid}/styles/manga"
    result = await tool.execute({"action": "get", "uri": uri})

    assert result.success is True
    data = json.loads(result.output)
    assert data["name"] == "manga"


# ---------------------------------------------------------------------------
# Explicit params take priority over URI-parsed values
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_explicit_params_override_uri(service) -> None:
    """Params explicitly provided take priority over URI-extracted values."""
    pid, iid = await _setup_project(service, "override_proj", "I1")
    tool = ComicAssetTool(service)

    for panel_name in ("panel_01", "panel_02"):
        r = await tool.execute(
            {
                "action": "store",
                "project": pid,
                "issue": iid,
                "type": "panel",
                "name": panel_name,
                "data": _PNG_B64,
            }
        )
        assert r.success is True

    # URI points to panel_01, but explicit name=panel_02 should win
    uri = f"comic://{pid}/issues/{iid}/panels/panel_01"
    result = await tool.execute(
        {
            "action": "get",
            "uri": uri,
            "project": pid,
            "issue": iid,
            "type": "panel",
            "name": "panel_02",
        }
    )

    assert result.success is True
    data = json.loads(result.output)
    assert data["name"] == "panel_02"


# ---------------------------------------------------------------------------
# Invalid URI returns a clear error
# ---------------------------------------------------------------------------


@pytest.mark.asyncio(loop_scope="function")
async def test_invalid_uri_returns_error(service) -> None:
    tool = ComicAssetTool(service)
    result = await tool.execute({"action": "get", "uri": "not-a-uri"})
    assert result.success is False
    assert "Invalid URI" in result.output


@pytest.mark.asyncio(loop_scope="function")
async def test_invalid_uri_character_tool(service) -> None:
    tool = ComicCharacterTool(service)
    result = await tool.execute({"action": "get", "uri": "not-a-uri"})
    assert result.success is False
    assert "Invalid URI" in result.output


@pytest.mark.asyncio(loop_scope="function")
async def test_invalid_uri_style_tool(service) -> None:
    tool = ComicStyleTool(service)
    result = await tool.execute({"action": "get", "uri": "not-a-uri"})
    assert result.success is False
    assert "Invalid URI" in result.output
```

**Step 2: Update `_parse_uri_params` to handle v2 URIs**

In `modules/tool-comic-assets/amplifier_module_comic_assets/__init__.py`, replace the `_parse_uri_params` function (lines 65-86) with:

```python
def _parse_uri_params(params: dict[str, Any]) -> "ToolResult | None":
    """Populate decomposed params from a ``uri`` entry using :func:`parse_comic_uri`.

    v2 URIs have two shapes:
    - Project-scoped: comic://project/collection/name → sets project, type (singularized), name
    - Issue-scoped: comic://project/issues/issue/collection/name → sets project, issue, type (singularized), name

    Applies :meth:`dict.setdefault` so that any params already supplied by the
    caller are left untouched (explicit params take priority over URI values).

    Returns a ``ToolResult`` error if the URI is malformed, or ``None`` when
    the operation succeeds (including when no ``uri`` key is present at all).
    """
    if "uri" not in params:
        return None
    try:
        parsed = parse_comic_uri(params["uri"])
        params.setdefault("project", parsed.project)
        if parsed.issue is not None:
            params.setdefault("issue", parsed.issue)
        # Service layer uses singular types; URI uses plural.
        from .comic_uri import singularize_type
        params.setdefault("type", singularize_type(parsed.asset_type))
        params.setdefault("name", parsed.name)
        if parsed.version is not None:
            params.setdefault("version", parsed.version)
    except ValueError as exc:
        return ToolResult(success=False, output=f"Invalid URI: {exc}")
    return None
```

**Step 3: Run tests to verify they pass**

```bash
cd modules/tool-comic-assets && python -m pytest tests/test_uri_input.py tests/test_comic_uri.py tests/test_service_uris.py -v
```

Expected: All PASS.

**Step 4: Run full tool-comic-assets test suite**

```bash
cd modules/tool-comic-assets && python -m pytest -v
```

Expected: All pass. If any other tests reference v1 URI format in assertions, fix them (see Step 5).

**Step 5: Fix any remaining test failures**

Check `test_removed_base64.py`, `test_preview.py`, `test_tools.py` for any v1 URI string assertions. The `test_removed_base64.py` checks that `batch_encode` is rejected — these assertions don't reference URI format, so they should pass. The `test_preview.py` tests pass project/issue/type/name decomposed, so `_parse_uri_params` isn't involved.

Scan with:
```bash
cd modules/tool-comic-assets && grep -rn 'comic://' tests/ | grep -v test_comic_uri | grep -v test_service_uris | grep -v test_uri_input
```

Fix any remaining v1 URI string literals in tests.

**Step 6: Commit**

```bash
git add modules/tool-comic-assets/amplifier_module_comic_assets/__init__.py \
       modules/tool-comic-assets/tests/test_uri_input.py
git commit -m "feat(tools): update _parse_uri_params for v2 scope-aware URIs

- Project-scoped URIs set project + type + name (no issue)
- Issue-scoped URIs set project + issue + type + name
- Type is singularized from URI plural to service singular
- Explicit params always win (setdefault semantics preserved)"
```

---

## WP-4: Update `comic_create` Tool (Task 4.1)

### Task 4.1: Update all 5 action handlers and their tests

**Files:**
- Modify: `modules/tool-comic-create/amplifier_module_comic_create/__init__.py`
- Modify: `modules/tool-comic-create/tests/test_create_character_ref.py`
- Modify: `modules/tool-comic-create/tests/test_create_panel.py`
- Modify: `modules/tool-comic-create/tests/test_create_cover.py`
- Modify: `modules/tool-comic-create/tests/test_review_asset.py`
- Modify: `modules/tool-comic-create/tests/test_assemble_comic.py`
- Modify: `modules/tool-comic-create/tests/test_integration.py`

**Step 1: Update test assertions to expect v2 URIs**

In each test file, update URI string assertions:

**`test_create_character_ref.py`:**
- Line 51: Change `assert data["uri"].startswith("comic://test-proj/issue-001/character/")` to `assert data["uri"].startswith("comic://test-proj/characters/")`

**`test_create_panel.py`:**
- Line 57: Change `"character_uris": [f"comic://{pid}/{iid}/character/explorer"]` to `"character_uris": [f"comic://{pid}/characters/explorer"]`
- Line 64: Change `assert data["uri"].startswith(f"comic://{pid}/{iid}/panel/panel_01")` to `assert data["uri"].startswith(f"comic://{pid}/issues/{iid}/panels/panel_01")`

**`test_create_cover.py`:**
- Line 44: Change `assert data["uri"].startswith("comic://test-proj/issue-001/cover/")` to `assert data["uri"].startswith("comic://test-proj/issues/issue-001/covers/")`

**`test_review_asset.py`:**
- Line 40: Change `f"comic://{pid}/{iid}/panel/panel_01"` to `f"comic://{pid}/issues/{iid}/panels/panel_01"`
- Line 46: Change `assert data["uri"] == f"comic://{pid}/{iid}/panel/panel_01"` to `assert data["uri"] == f"comic://{pid}/issues/{iid}/panels/panel_01"`
- Line 132: Change `f"comic://{pid}/{iid}/panel/panel_01"` to `f"comic://{pid}/issues/{iid}/panels/panel_01"`
- Line 171: Change `"comic://nonexistent-proj/issue-001/panel/ghost_panel"` to `"comic://nonexistent-proj/issues/issue-001/panels/ghost_panel"`
- Line 177: Change `"comic://test-proj/issue-001/panel/panel_01"` to `"comic://test-proj/issues/issue-001/panels/panel_01"`

**`test_assemble_comic.py`:**
- Line 43: Change `f"comic://{pid}/{iid}/cover/cover"` to `f"comic://{pid}/issues/{iid}/covers/cover"`
- Line 49: Change `f"comic://{pid}/{iid}/panel/panel_01"` to `f"comic://{pid}/issues/{iid}/panels/panel_01"`
- Line 53: Change `f"comic://{pid}/{iid}/panel/panel_02"` to `f"comic://{pid}/issues/{iid}/panels/panel_02"`
- Line 67: Change `f"comic://{pid}/{iid}/style/default"` to `f"comic://{pid}/styles/default"`
- Line 115: Change `f"comic://{pid}/{iid}/cover/cover"` to `f"comic://{pid}/issues/{iid}/covers/cover"`

**`test_integration.py`:**
- Line 84: Change `"comic://e2e-proj/issue-001/style/default"` to `"comic://e2e-proj/styles/default"`

**Step 2: Run tests to verify they fail**

```bash
cd modules/tool-comic-create && python -m pytest tests/ -v
```

Expected: Multiple FAIL (old code produces v1 URIs).

**Step 3: Update `__init__.py` action handlers**

In `modules/tool-comic-create/amplifier_module_comic_create/__init__.py`:

1. **`_create_character_ref` (line 211):** Change:
   ```python
   uri = ComicURI.for_character(project, issue, char_slug, version=version)
   ```
   To:
   ```python
   uri = ComicURI.for_character(project, char_slug, version=version)
   ```

2. **`_resolve_character_image_paths` (lines 217, 221):** The parser now returns `parsed.issue == None` for project-scoped character URIs. The code already calls `self._service.get_character(parsed.project, parsed.name, ...)` which ignores issue, so this works as-is. No change needed.

3. **`_create_panel` (line 287):** Change:
   ```python
   uri = ComicURI.for_asset(project, issue, "panel", name, version=version)
   ```
   To (no change needed — `for_asset` already pluralizes internally):
   ```python
   uri = ComicURI.for_asset(project, issue, "panel", name, version=version)
   ```
   This line is already correct since `for_asset` now calls `pluralize_type("panel")` → `"panels"`.

4. **`_create_cover` (line 342):** Same as panel — already correct since `for_asset` pluralizes.

5. **`_review_asset` (lines 506, 517-518):** The parser handles v2 URIs now. For issue-scoped assets, `parsed.issue` is populated; for characters, `parsed.issue` is None. Update the character branch check:
   
   Change (line 506):
   ```python
   if parsed.asset_type == "character":
   ```
   To:
   ```python
   if parsed.asset_type in ("character", "characters"):
   ```
   
   And for reference URI resolution (line 537), same change:
   ```python
   if ref_parsed.asset_type == "character":
   ```
   To:
   ```python
   if ref_parsed.asset_type in ("character", "characters"):
   ```

6. **`_resolve_image_as_data_uri` (line 586):** Same asset_type check:
   Change:
   ```python
   if parsed.asset_type == "character":
   ```
   To:
   ```python
   if parsed.asset_type in ("character", "characters"):
   ```
   
   And for the non-character branch, need to handle the fact that `parsed.issue` is now populated from the v2 issue-scoped URI. The existing code already uses `parsed.issue` in `get_asset(parsed.project, parsed.issue, ...)` — this is correct for issue-scoped URIs.

7. **`_resolve_style_css` (line 630):** Same — `get_asset` uses `parsed.issue` and the singular type. The service layer expects singular types (`"style"` not `"styles"`). We need to singularize:
   
   Change:
   ```python
   asset = await self._service.get_asset(
       parsed.project, parsed.issue, parsed.asset_type, parsed.name,
   ```
   To:
   ```python
   from amplifier_module_comic_assets.comic_uri import singularize_type
   singular_type = singularize_type(parsed.asset_type)
   asset = await self._service.get_asset(
       parsed.project, parsed.issue, singular_type, parsed.name,
   ```
   
   But wait — style URIs are project-scoped in v2, so `parsed.issue` is None. This method should use `get_style` instead. Update:
   ```python
   try:
       parsed = parse_comic_uri(style_uri)
   except ValueError:
       return ""
   try:
       style_data = await self._service.get_style(
           parsed.project, parsed.name,
           version=parsed.version, include="full",
       )
       definition = style_data.get("definition", {})
       css_content = definition.get("css", "")
       return css_content if isinstance(css_content, str) else ""
   except Exception:
       return ""
   ```

8. **For `_review_asset` non-character branch**, the service expects singular types. The URI now gives plural types. Singularize before passing to service:

   In `_review_asset`, change the non-character asset resolution:
   ```python
   asset_data = await self._service.get_asset(
       parsed.project, parsed.issue, parsed.asset_type, parsed.name,
   ```
   To:
   ```python
   from amplifier_module_comic_assets.comic_uri import singularize_type
   asset_data = await self._service.get_asset(
       parsed.project, parsed.issue, singularize_type(parsed.asset_type), parsed.name,
   ```
   
   Apply the same `singularize_type` call everywhere a parsed URI's `asset_type` is passed to a service method that expects singular types. This includes:
   - `_review_asset` main asset resolution (line ~517)
   - `_review_asset` reference resolution (line ~545)
   - `_resolve_image_as_data_uri` (line ~593)

**Step 4: Run tests to verify they pass**

```bash
cd modules/tool-comic-create && python -m pytest tests/ -v
```

Expected: All PASS.

**Step 5: Commit**

```bash
git add modules/tool-comic-create/amplifier_module_comic_create/__init__.py \
       modules/tool-comic-create/tests/
git commit -m "feat(comic_create): update all actions for v2 scope-aware URIs

- create_character_ref returns comic://project/characters/name (no issue)
- create_panel/create_cover return comic://project/issues/issue/type/name
- review_asset handles both project-scoped and issue-scoped URIs
- _resolve_image_as_data_uri singularizes types from parsed URIs
- _resolve_style_css uses get_style for project-scoped style URIs
- All test URI literals updated to v2 format"
```

---

## WP-5: Update Agent Instructions (Task 5.1)

### Task 5.1: Update all 6 agent markdown files for v2 URIs

**Files:**
- Modify: `agents/character-designer.md`
- Modify: `agents/panel-artist.md`
- Modify: `agents/cover-artist.md`
- Modify: `agents/strip-compositor.md`
- Modify: `agents/storyboard-writer.md`
- Modify: `agents/style-curator.md`

**Step 1: Search-and-replace URI patterns across all agent files**

In all 6 agent files, apply these transformations:

1. **Character URIs** — project-scoped, no issue:
   - `comic://{{project_id}}/{{issue_id}}/character/` → `comic://{{project_id}}/characters/`
   - `comic://proj/issue/character/` → `comic://proj/characters/`
   - Any `comic://.../character/the_explorer` → `comic://.../characters/the_explorer`

2. **Style URIs** — project-scoped, no issue:
   - `comic://{{project_id}}/{{issue_id}}/style/` → `comic://{{project_id}}/styles/`
   - `comic://proj/issue/style/` → `comic://proj/styles/`

3. **Panel URIs** — issue-scoped with `issues/` prefix:
   - `comic://{{project_id}}/{{issue_id}}/panel/` → `comic://{{project_id}}/issues/{{issue_id}}/panels/`

4. **Cover URIs** — issue-scoped:
   - `comic://{{project_id}}/{{issue_id}}/cover/` → `comic://{{project_id}}/issues/{{issue_id}}/covers/`

5. **Storyboard URIs** — issue-scoped:
   - `comic://{{project_id}}/{{issue_id}}/storyboard/` → `comic://{{project_id}}/issues/{{issue_id}}/storyboards/`

6. **Generic URI format descriptions** — update any text that says `comic://project/issue/type/name`:
   - Replace with: `comic://project/collection/name` (project-scoped) or `comic://project/issues/issue/collection/name` (issue-scoped)

**Specific file changes:**

**`agents/character-designer.md`:** Update all character URI examples to `comic://{{project_id}}/characters/the_explorer`. Remove any mention of issue in character URI context.

**`agents/panel-artist.md`:** Update panel URIs to `comic://{{project_id}}/issues/{{issue_id}}/panels/panel_01`. Update character_uris examples to use project-scoped format: `comic://{{project_id}}/characters/the_explorer`.

**`agents/cover-artist.md`:** Update cover URIs to `comic://{{project_id}}/issues/{{issue_id}}/covers/cover`. Character URIs to project-scoped.

**`agents/strip-compositor.md`:** Update all layout JSON examples to v2 URIs — panels, covers, characters, style. The layout JSON example should show:
```json
"style_uri": "comic://{{project_id}}/styles/manga",
"cover": {"uri": "comic://{{project_id}}/issues/{{issue_id}}/covers/cover"},
"characters": [{"uri": "comic://{{project_id}}/characters/the_explorer"}],
"pages": [{"panels": [{"uri": "comic://{{project_id}}/issues/{{issue_id}}/panels/panel_01"}]}]
```

**`agents/storyboard-writer.md`:** Update storyboard URI example to `comic://{{project_id}}/issues/{{issue_id}}/storyboards/storyboard`. Update character_list URI format in storyboard JSON example.

**`agents/style-curator.md`:** Update style URI example to `comic://{{project_id}}/styles/<style_name>`.

**Step 2: Verify no v1 URIs remain**

```bash
grep -rn 'comic://.*/.*/character/' agents/
grep -rn 'comic://.*/.*/style/' agents/
grep -rn 'comic://.*/.*/panel/' agents/ | grep -v '/issues/'
grep -rn 'comic://.*/.*/cover/' agents/ | grep -v '/issues/'
```

Expected: No matches (all converted to v2).

**Step 3: Commit**

```bash
git add agents/
git commit -m "docs(agents): update all 6 agent instructions for v2 URI format

- Character/style URIs: comic://project/characters/name (project-scoped)
- Panel/cover/storyboard URIs: comic://project/issues/issue/collection/name
- Layout JSON examples updated with v2 URIs
- Character references in storyboard use project-scoped URIs with ?v=N"
```

---

## WP-6: Update Recipe (Task 6.1)

### Task 6.1: Update recipe context variable docs and URI examples

**Files:**
- Modify: `recipes/session-to-comic.yaml`

**Step 1: Update recipe changelog and URI references**

Add a v7.1.0 changelog entry at the top of the changelog section:

```yaml
# v7.1.0 (WP-6 URI v2):
#   - CHANGE: All comic:// URIs in recipe context and prompts now use v2
#     scope-aware format. Characters: comic://project/characters/name.
#     Panels: comic://project/issues/issue/panels/name. Styles:
#     comic://project/styles/name.
#   - NOTE: {{character_sheet}} items are now project-scoped URIs
#     (e.g., "comic://proj/characters/explorer?v=1"), not issue-scoped.
#   - NOTE: The storyboard character_list uses versioned project-scoped
#     character URIs as the cast binding for each issue.
```

Update the version line:
```yaml
version: "7.1.0"
```

Search for any `comic://` URI string literals or comments in the recipe file and update them to v2 format. The recipe primarily uses template variables (`{{character_sheet}}`, `{{panel_results}}`) which are produced by the tools at runtime, so the actual URIs are generated by the updated code. But any example URIs in comments or prompts need updating.

**Step 2: Verify no v1 URI patterns in recipe**

```bash
grep -n 'comic://' recipes/session-to-comic.yaml
```

Fix any remaining v1 patterns.

**Step 3: Commit**

```bash
git add recipes/session-to-comic.yaml
git commit -m "feat(recipe): bump to v7.1.0 with v2 URI format documentation"
```

---

## WP-7: Update Context Files (Task 7.1)

### Task 7.1: Update `context/comic-instructions.md`

**Files:**
- Modify: `context/comic-instructions.md`

**Step 1: Update URI protocol section**

In `context/comic-instructions.md`, replace the entire `## The comic:// URI Protocol` section (starting at approximately line 60) with:

```markdown
## The `comic://` URI Protocol

All assets in the pipeline are referenced using `comic://` URIs. These identifiers flow between agents, recipe stages, and tool calls. Image bytes never enter conversation context.

**Project-scoped format** (characters, styles):
`comic://project/collection/name` or `comic://project/collection/name?v=N`

**Issue-scoped format** (panels, covers, storyboards, etc.):
`comic://project/issues/issue-name/collection/name` or `comic://project/issues/issue-name/collection/name?v=N`

**Project-scoped examples:**
```
comic://my-comic/characters/the-explorer
comic://my-comic/characters/the-explorer?v=2
comic://my-comic/styles/manga
```

**Issue-scoped examples:**
```
comic://my-comic/issues/the-revenge/panels/panel_01
comic://my-comic/issues/the-revenge/covers/cover
comic://my-comic/issues/the-revenge/storyboards/main
comic://my-comic/issues/the-revenge/finals/comic
```

**Rules:**
- Characters and styles are project-scoped — they exist at the project level and are reusable across issues
- Panels, covers, storyboards, research, finals, avatars, and QA screenshots are issue-scoped
- Absence of `?v=N` means latest version
- The storyboard's `character_list` carries versioned project-scoped character URIs, making it the cast binding for each issue
- Human-readable in logs, recipe context, and debugging output
- Tools resolve URIs to disk paths internally — agents never handle file paths or bytes directly
```

Also update the `## Cross-Agent Data Flow` section to use v2 URI examples.

**Step 2: Update `bundle.md`**

In `bundle.md`, update the two lines that mention `comic://` URIs to reference the v2 format (both project-scoped and issue-scoped).

**Step 3: Commit**

```bash
git add context/comic-instructions.md bundle.md
git commit -m "docs: update context files for v2 scope-aware URI protocol

- comic-instructions.md: document both project-scoped and issue-scoped formats
- Storyboard as cast binding with versioned character URIs
- bundle.md: update URI protocol references"
```

---

## WP-8: Full Test Suite Verification (Task 8.1)

### Task 8.1: Run all 329+ tests, fix any remaining regressions

**Files:** All test files across both modules.

**Step 1: Run tool-comic-assets full suite**

```bash
cd modules/tool-comic-assets && python -m pytest -v
```

Expected: All pass. If any test has a hardcoded v1 URI assertion that was missed, fix it.

**Step 2: Run tool-comic-create full suite**

```bash
cd modules/tool-comic-create && python -m pytest -v
```

Expected: All pass.

**Step 3: Run tool-comic-image-gen full suite (sanity check)**

```bash
cd modules/tool-comic-image-gen && python -m pytest -v
```

Expected: All 132 pass (this module doesn't reference URIs).

**Step 4: Run code quality checks**

```bash
cd modules/tool-comic-assets && python -m ruff check . && python -m ruff format --check .
cd modules/tool-comic-create && python -m ruff check . && python -m ruff format --check .
```

Expected: Clean.

**Step 5: Fix any remaining issues and commit**

If any tests failed:
1. Read the failure output
2. Identify the v1 URI literal
3. Convert to v2 format
4. Re-run

```bash
git add -A
git commit -m "fix: resolve remaining v1 URI references across test suite

All 329+ tests pass with v2 scope-aware URI format."
```

---

## Summary: Dependency Graph

```
WP-1 (ComicURI core)
  ├── WP-2 (Service layer) ──┐
  ├── WP-3 (_parse_uri_params)──┤
  │                             ├── WP-4 (comic_create tool)
  │                             │     ├── WP-5 (Agent instructions)
  │                             │     ├── WP-6 (Recipe)
  │                             │     └── WP-7 (Context files)
  │                             │
  └─────────────────────────────┴── WP-8 (Full verification)
```

WP-1 first (foundation). Then WP-2 + WP-3 (can be parallel). Then WP-4 (depends on WP-2 + WP-3). Then WP-5 + WP-6 + WP-7 (parallel, docs only). Finally WP-8 (full verification).

Total: **8 work packages, 8 tasks, ~30-40 minutes of implementation**.
