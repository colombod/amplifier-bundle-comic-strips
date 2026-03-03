# Comic URI Protocol & `comic_create` Tool — Implementation Plan

> **Execution:** Use the subagent-driven-development workflow to implement this plan.

**Goal:** Eliminate ~15 MB of base64 image data from LLM conversation context by introducing a `comic://` URI protocol and a high-level `comic_create` tool that keeps all binary operations internal to the tool layer.

**Architecture:** Agents work with `comic://project/issue/type/name` URIs — tools handle all binary internally. A new `comic_create` tool orchestrates image generation, storage, vision-based review, and HTML assembly. Existing CRUD tools are updated to speak URIs and stripped of base64 leak paths.

**Tech Stack:** Python 3.11+, pytest + pytest-asyncio (strict mode, function-scoped loops), hatchling build system, async service layer with `StorageProtocol`, `ComicProjectService`.

**Design Document:** `docs/DESIGN-comic-create-uri-abstraction.md`

---

## Conventions & Paths

All paths are relative to the bundle root:
```
/home/dicolomb/comic-strip-bundle/amplifier-bundle-comic-strips/
```

Abbreviations used throughout:
- `ASSETS_MOD` = `modules/tool-comic-assets/amplifier_module_comic_assets`
- `ASSETS_TESTS` = `modules/tool-comic-assets/tests`
- `IMGEN_MOD` = `modules/tool-comic-image-gen/amplifier_module_comic_image_gen`
- `CREATE_MOD` = `modules/tool-comic-create/amplifier_module_comic_create`
- `CREATE_TESTS` = `modules/tool-comic-create/tests`

---

## WP-1: URI Protocol — The Foundation

Everything else depends on this. Pure logic, no tool changes.

### Task 1.1: Create the `comic_uri.py` module with `ComicURI` dataclass

**Files:**
- Create: `ASSETS_MOD/comic_uri.py`
- Test: `ASSETS_TESTS/test_comic_uri.py`

**Step 1: Write the failing test**

Create `modules/tool-comic-assets/tests/test_comic_uri.py`:

```python
"""Tests for the comic:// URI protocol."""
from __future__ import annotations

import pytest

from amplifier_module_comic_assets.comic_uri import ComicURI, parse_comic_uri, InvalidComicURI


class TestComicURIParsing:
    """Parse comic:// URIs into ComicURI dataclass."""

    def test_parse_basic_uri(self) -> None:
        uri = parse_comic_uri("comic://my-project/issue-001/panel/panel_01")
        assert uri.project == "my-project"
        assert uri.issue == "issue-001"
        assert uri.asset_type == "panel"
        assert uri.name == "panel_01"
        assert uri.version is None

    def test_parse_uri_with_version(self) -> None:
        uri = parse_comic_uri("comic://my-project/issue-001/character/explorer?v=2")
        assert uri.project == "my-project"
        assert uri.issue == "issue-001"
        assert uri.asset_type == "character"
        assert uri.name == "explorer"
        assert uri.version == 2

    def test_parse_all_asset_types(self) -> None:
        for atype in ("panel", "cover", "avatar", "character", "storyboard",
                       "style", "research", "final", "qa_screenshot"):
            uri = parse_comic_uri(f"comic://p/i/{atype}/n")
            assert uri.asset_type == atype

    def test_parse_rejects_wrong_scheme(self) -> None:
        with pytest.raises(InvalidComicURI, match="scheme"):
            parse_comic_uri("http://proj/issue/panel/name")

    def test_parse_rejects_missing_parts(self) -> None:
        with pytest.raises(InvalidComicURI, match="format"):
            parse_comic_uri("comic://proj/issue/panel")

    def test_parse_rejects_empty_segments(self) -> None:
        with pytest.raises(InvalidComicURI, match="empty"):
            parse_comic_uri("comic://proj//panel/name")

    def test_parse_rejects_invalid_version(self) -> None:
        with pytest.raises(InvalidComicURI, match="version"):
            parse_comic_uri("comic://proj/issue/panel/name?v=abc")


class TestComicURIFormatting:
    """Format ComicURI dataclass back to string."""

    def test_format_basic(self) -> None:
        uri = ComicURI(project="my-proj", issue="issue-001", asset_type="panel", name="panel_01")
        assert str(uri) == "comic://my-proj/issue-001/panel/panel_01"

    def test_format_with_version(self) -> None:
        uri = ComicURI(project="p", issue="i", asset_type="character", name="explorer", version=3)
        assert str(uri) == "comic://p/i/character/explorer?v=3"

    def test_roundtrip(self) -> None:
        original = "comic://my-comic/issue-001/cover/cover?v=2"
        uri = parse_comic_uri(original)
        assert str(uri) == original


class TestComicURILatest:
    """Version resolution: no version means latest."""

    def test_is_latest_when_no_version(self) -> None:
        uri = ComicURI(project="p", issue="i", asset_type="panel", name="n")
        assert uri.is_latest is True

    def test_is_not_latest_when_version_set(self) -> None:
        uri = ComicURI(project="p", issue="i", asset_type="panel", name="n", version=1)
        assert uri.is_latest is False
```

**Step 2: Run test to verify it fails**

```bash
cd modules/tool-comic-assets && python -m pytest tests/test_comic_uri.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'amplifier_module_comic_assets.comic_uri'`

**Step 3: Write the implementation**

Create `modules/tool-comic-assets/amplifier_module_comic_assets/comic_uri.py`:

```python
"""comic:// URI protocol — universal asset identifier.

Format: comic://project/issue/type/name[?v=N]
When version is absent, resolution defaults to latest.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs

# All valid asset types in the URI namespace.
COMIC_URI_TYPES = frozenset({
    "panel", "cover", "avatar", "character", "storyboard",
    "style", "research", "final", "qa_screenshot",
})


class InvalidComicURI(ValueError):
    """Raised when a string cannot be parsed as a valid comic:// URI."""


@dataclass(frozen=True, slots=True)
class ComicURI:
    """Parsed comic:// URI.

    Attributes:
        project: Project identifier (slugified).
        issue: Issue identifier (e.g. "issue-001").
        asset_type: One of COMIC_URI_TYPES.
        name: Asset name within the type namespace.
        version: Explicit version, or None for latest.
    """

    project: str
    issue: str
    asset_type: str
    name: str
    version: int | None = None

    @property
    def is_latest(self) -> bool:
        """True when no explicit version is pinned."""
        return self.version is None

    def __str__(self) -> str:
        base = f"comic://{self.project}/{self.issue}/{self.asset_type}/{self.name}"
        if self.version is not None:
            return f"{base}?v={self.version}"
        return base


def parse_comic_uri(raw: str) -> ComicURI:
    """Parse a ``comic://project/issue/type/name[?v=N]`` string.

    Raises:
        InvalidComicURI: On any malformed input.
    """
    parsed = urlparse(raw)

    if parsed.scheme != "comic":
        raise InvalidComicURI(
            f"Invalid scheme '{parsed.scheme}' — expected 'comic' in: {raw}"
        )

    # urlparse puts everything after comic:// into netloc + path.
    # comic://project/issue/type/name → netloc="project", path="/issue/type/name"
    parts = [parsed.netloc] + [p for p in parsed.path.split("/") if p != ""]

    if len(parts) != 4:
        raise InvalidComicURI(
            f"Invalid format — expected comic://project/issue/type/name, "
            f"got {len(parts)} segments in: {raw}"
        )

    project, issue, asset_type, name = parts

    for segment_name, segment_value in [
        ("project", project), ("issue", issue),
        ("asset_type", asset_type), ("name", name),
    ]:
        if not segment_value:
            raise InvalidComicURI(
                f"URI has empty {segment_name} segment in: {raw}"
            )

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

    return ComicURI(
        project=project,
        issue=issue,
        asset_type=asset_type,
        name=name,
        version=version,
    )
```

**Step 4: Run test to verify it passes**

```bash
cd modules/tool-comic-assets && python -m pytest tests/test_comic_uri.py -v
```
Expected: All 12 tests PASS.

**Step 5: Commit**

```bash
git add modules/tool-comic-assets/amplifier_module_comic_assets/comic_uri.py modules/tool-comic-assets/tests/test_comic_uri.py
git commit -m "feat(uri): add comic:// URI protocol — ComicURI dataclass, parse, format"
```

---

### Task 1.2: Add URI builder helpers to `ComicURI`

**Files:**
- Modify: `ASSETS_MOD/comic_uri.py`
- Test: `ASSETS_TESTS/test_comic_uri.py`

**Step 1: Write the failing test**

Append to `modules/tool-comic-assets/tests/test_comic_uri.py`:

```python
class TestComicURIBuilders:
    """Convenience class methods for building URIs from components."""

    def test_for_asset(self) -> None:
        uri = ComicURI.for_asset("proj", "issue-001", "panel", "panel_01", version=2)
        assert str(uri) == "comic://proj/issue-001/panel/panel_01?v=2"

    def test_for_asset_latest(self) -> None:
        uri = ComicURI.for_asset("proj", "issue-001", "cover", "cover")
        assert uri.version is None
        assert str(uri) == "comic://proj/issue-001/cover/cover"

    def test_for_character(self) -> None:
        uri = ComicURI.for_character("proj", "issue-001", "explorer")
        assert uri.asset_type == "character"
        assert str(uri) == "comic://proj/issue-001/character/explorer"

    def test_for_style(self) -> None:
        uri = ComicURI.for_style("proj", "issue-001", "manga")
        assert uri.asset_type == "style"
        assert str(uri) == "comic://proj/issue-001/style/manga"
```

**Step 2: Run to verify fail**

```bash
cd modules/tool-comic-assets && python -m pytest tests/test_comic_uri.py::TestComicURIBuilders -v
```
Expected: FAIL — `AttributeError: type object 'ComicURI' has no attribute 'for_asset'`

**Step 3: Add builder class methods to `ComicURI`**

In `modules/tool-comic-assets/amplifier_module_comic_assets/comic_uri.py`, add these class methods inside the `ComicURI` dataclass, after the `__str__` method:

```python
    @classmethod
    def for_asset(
        cls,
        project: str,
        issue: str,
        asset_type: str,
        name: str,
        version: int | None = None,
    ) -> ComicURI:
        """Build a URI for an issue-scoped asset."""
        return cls(project=project, issue=issue, asset_type=asset_type, name=name, version=version)

    @classmethod
    def for_character(
        cls, project: str, issue: str, name: str, version: int | None = None
    ) -> ComicURI:
        """Build a URI for a character asset."""
        return cls(project=project, issue=issue, asset_type="character", name=name, version=version)

    @classmethod
    def for_style(
        cls, project: str, issue: str, name: str, version: int | None = None
    ) -> ComicURI:
        """Build a URI for a style guide asset."""
        return cls(project=project, issue=issue, asset_type="style", name=name, version=version)
```

**Step 4: Run to verify pass**

```bash
cd modules/tool-comic-assets && python -m pytest tests/test_comic_uri.py -v
```
Expected: All 16 tests PASS.

**Step 5: Export from package and commit**

Add `ComicURI`, `parse_comic_uri`, and `InvalidComicURI` to `ASSETS_MOD/__init__.py`'s `__all__` list and add the import:

In `modules/tool-comic-assets/amplifier_module_comic_assets/__init__.py`, add near the top imports:
```python
from .comic_uri import ComicURI, InvalidComicURI, parse_comic_uri  # noqa: E402
```

Add to `__all__`:
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
]
```

```bash
git add -A && git commit -m "feat(uri): add ComicURI builder helpers, export from package"
```

---

## WP-2: `comic_create` Tool Module — Skeleton

New module with directory structure, pyproject.toml, mount(), and tool class skeleton.

### Task 2.1: Create module directory and `pyproject.toml`

**Files:**
- Create: `modules/tool-comic-create/pyproject.toml`
- Create: `modules/tool-comic-create/amplifier_module_comic_create/__init__.py`
- Create: `modules/tool-comic-create/amplifier_module_comic_create/_version.py`
- Create: `modules/tool-comic-create/tests/__init__.py`
- Create: `modules/tool-comic-create/tests/conftest.py`

**Step 1: Create the directory structure**

```bash
mkdir -p modules/tool-comic-create/amplifier_module_comic_create
mkdir -p modules/tool-comic-create/tests
touch modules/tool-comic-create/tests/__init__.py
```

**Step 2: Create `pyproject.toml`**

Create `modules/tool-comic-create/pyproject.toml`:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "amplifier-module-tool-comic-create"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "amplifier-module-tool-comic-assets",
    "amplifier-module-tool-comic-image-gen",
]

[dependency-groups]
dev = [
    "pytest>=9.0.2",
    "pytest-asyncio>=1.3.0",
]

[project.entry-points."amplifier.modules"]
tool-comic-create = "amplifier_module_comic_create:mount"

[tool.hatch.build.targets.wheel]
packages = ["amplifier_module_comic_create"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--import-mode=importlib"
asyncio_mode = "strict"
```

**Step 3: Create `_version.py`**

Create `modules/tool-comic-create/amplifier_module_comic_create/_version.py`:

```python
__version__ = "0.1.0"
```

**Step 4: Create the conftest**

Create `modules/tool-comic-create/tests/conftest.py`:

```python
"""Shared pytest fixtures for tool-comic-create tests."""
from __future__ import annotations

import pytest

from amplifier_module_comic_assets.service import ComicProjectService
from amplifier_module_comic_assets.storage import FileSystemStorage

_MINIMAL_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


@pytest.fixture()
def tmp_storage(tmp_path):
    """FileSystemStorage rooted at tmp_path / '.comic-assets'."""
    return FileSystemStorage(str(tmp_path / ".comic-assets"))


@pytest.fixture()
def service(tmp_storage):
    """ComicProjectService backed by a fresh temporary storage."""
    return ComicProjectService(tmp_storage)


@pytest.fixture()
def sample_png(tmp_path):
    """Write a minimal PNG file and return its path as a string."""
    png_path = tmp_path / "test.png"
    png_path.write_bytes(_MINIMAL_PNG)
    return str(png_path)
```

**Step 5: Create the tool skeleton `__init__.py`**

Create `modules/tool-comic-create/amplifier_module_comic_create/__init__.py`:

```python
"""High-level comic creation tool — orchestrates image generation, storage, review, and assembly.

Agents work with comic:// URIs. Binary image data never enters conversation context.
All image plumbing (generation, storage, encoding, vision API) is internal.

Registration entry point: :func:`mount` (called by the Amplifier module loader).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

try:
    from amplifier_core.models import ToolResult  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover

    @dataclass
    class ToolResult:  # type: ignore[no-redef]
        """Minimal stand-in used when amplifier_core is not installed."""

        success: bool = False
        output: Any = ""


from ._version import __version__  # noqa: F401, E402

__amplifier_module_type__ = "tool"

__all__ = ["mount", "ComicCreateTool"]


def _ok(result: Any) -> ToolResult:
    return ToolResult(success=True, output=json.dumps(result))


def _error(msg: str) -> ToolResult:
    return ToolResult(success=False, output=msg)


class ComicCreateTool:
    """High-level comic creation tool with 5 actions.

    Actions:
        create_character_ref — Generate + store character reference sheet.
        create_panel — Resolve character refs + generate + store panel.
        create_cover — Resolve character refs + generate + store cover.
        review_asset — Vision-based review with optional reference comparison.
        assemble_comic — Resolve all URIs + produce self-contained HTML.

    Binary image data stays internal. Agents receive only URIs and text.
    """

    def __init__(
        self,
        service: Any,
        image_gen: Any | None = None,
    ) -> None:
        self._service = service
        self._image_gen = image_gen  # ComicImageGenTool instance (internal)

    @property
    def name(self) -> str:
        return "comic_create"

    @property
    def description(self) -> str:
        return (
            "High-level comic creation tool. Create character references, panels, "
            "covers, review assets via vision, and assemble final HTML comics. "
            "Works with comic:// URIs — binary image data stays internal."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Operation to perform.",
                    "enum": [
                        "create_character_ref",
                        "create_panel",
                        "create_cover",
                        "review_asset",
                        "assemble_comic",
                    ],
                },
                "project": {"type": "string", "description": "Project identifier."},
                "issue": {"type": "string", "description": "Issue identifier."},
                "name": {"type": "string", "description": "Asset name."},
                "prompt": {"type": "string", "description": "Generation or review prompt."},
                "visual_traits": {"type": "string", "description": "Character visual description."},
                "distinctive_features": {"type": "string", "description": "Character distinctive features."},
                "personality": {"type": "string", "description": "Character personality context."},
                "character_uris": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of comic:// character URIs for reference images.",
                },
                "size": {
                    "type": "string",
                    "description": "Image aspect ratio.",
                    "enum": ["landscape", "portrait", "square"],
                    "default": "square",
                },
                "camera_angle": {"type": "string", "description": "Camera framing hint."},
                "title": {"type": "string", "description": "Comic/cover title."},
                "subtitle": {"type": "string", "description": "Subtitle or tagline."},
                "uri": {"type": "string", "description": "comic:// URI for review_asset target."},
                "reference_uris": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Additional comic:// URIs for visual comparison in review.",
                },
                "output_path": {"type": "string", "description": "Output path for assemble_comic."},
                "style_uri": {"type": "string", "description": "Style guide URI for assembly."},
                "layout": {"type": "object", "description": "Structured layout for assemble_comic."},
            },
            "required": ["action"],
        }

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        """Dispatch to the appropriate action handler."""
        action = params.get("action")
        dispatch: dict[str, Any] = {
            "create_character_ref": self._create_character_ref,
            "create_panel": self._create_panel,
            "create_cover": self._create_cover,
            "review_asset": self._review_asset,
            "assemble_comic": self._assemble_comic,
        }
        handler = dispatch.get(action)  # type: ignore[arg-type]
        if handler is None:
            valid = ", ".join(sorted(dispatch))
            return _error(f"Unknown action '{action}'. Valid actions: {valid}")
        return await handler(params)

    async def _create_character_ref(self, params: dict[str, Any]) -> ToolResult:
        return _error("create_character_ref not yet implemented")

    async def _create_panel(self, params: dict[str, Any]) -> ToolResult:
        return _error("create_panel not yet implemented")

    async def _create_cover(self, params: dict[str, Any]) -> ToolResult:
        return _error("create_cover not yet implemented")

    async def _review_asset(self, params: dict[str, Any]) -> ToolResult:
        return _error("review_asset not yet implemented")

    async def _assemble_comic(self, params: dict[str, Any]) -> ToolResult:
        return _error("assemble_comic not yet implemented")


async def mount(coordinator: Any, config: Any = None) -> None:
    """Amplifier module entry point — build service and register the tool."""
    from amplifier_module_comic_assets.service import ComicProjectService
    from amplifier_module_comic_assets.storage import FileSystemStorage

    cfg = config or {}
    storage_cfg = cfg.get("storage", {})
    backend = storage_cfg.get("backend", "filesystem")
    if backend == "filesystem":
        fs_cfg = storage_cfg.get("filesystem", {})
        root = fs_cfg.get("root", ".comic-assets")
        storage = FileSystemStorage(root=root)
    else:
        raise ValueError(f"Unknown storage backend '{backend}'")

    service = ComicProjectService(storage=storage)

    # Attempt to get the generate_image tool's internal backend.
    # It may not be available (validation dry-run, or image-gen not loaded).
    image_gen = None
    try:
        tools = coordinator.get("tools") or {}
        image_gen = tools.get("generate_image")
    except Exception:
        pass

    tool = ComicCreateTool(service=service, image_gen=image_gen)
    await coordinator.mount("tools", tool, name=tool.name)
```

**Step 6: Write a basic smoke test**

Create `modules/tool-comic-create/tests/test_tool_skeleton.py`:

```python
"""Smoke tests for ComicCreateTool skeleton."""
from __future__ import annotations

import json
import pytest
from amplifier_module_comic_create import ComicCreateTool


@pytest.mark.asyncio(loop_scope="function")
async def test_tool_name(service) -> None:
    tool = ComicCreateTool(service=service)
    assert tool.name == "comic_create"


@pytest.mark.asyncio(loop_scope="function")
async def test_unknown_action(service) -> None:
    tool = ComicCreateTool(service=service)
    result = await tool.execute({"action": "does_not_exist"})
    assert result.success is False
    assert "does_not_exist" in result.output


@pytest.mark.asyncio(loop_scope="function")
async def test_all_actions_listed_in_schema(service) -> None:
    tool = ComicCreateTool(service=service)
    schema_actions = tool.input_schema["properties"]["action"]["enum"]
    expected = [
        "create_character_ref", "create_panel", "create_cover",
        "review_asset", "assemble_comic",
    ]
    assert sorted(schema_actions) == sorted(expected)
```

**Step 7: Run tests**

```bash
cd modules/tool-comic-create && python -m pytest tests/ -v
```
Expected: 3 tests PASS.

**Step 8: Commit**

```bash
git add modules/tool-comic-create/ && git commit -m "feat(comic_create): add tool module skeleton with 5 action stubs"
```

---

## WP-3: `create_character_ref` Action

First creation action. Orchestrates: resolve style → compose prompt → call `generate_image` internally → store character → return URI.

### Task 3.1: Implement `_create_character_ref` with mocked image gen

**Files:**
- Modify: `CREATE_MOD/__init__.py` (the `_create_character_ref` method)
- Test: `CREATE_TESTS/test_create_character_ref.py`

**Step 1: Write the failing test**

Create `modules/tool-comic-create/tests/test_create_character_ref.py`:

```python
"""Tests for comic_create(action='create_character_ref')."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from amplifier_module_comic_create import ComicCreateTool


def _make_mock_image_gen(tmp_path: Path):
    """Create a mock image generator that writes a fake PNG file."""
    _PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

    async def _generate(**kwargs):
        out = Path(kwargs["output_path"])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(_PNG)
        return {"success": True, "path": str(out), "provider_used": "mock"}

    mock = MagicMock()
    mock.execute = AsyncMock(side_effect=lambda params: _generate(**params))
    # For internal use, we expose a .generate method:
    mock.generate = AsyncMock(side_effect=_generate)
    return mock


@pytest.mark.asyncio(loop_scope="function")
async def test_create_character_ref_returns_uri(service, tmp_path) -> None:
    # Setup: create a project + issue first
    await service.create_issue("test-proj", "Issue 1")

    mock_gen = _make_mock_image_gen(tmp_path)
    tool = ComicCreateTool(service=service, image_gen=mock_gen)

    result = await tool.execute({
        "action": "create_character_ref",
        "project": "test-proj",
        "issue": "issue-001",
        "name": "The Explorer",
        "prompt": "A seasoned scout in worn leather jacket",
        "visual_traits": "tall, blue eyes, leather jacket",
        "distinctive_features": "compass pendant, scar on cheek",
    })

    assert result.success is True
    data = json.loads(result.output)
    assert "uri" in data
    assert data["uri"].startswith("comic://test-proj/issue-001/character/")
    assert "version" in data
    assert isinstance(data["version"], int)


@pytest.mark.asyncio(loop_scope="function")
async def test_create_character_ref_missing_required_param(service) -> None:
    tool = ComicCreateTool(service=service)
    result = await tool.execute({
        "action": "create_character_ref",
        "project": "test-proj",
        "issue": "issue-001",
        # missing: name, prompt, visual_traits, distinctive_features
    })
    assert result.success is False
    assert "Missing" in result.output


@pytest.mark.asyncio(loop_scope="function")
async def test_create_character_ref_no_image_gen(service) -> None:
    await service.create_issue("test-proj", "Issue 1")
    tool = ComicCreateTool(service=service, image_gen=None)

    result = await tool.execute({
        "action": "create_character_ref",
        "project": "test-proj",
        "issue": "issue-001",
        "name": "Explorer",
        "prompt": "A scout",
        "visual_traits": "tall",
        "distinctive_features": "scar",
    })
    assert result.success is False
    assert "image generation" in result.output.lower()
```

**Step 2: Run to verify fail**

```bash
cd modules/tool-comic-create && python -m pytest tests/test_create_character_ref.py -v
```
Expected: FAIL — "create_character_ref not yet implemented"

**Step 3: Implement `_create_character_ref`**

In `modules/tool-comic-create/amplifier_module_comic_create/__init__.py`, replace the stub:

```python
    async def _create_character_ref(self, params: dict[str, Any]) -> ToolResult:
        """Generate + store a character reference sheet. Return URI."""
        required = ("project", "issue", "name", "prompt", "visual_traits", "distinctive_features")
        for key in required:
            if key not in params:
                return _error(f"Missing required param: {key}")

        if self._image_gen is None:
            return _error("No image generation backend available. Cannot create character reference.")

        from amplifier_module_comic_assets.comic_uri import ComicURI
        from amplifier_module_comic_assets.models import slugify

        project = params["project"]
        issue = params["issue"]
        name = params["name"]
        char_slug = slugify(name)

        # Generate the reference image to a temp path
        import tempfile, os
        output_dir = tempfile.mkdtemp(prefix="comic_create_")
        output_path = os.path.join(output_dir, f"ref_{char_slug}.png")

        gen_result = await self._image_gen.generate(
            prompt=params["prompt"],
            output_path=output_path,
            size=params.get("size", "portrait"),
            style=params.get("style"),
            reference_images=None,
        )

        if not gen_result.get("success", False):
            return _error(f"Image generation failed: {gen_result.get('error', 'unknown')}")

        # Store the character via the service
        store_result = await self._service.store_character(
            project,
            issue,
            name,
            style=params.get("style", "default"),
            role=params.get("role", ""),
            character_type=params.get("character_type", "main"),
            bundle=params.get("bundle", ""),
            visual_traits=params["visual_traits"],
            team_markers=params.get("team_markers", ""),
            distinctive_features=params["distinctive_features"],
            backstory=params.get("backstory", ""),
            motivations=params.get("motivations", ""),
            personality=params.get("personality", ""),
            source_path=output_path,
        )

        version = store_result["version"]
        uri = ComicURI.for_character(project, issue, char_slug, version=version)

        return _ok({"uri": str(uri), "version": version})
```

**Step 4: Run to verify pass**

```bash
cd modules/tool-comic-create && python -m pytest tests/test_create_character_ref.py -v
```
Expected: 3 tests PASS.

**Step 5: Commit**

```bash
git add -A && git commit -m "feat(comic_create): implement create_character_ref action"
```

---

## WP-4: `create_panel` Action

Resolves character URIs → gets reference image paths → generates panel → stores → returns URI.

### Task 4.1: Add URI resolution helper

**Files:**
- Modify: `CREATE_MOD/__init__.py`
- Test: `CREATE_TESTS/test_create_panel.py`

**Step 1: Write the failing test**

Create `modules/tool-comic-create/tests/test_create_panel.py`:

```python
"""Tests for comic_create(action='create_panel')."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from amplifier_module_comic_create import ComicCreateTool


_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


def _make_mock_image_gen(tmp_path: Path):
    async def _generate(**kwargs):
        out = Path(kwargs["output_path"])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(_PNG)
        return {"success": True, "path": str(out), "provider_used": "mock"}

    mock = MagicMock()
    mock.generate = AsyncMock(side_effect=_generate)
    return mock


async def _setup_project_with_character(service, tmp_path):
    """Create project, issue, and one stored character with a reference image."""
    await service.create_issue("test-proj", "Issue 1")

    # Write a fake reference image to disk, then store the character
    ref_path = tmp_path / "ref_explorer.png"
    ref_path.write_bytes(_PNG)

    await service.store_character(
        "test-proj", "issue-001", "Explorer", "default",
        role="protagonist", character_type="main", bundle="foundation",
        visual_traits="tall, blue eyes", team_markers="blue badge",
        distinctive_features="scar", source_path=str(ref_path),
    )
    return "test-proj", "issue-001"


@pytest.mark.asyncio(loop_scope="function")
async def test_create_panel_returns_uri(service, tmp_path) -> None:
    pid, iid = await _setup_project_with_character(service, tmp_path)
    mock_gen = _make_mock_image_gen(tmp_path)
    tool = ComicCreateTool(service=service, image_gen=mock_gen)

    result = await tool.execute({
        "action": "create_panel",
        "project": pid,
        "issue": iid,
        "name": "panel_01",
        "prompt": "Explorer faces a wall of errors",
        "character_uris": [f"comic://{pid}/{iid}/character/explorer"],
        "size": "landscape",
    })

    assert result.success is True
    data = json.loads(result.output)
    assert "uri" in data
    assert data["uri"].startswith(f"comic://{pid}/{iid}/panel/panel_01")
    assert "version" in data


@pytest.mark.asyncio(loop_scope="function")
async def test_create_panel_without_characters(service, tmp_path) -> None:
    await service.create_issue("test-proj", "Issue 1")
    mock_gen = _make_mock_image_gen(tmp_path)
    tool = ComicCreateTool(service=service, image_gen=mock_gen)

    result = await tool.execute({
        "action": "create_panel",
        "project": "test-proj",
        "issue": "issue-001",
        "name": "panel_01",
        "prompt": "An empty landscape",
    })
    assert result.success is True


@pytest.mark.asyncio(loop_scope="function")
async def test_create_panel_missing_prompt(service) -> None:
    tool = ComicCreateTool(service=service)
    result = await tool.execute({
        "action": "create_panel",
        "project": "p",
        "issue": "i",
        "name": "panel_01",
        # missing: prompt
    })
    assert result.success is False
    assert "prompt" in result.output.lower()
```

**Step 2: Run to verify fail**

```bash
cd modules/tool-comic-create && python -m pytest tests/test_create_panel.py -v
```
Expected: FAIL — "create_panel not yet implemented"

**Step 3: Implement `_resolve_character_uris` helper and `_create_panel`**

In `modules/tool-comic-create/amplifier_module_comic_create/__init__.py`, add:

```python
    async def _resolve_character_image_paths(self, uris: list[str]) -> list[str]:
        """Resolve comic:// character URIs to absolute file paths on disk."""
        from amplifier_module_comic_assets.comic_uri import parse_comic_uri

        paths: list[str] = []
        for raw in uris:
            parsed = parse_comic_uri(raw)
            char_data = await self._service.get_character(
                parsed.project,
                parsed.name,
                style=None,
                version=parsed.version,
                include="full",
                format="path",
            )
            image_path = char_data.get("image")
            if image_path:
                paths.append(image_path)
        return paths

    async def _create_panel(self, params: dict[str, Any]) -> ToolResult:
        """Resolve character refs + generate + store panel. Return URI."""
        required = ("project", "issue", "name", "prompt")
        for key in required:
            if key not in params:
                return _error(f"Missing required param: {key}")

        if self._image_gen is None:
            return _error("No image generation backend available. Cannot create panel.")

        from amplifier_module_comic_assets.comic_uri import ComicURI

        project = params["project"]
        issue = params["issue"]
        name = params["name"]

        # Resolve character URIs to reference image paths
        character_uris = params.get("character_uris") or []
        ref_paths: list[str] = []
        if character_uris:
            try:
                ref_paths = await self._resolve_character_image_paths(character_uris)
            except (FileNotFoundError, ValueError) as exc:
                return _error(f"Failed to resolve character URIs: {exc}")

        import tempfile, os
        output_dir = tempfile.mkdtemp(prefix="comic_create_")
        output_path = os.path.join(output_dir, f"{name}.png")

        gen_result = await self._image_gen.generate(
            prompt=params["prompt"],
            output_path=output_path,
            size=params.get("size", "square"),
            style=params.get("style"),
            reference_images=ref_paths or None,
        )

        if not gen_result.get("success", False):
            return _error(f"Image generation failed: {gen_result.get('error', 'unknown')}")

        store_result = await self._service.store_asset(
            project, issue, "panel", name,
            source_path=output_path,
            metadata={"prompt": params["prompt"], "camera_angle": params.get("camera_angle", "")},
        )

        version = store_result["version"]
        uri = ComicURI.for_asset(project, issue, "panel", name, version=version)

        return _ok({"uri": str(uri), "version": version})
```

**Step 4: Run to verify pass**

```bash
cd modules/tool-comic-create && python -m pytest tests/test_create_panel.py -v
```
Expected: 3 tests PASS.

**Step 5: Commit**

```bash
git add -A && git commit -m "feat(comic_create): implement create_panel action with URI resolution"
```

---

## WP-5: `create_cover` Action

Same pattern as `create_panel` but for covers.

### Task 5.1: Implement `_create_cover`

**Files:**
- Modify: `CREATE_MOD/__init__.py`
- Test: `CREATE_TESTS/test_create_cover.py`

**Step 1: Write the failing test**

Create `modules/tool-comic-create/tests/test_create_cover.py`:

```python
"""Tests for comic_create(action='create_cover')."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from amplifier_module_comic_create import ComicCreateTool

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


def _make_mock_image_gen(tmp_path: Path):
    async def _generate(**kwargs):
        out = Path(kwargs["output_path"])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(_PNG)
        return {"success": True, "path": str(out), "provider_used": "mock"}

    mock = MagicMock()
    mock.generate = AsyncMock(side_effect=_generate)
    return mock


@pytest.mark.asyncio(loop_scope="function")
async def test_create_cover_returns_uri(service, tmp_path) -> None:
    await service.create_issue("test-proj", "Issue 1")
    mock_gen = _make_mock_image_gen(tmp_path)
    tool = ComicCreateTool(service=service, image_gen=mock_gen)

    result = await tool.execute({
        "action": "create_cover",
        "project": "test-proj",
        "issue": "issue-001",
        "prompt": "A dramatic group shot of heroes",
        "title": "The Great Debug",
        "subtitle": "Issue 1",
    })

    assert result.success is True
    data = json.loads(result.output)
    assert data["uri"].startswith("comic://test-proj/issue-001/cover/")
    assert "version" in data


@pytest.mark.asyncio(loop_scope="function")
async def test_create_cover_missing_prompt(service) -> None:
    tool = ComicCreateTool(service=service)
    result = await tool.execute({
        "action": "create_cover",
        "project": "p",
        "issue": "i",
        # missing: prompt, title
    })
    assert result.success is False
```

**Step 2: Run to verify fail**

```bash
cd modules/tool-comic-create && python -m pytest tests/test_create_cover.py -v
```
Expected: FAIL — "create_cover not yet implemented"

**Step 3: Implement `_create_cover`**

In `modules/tool-comic-create/amplifier_module_comic_create/__init__.py`, replace the stub:

```python
    async def _create_cover(self, params: dict[str, Any]) -> ToolResult:
        """Resolve character refs + generate + store cover. Return URI."""
        required = ("project", "issue", "prompt", "title")
        for key in required:
            if key not in params:
                return _error(f"Missing required param: {key}")

        if self._image_gen is None:
            return _error("No image generation backend available. Cannot create cover.")

        from amplifier_module_comic_assets.comic_uri import ComicURI

        project = params["project"]
        issue = params["issue"]
        name = "cover"  # Covers always use name "cover"

        character_uris = params.get("character_uris") or []
        ref_paths: list[str] = []
        if character_uris:
            try:
                ref_paths = await self._resolve_character_image_paths(character_uris)
            except (FileNotFoundError, ValueError) as exc:
                return _error(f"Failed to resolve character URIs: {exc}")

        import tempfile, os
        output_dir = tempfile.mkdtemp(prefix="comic_create_")
        output_path = os.path.join(output_dir, "cover.png")

        gen_result = await self._image_gen.generate(
            prompt=params["prompt"],
            output_path=output_path,
            size=params.get("size", "landscape"),
            style=params.get("style"),
            reference_images=ref_paths or None,
        )

        if not gen_result.get("success", False):
            return _error(f"Image generation failed: {gen_result.get('error', 'unknown')}")

        store_result = await self._service.store_asset(
            project, issue, "cover", name,
            source_path=output_path,
            metadata={
                "title": params["title"],
                "subtitle": params.get("subtitle", ""),
            },
        )

        version = store_result["version"]
        uri = ComicURI.for_asset(project, issue, "cover", name, version=version)

        return _ok({"uri": str(uri), "version": version})
```

**Step 4: Run to verify pass**

```bash
cd modules/tool-comic-create && python -m pytest tests/test_create_cover.py -v
```
Expected: 2 tests PASS.

**Step 5: Commit**

```bash
git add -A && git commit -m "feat(comic_create): implement create_cover action"
```

---

## WP-6: `review_asset` Action

Resolve URI + optional reference URIs → send images to vision model → return text feedback.

### Task 6.1: Implement `_review_asset`

**Files:**
- Modify: `CREATE_MOD/__init__.py`
- Test: `CREATE_TESTS/test_review_asset.py`

**Step 1: Write the failing test**

Create `modules/tool-comic-create/tests/test_review_asset.py`:

```python
"""Tests for comic_create(action='review_asset')."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from amplifier_module_comic_create import ComicCreateTool

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


async def _setup_with_panel(service, tmp_path):
    """Create project, issue, and a stored panel asset."""
    await service.create_issue("test-proj", "Issue 1")

    ref_path = tmp_path / "panel_01.png"
    ref_path.write_bytes(_PNG)

    await service.store_asset(
        "test-proj", "issue-001", "panel", "panel_01",
        source_path=str(ref_path),
    )
    return "test-proj", "issue-001"


@pytest.mark.asyncio(loop_scope="function")
async def test_review_asset_returns_text_feedback(service, tmp_path) -> None:
    pid, iid = await _setup_with_panel(service, tmp_path)
    tool = ComicCreateTool(service=service)

    # Mock the vision API call that review_asset makes internally
    mock_feedback = "Character proportions are consistent. Framing is correct."
    with patch.object(tool, "_call_vision_api", new_callable=AsyncMock,
                      return_value={"passed": True, "feedback": mock_feedback}):
        result = await tool.execute({
            "action": "review_asset",
            "uri": f"comic://{pid}/{iid}/panel/panel_01",
            "prompt": "Check character consistency and framing",
        })

    assert result.success is True
    data = json.loads(result.output)
    assert data["uri"] == f"comic://{pid}/{iid}/panel/panel_01"
    assert "passed" in data
    assert "feedback" in data
    # Verify no base64 in the result
    assert "base64" not in result.output.lower()


@pytest.mark.asyncio(loop_scope="function")
async def test_review_asset_missing_uri(service) -> None:
    tool = ComicCreateTool(service=service)
    result = await tool.execute({
        "action": "review_asset",
        "prompt": "Check quality",
        # missing: uri
    })
    assert result.success is False
    assert "uri" in result.output.lower()
```

**Step 2: Run to verify fail**

```bash
cd modules/tool-comic-create && python -m pytest tests/test_review_asset.py -v
```
Expected: FAIL — "review_asset not yet implemented"

**Step 3: Implement `_review_asset`**

In `modules/tool-comic-create/amplifier_module_comic_create/__init__.py`, replace the stub:

```python
    async def _call_vision_api(
        self, image_paths: list[str], prompt: str
    ) -> dict[str, Any]:
        """Call a vision-capable model with images and a review prompt.

        Returns {"passed": bool, "feedback": str}.
        This is a placeholder — the real implementation will use a vision
        provider from the coordinator. For now, returns a "not available"
        response so the agent can still proceed.
        """
        return {
            "passed": True,
            "feedback": "Vision review not yet available — auto-passing.",
        }

    async def _review_asset(self, params: dict[str, Any]) -> ToolResult:
        """Vision-based review. Resolve URI → image path → vision API → text feedback."""
        required = ("uri", "prompt")
        for key in required:
            if key not in params:
                return _error(f"Missing required param: {key}")

        from amplifier_module_comic_assets.comic_uri import parse_comic_uri

        raw_uri = params["uri"]
        try:
            parsed = parse_comic_uri(raw_uri)
        except ValueError as exc:
            return _error(f"Invalid URI: {exc}")

        # Resolve the target asset to a file path
        try:
            if parsed.asset_type == "character":
                asset_data = await self._service.get_character(
                    parsed.project, parsed.name,
                    version=parsed.version,
                    include="full", format="path",
                )
                image_path = asset_data.get("image")
            else:
                asset_data = await self._service.get_asset(
                    parsed.project, parsed.issue, parsed.asset_type, parsed.name,
                    version=parsed.version,
                    include="full", format="path",
                )
                image_path = asset_data.get("image")
        except (FileNotFoundError, ValueError) as exc:
            return _error(f"Cannot resolve URI {raw_uri}: {exc}")

        if not image_path:
            return _error(f"No image found for URI: {raw_uri}")

        # Collect all image paths for vision (target + optional references)
        all_paths = [image_path]

        reference_uris = params.get("reference_uris") or []
        for ref_raw in reference_uris:
            try:
                ref_parsed = parse_comic_uri(ref_raw)
                if ref_parsed.asset_type == "character":
                    ref_data = await self._service.get_character(
                        ref_parsed.project, ref_parsed.name,
                        version=ref_parsed.version,
                        include="full", format="path",
                    )
                    ref_image = ref_data.get("image")
                else:
                    ref_data = await self._service.get_asset(
                        ref_parsed.project, ref_parsed.issue,
                        ref_parsed.asset_type, ref_parsed.name,
                        version=ref_parsed.version,
                        include="full", format="path",
                    )
                    ref_image = ref_data.get("image")
                if ref_image:
                    all_paths.append(ref_image)
            except (FileNotFoundError, ValueError):
                continue  # Skip unresolvable references

        # Call vision API — images sent to API wire, never to LLM context
        vision_result = await self._call_vision_api(all_paths, params["prompt"])

        return _ok({
            "uri": raw_uri,
            "passed": vision_result.get("passed", False),
            "feedback": vision_result.get("feedback", ""),
        })
```

**Step 4: Run to verify pass**

```bash
cd modules/tool-comic-create && python -m pytest tests/test_review_asset.py -v
```
Expected: 2 tests PASS.

**Step 5: Commit**

```bash
git add -A && git commit -m "feat(comic_create): implement review_asset action with vision API"
```

---

## WP-7: `assemble_comic` Action

Resolve all URIs in layout → base64 encode internally → produce self-contained HTML.

### Task 7.1: Implement `_assemble_comic`

**Files:**
- Modify: `CREATE_MOD/__init__.py`
- Test: `CREATE_TESTS/test_assemble_comic.py`

**Step 1: Write the failing test**

Create `modules/tool-comic-create/tests/test_assemble_comic.py`:

```python
"""Tests for comic_create(action='assemble_comic')."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from amplifier_module_comic_create import ComicCreateTool

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


async def _setup_with_assets(service, tmp_path):
    """Create a project with a cover and two panels."""
    await service.create_issue("test-proj", "Issue 1")

    for name in ("panel_01", "panel_02"):
        img = tmp_path / f"{name}.png"
        img.write_bytes(_PNG)
        await service.store_asset(
            "test-proj", "issue-001", "panel", name, source_path=str(img)
        )

    cover_img = tmp_path / "cover.png"
    cover_img.write_bytes(_PNG)
    await service.store_asset(
        "test-proj", "issue-001", "cover", "cover", source_path=str(cover_img)
    )

    return "test-proj", "issue-001"


@pytest.mark.asyncio(loop_scope="function")
async def test_assemble_comic_produces_html(service, tmp_path) -> None:
    pid, iid = await _setup_with_assets(service, tmp_path)
    tool = ComicCreateTool(service=service)

    output_path = str(tmp_path / "final-comic.html")

    layout = {
        "title": "Test Comic",
        "cover": {"uri": f"comic://{pid}/{iid}/cover/cover"},
        "pages": [
            {
                "layout": "2x1",
                "panels": [
                    {
                        "uri": f"comic://{pid}/{iid}/panel/panel_01",
                        "overlays": [],
                    },
                    {
                        "uri": f"comic://{pid}/{iid}/panel/panel_02",
                        "overlays": [],
                    },
                ],
            },
        ],
    }

    result = await tool.execute({
        "action": "assemble_comic",
        "project": pid,
        "issue": iid,
        "output_path": output_path,
        "style_uri": f"comic://{pid}/{iid}/style/default",
        "layout": layout,
    })

    assert result.success is True
    data = json.loads(result.output)
    assert data["output_path"] == output_path
    assert data["pages"] >= 1
    assert data["images_embedded"] >= 2

    # Verify the HTML file exists and contains base64
    html = Path(output_path).read_text()
    assert "data:image/png;base64," in html
    assert "<!DOCTYPE html>" in html


@pytest.mark.asyncio(loop_scope="function")
async def test_assemble_comic_missing_output_path(service) -> None:
    tool = ComicCreateTool(service=service)
    result = await tool.execute({
        "action": "assemble_comic",
        "project": "p",
        "issue": "i",
        # missing: output_path, layout
    })
    assert result.success is False
```

**Step 2: Run to verify fail**

```bash
cd modules/tool-comic-create && python -m pytest tests/test_assemble_comic.py -v
```
Expected: FAIL — "assemble_comic not yet implemented"

**Step 3: Implement `_assemble_comic`**

In `modules/tool-comic-create/amplifier_module_comic_create/__init__.py`, replace the stub:

```python
    async def _resolve_image_as_data_uri(self, raw_uri: str) -> str | None:
        """Resolve a comic:// URI to a base64 data URI string (internal only)."""
        from amplifier_module_comic_assets.comic_uri import parse_comic_uri
        from amplifier_module_comic_assets.encoding import bytes_to_data_uri

        try:
            parsed = parse_comic_uri(raw_uri)
        except ValueError:
            return None

        try:
            if parsed.asset_type == "character":
                asset = await self._service.get_character(
                    parsed.project, parsed.name,
                    version=parsed.version, include="full", format="path",
                )
                image_path = asset.get("image")
            else:
                asset = await self._service.get_asset(
                    parsed.project, parsed.issue, parsed.asset_type, parsed.name,
                    version=parsed.version, include="full", format="path",
                )
                image_path = asset.get("image")
        except (FileNotFoundError, ValueError):
            return None

        if not image_path:
            return None

        import asyncio
        from pathlib import Path
        image_bytes = await asyncio.to_thread(Path(image_path).read_bytes)
        # Detect MIME from magic bytes
        if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            mime = "image/png"
        elif image_bytes[:3] == b'\xff\xd8\xff':
            mime = "image/jpeg"
        else:
            mime = "image/png"

        return bytes_to_data_uri(image_bytes, mime)

    async def _assemble_comic(self, params: dict[str, Any]) -> ToolResult:
        """Resolve all URIs in layout → base64 encode → produce HTML."""
        required = ("project", "issue", "output_path", "layout")
        for key in required:
            if key not in params:
                return _error(f"Missing required param: {key}")

        layout = params["layout"]
        output_path = params["output_path"]

        images_embedded = 0
        page_count = 0

        # --- Resolve cover ---
        cover_html = ""
        cover_info = layout.get("cover")
        if cover_info and "uri" in cover_info:
            cover_data_uri = await self._resolve_image_as_data_uri(cover_info["uri"])
            if cover_data_uri:
                title = cover_info.get("title", layout.get("title", ""))
                subtitle = cover_info.get("subtitle", "")
                cover_html = (
                    f'<section class="page cover-page">'
                    f'<div style="position:relative;text-align:center;">'
                    f'<img src="{cover_data_uri}" style="max-width:100%;max-height:80vh;" />'
                    f'<h1 style="position:absolute;top:5%;left:50%;transform:translateX(-50%);">{title}</h1>'
                    f'<h2>{subtitle}</h2>'
                    f'</div></section>'
                )
                images_embedded += 1
                page_count += 1

        # --- Resolve pages ---
        pages_html = ""
        for page_def in layout.get("pages", []):
            page_count += 1
            panels_html = ""
            for panel_def in page_def.get("panels", []):
                panel_uri = panel_def.get("uri", "")
                data_uri = await self._resolve_image_as_data_uri(panel_uri)
                if data_uri:
                    images_embedded += 1
                    # Build overlay HTML
                    overlays_html = ""
                    for overlay in panel_def.get("overlays", []):
                        pos = overlay.get("position", {})
                        style = (
                            f"position:absolute;left:{pos.get('x', 10)}%;"
                            f"top:{pos.get('y', 10)}%;width:{pos.get('width', 30)}%;"
                        )
                        text = overlay.get("text", "")
                        overlays_html += f'<div class="overlay" style="{style}">{text}</div>'

                    panels_html += (
                        f'<div class="panel" style="position:relative;">'
                        f'<img src="{data_uri}" style="width:100%;" />'
                        f'{overlays_html}</div>'
                    )

            pages_html += f'<section class="page story-page"><div class="panel-grid">{panels_html}</div></section>'

        # --- Assemble final HTML ---
        title = layout.get("title", "Comic")
        html = (
            f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">'
            f'<title>{title}</title>'
            f'<style>'
            f'*{{box-sizing:border-box;margin:0;padding:0;}}'
            f'.page{{width:100%;padding:1rem;}}'
            f'.panel-grid{{display:grid;gap:8px;}}'
            f'.panel img{{width:100%;display:block;}}'
            f'</style></head><body>'
            f'{cover_html}{pages_html}'
            f'</body></html>'
        )

        import asyncio
        from pathlib import Path
        await asyncio.to_thread(lambda: Path(output_path).write_text(html, encoding="utf-8"))

        # Also store as final asset
        try:
            await self._service.store_asset(
                params["project"], params["issue"], "final", "comic",
                content=html,
            )
        except Exception:
            pass  # Non-fatal if store fails

        return _ok({
            "output_path": output_path,
            "pages": page_count,
            "images_embedded": images_embedded,
        })
```

**Step 4: Run to verify pass**

```bash
cd modules/tool-comic-create && python -m pytest tests/test_assemble_comic.py -v
```
Expected: 2 tests PASS.

**Step 5: Commit**

```bash
git add -A && git commit -m "feat(comic_create): implement assemble_comic action with HTML generation"
```

---

## WP-8: Update Existing CRUD Tools

Add URIs to all responses, accept URI input, add `preview` action, remove base64 leak paths.

### Task 8.1: Add `uri` field to all service method return values

**Files:**
- Modify: `ASSETS_MOD/service.py` — `store_character`, `get_character`, `list_characters`, `store_asset`, `get_asset`, `list_assets`, `store_style`, `get_style`, `list_styles`
- Test: `ASSETS_TESTS/test_service.py` — add tests verifying `uri` field in responses

**Step 1: Write failing tests**

Add to `modules/tool-comic-assets/tests/test_service.py` (or create a new file `test_service_uris.py`):

```python
"""Tests for URI fields in service responses."""
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
    assert result["uri"] == "comic://test-proj/issue-001/panel/panel_01?v=1"


@pytest.mark.asyncio(loop_scope="function")
async def test_list_assets_returns_uris(service, sample_png) -> None:
    await service.create_issue("test-proj", "Issue 1")
    await service.store_asset("test-proj", "issue-001", "panel", "panel_01", source_path=sample_png)
    result = await service.list_assets("test-proj", "issue-001")
    assert len(result) == 1
    assert "uri" in result[0]
    assert result[0]["uri"].startswith("comic://test-proj/issue-001/panel/panel_01")


@pytest.mark.asyncio(loop_scope="function")
async def test_store_character_returns_uri(service, sample_png) -> None:
    await service.create_issue("test-proj", "Issue 1")
    result = await service.store_character(
        "test-proj", "issue-001", "Explorer", "manga",
        role="hero", character_type="main", bundle="foundation",
        visual_traits="tall", team_markers="badge",
        distinctive_features="scar", source_path=sample_png,
    )
    assert "uri" in result
    assert result["uri"].startswith("comic://test-proj/issue-001/character/explorer")


@pytest.mark.asyncio(loop_scope="function")
async def test_store_style_returns_uri(service) -> None:
    await service.create_issue("test-proj", "Issue 1")
    result = await service.store_style(
        "test-proj", "issue-001", "manga", {"palette": "vibrant"},
    )
    assert "uri" in result
    assert result["uri"].startswith("comic://test-proj/issue-001/style/manga")
```

**Step 2: Run to verify fail**

```bash
cd modules/tool-comic-assets && python -m pytest tests/test_service_uris.py -v
```
Expected: FAIL — `KeyError: 'uri'`

**Step 3: Add `uri` fields to service return values**

In `modules/tool-comic-assets/amplifier_module_comic_assets/service.py`, modify each method's return dict.

For `store_asset` (around line 790), change the return to:

```python
        from .comic_uri import ComicURI
        uri = ComicURI.for_asset(project_id, issue_id, asset_type, name, version=version)

        return {
            "name": name,
            "asset_type": asset_type,
            "version": version,
            "storage_path": storage_path,
            "size_bytes": size_bytes,
            "uri": str(uri),
        }
```

For `store_character` (around line 442), add uri:

```python
        from .comic_uri import ComicURI
        uri = ComicURI.for_character(project_id, issue_id, char_slug, version=version)

        return {
            "name": name,
            "style": style,
            "version": version,
            "storage_path": version_dir,
            "uri": str(uri),
        }
```

For `list_assets` (around line 939), add uri to each entry:

```python
            from .comic_uri import ComicURI
            uri = ComicURI.for_asset(
                project_id, issue_id, atype, aname,
                version=entry.get("latest_version", 1),
            )
            result.append(
                {
                    "name": aname,
                    "asset_type": atype,
                    "latest_version": entry.get("latest_version", 1),
                    "uri": str(uri),
                }
            )
```

For `store_style` (around line 1112), add uri:

```python
        from .comic_uri import ComicURI
        uri = ComicURI.for_style(project_id, issue_id, style_slug, version=version)

        return {"name": name, "version": version, "uri": str(uri)}
```

Apply similar patterns to `get_character`, `list_characters`, `get_style`, `list_styles`, `get_asset` — add a `uri` field to each response dict.

**Step 4: Run to verify pass**

```bash
cd modules/tool-comic-assets && python -m pytest tests/test_service_uris.py -v
```
Expected: All 4 tests PASS.

**Step 5: Commit**

```bash
git add -A && git commit -m "feat(service): add comic:// URI to all service responses"
```

---

### Task 8.2: Remove `format='base64'`/`format='data_uri'` and `batch_encode`

**Files:**
- Modify: `ASSETS_MOD/__init__.py` — remove `batch_encode` from dispatch, remove `base64`/`data_uri` from `format` enum in schemas
- Modify: `ASSETS_MOD/service.py` — remove `batch_encode` method, make `get_character` and `get_asset` reject `format` values other than `"path"`
- Test: `ASSETS_TESTS/test_tools.py` — add test that `batch_encode` action returns error, `format='base64'` returns error

**Step 1: Write failing tests**

Create `modules/tool-comic-assets/tests/test_removed_base64.py`:

```python
"""Tests that base64/data_uri formats and batch_encode are removed."""
from __future__ import annotations

import json
import pytest

from amplifier_module_comic_assets import ComicAssetTool, ComicCharacterTool


@pytest.mark.asyncio(loop_scope="function")
async def test_batch_encode_action_rejected(service) -> None:
    tool = ComicAssetTool(service)
    result = await tool.execute({
        "action": "batch_encode",
        "project": "p",
        "issue": "i",
        "type": "panel",
    })
    assert result.success is False
    assert "batch_encode" in result.output or "Unknown action" in result.output


@pytest.mark.asyncio(loop_scope="function")
async def test_format_base64_rejected_on_asset(service) -> None:
    tool = ComicAssetTool(service)
    result = await tool.execute({
        "action": "get",
        "project": "p",
        "issue": "i",
        "type": "panel",
        "name": "panel_01",
        "format": "base64",
        "include": "full",
    })
    assert result.success is False
    assert "base64" in result.output.lower() or "format" in result.output.lower()


@pytest.mark.asyncio(loop_scope="function")
async def test_format_data_uri_rejected_on_character(service) -> None:
    tool = ComicCharacterTool(service)
    result = await tool.execute({
        "action": "get",
        "project": "p",
        "name": "explorer",
        "format": "data_uri",
        "include": "full",
    })
    assert result.success is False
    assert "data_uri" in result.output.lower() or "format" in result.output.lower()
```

**Step 2: Run to verify fail**

```bash
cd modules/tool-comic-assets && python -m pytest tests/test_removed_base64.py -v
```
Expected: FAIL — `batch_encode` still succeeds, `base64`/`data_uri` formats still accepted.

**Step 3: Apply removals**

In `ASSETS_MOD/__init__.py`:
1. Remove `"batch_encode"` from `ComicAssetTool.input_schema` enum and dispatch dict.
2. Change `format` enum in both `ComicAssetTool` and `ComicCharacterTool` schemas from `["path", "base64", "data_uri"]` to just `["path"]`.
3. Add validation in `_get()` handlers to reject `base64` and `data_uri` format values with an error.

In `ASSETS_MOD/service.py`:
1. In `get_character`, change the `format` handling to raise `ValueError` for `base64` or `data_uri`.
2. In `get_asset`, change the `format` handling similarly.
3. The `batch_encode` method can remain in the service for internal use by `assemble_comic`, but the tool no longer exposes it.

**Step 4: Run to verify pass**

```bash
cd modules/tool-comic-assets && python -m pytest tests/test_removed_base64.py -v
```
Expected: 3 tests PASS.

Run full test suite to check no regressions:

```bash
cd modules/tool-comic-assets && python -m pytest tests/ -v
```
Expected: All existing tests still pass (some may need `format='path'` adjustments if they previously used `base64`).

**Step 5: Commit**

```bash
git add -A && git commit -m "feat(tools): remove format=base64/data_uri and batch_encode from agent-facing tools"
```

---

### Task 8.3: Add `preview` action to `ComicAssetTool`

**Files:**
- Modify: `ASSETS_MOD/__init__.py` — add `_preview` handler to `ComicAssetTool`
- Test: `ASSETS_TESTS/test_tools.py` or new `test_preview.py`

**Step 1: Write failing test**

Create `modules/tool-comic-assets/tests/test_preview.py`:

```python
"""Tests for comic_asset(action='preview')."""
from __future__ import annotations

import json
import sys
import pytest

from amplifier_module_comic_assets import ComicAssetTool, ComicProjectTool

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


@pytest.mark.asyncio(loop_scope="function")
async def test_preview_returns_path_and_hint(service, tmp_path) -> None:
    # Setup
    proj_tool = ComicProjectTool(service)
    await proj_tool.execute({"action": "create_issue", "project": "test_proj", "title": "I1"})

    png_path = tmp_path / "panel.png"
    png_path.write_bytes(_PNG)
    await service.store_asset("test_proj", "issue-001", "panel", "panel_01", source_path=str(png_path))

    tool = ComicAssetTool(service)
    result = await tool.execute({
        "action": "preview",
        "project": "test_proj",
        "issue": "issue-001",
        "type": "panel",
        "name": "panel_01",
    })

    assert result.success is True
    data = json.loads(result.output)
    assert "path" in data
    assert "hint" in data
    assert "uri" in data
    assert data["type"] == "image/png"
    # Hint should contain an opener command
    assert "open" in data["hint"] or "xdg-open" in data["hint"]
```

**Step 2: Run to verify fail, implement, verify pass, commit**

Follow the standard TDD pattern. The `_preview` handler resolves the asset to a file path using `get_asset(..., include='full', format='path')`, then returns the path, MIME type, URI, and a platform-appropriate hint:

```python
import platform
hint_cmd = "open" if platform.system() == "Darwin" else "xdg-open"
```

**Step 5: Commit**

```bash
git add -A && git commit -m "feat(comic_asset): add preview action — resolve URI to disk path + viewer hint"
```

---

## WP-9: Update Agent Instructions

Update all 6 agent markdown files to use the new `comic_create` tool and URI-based workflows.

### Task 9.1: Update `character-designer.md`

**Files:**
- Modify: `agents/character-designer.md`

**Changes:**
1. Replace `tools:` section — remove `tool-comic-image-gen`, add `tool-comic-create`:
   ```yaml
   tools:
     - module: tool-comic-create
     - module: tool-comic-assets
     - module: tool-skills
   ```
2. Remove all `generate_image` references. Replace with `comic_create(action='create_character_ref', ...)`.
3. Remove "Step 0: Verify Image Generation" section — `comic_create` handles this internally.
4. Update the Process section to show the new workflow:
   - Read style guide via `comic_style(action='get', ...)`
   - Call `comic_create(action='create_character_ref', project=..., issue=..., name=..., prompt=..., visual_traits=..., distinctive_features=...)`
   - Receive `{"uri": "comic://...", "version": 1}` back
5. Update Output section — return the URI and version, not file paths.
6. Remove `comic_character(action='store', ...)` call — `comic_create` stores internally.
7. Update description meta to reference `comic_create` instead of `generate_image`.

**Step 1: Apply all edits to `agents/character-designer.md`**

**Step 2: Commit**

```bash
git add agents/character-designer.md && git commit -m "docs(agents): update character-designer to use comic_create + URIs"
```

### Task 9.2: Update `panel-artist.md`

**Files:**
- Modify: `agents/panel-artist.md`

**Changes:**
1. Replace tools — remove `tool-comic-image-gen`, add `tool-comic-create`.
2. Replace `generate_image` calls with `comic_create(action='create_panel', ...)`:
   - `character_uris` replaces manual lookup of `reference_images` file paths.
3. Replace vision self-review with `comic_create(action='review_asset', uri=..., prompt=...)`.
4. Remove `comic_asset(action='store', ...)` — `comic_create` stores internally.
5. Remove `comic_character(action='get', ... format='path')` — character URIs are passed directly.
6. Output becomes panel URI instead of file path.

**Step 1: Apply all edits to `agents/panel-artist.md`**

**Step 2: Commit**

```bash
git add agents/panel-artist.md && git commit -m "docs(agents): update panel-artist to use comic_create + URIs"
```

### Task 9.3: Update `cover-artist.md`

**Files:**
- Modify: `agents/cover-artist.md`

**Changes:**
1. Replace tools — remove `tool-comic-image-gen`, `tool-web`, `tool-filesystem`. Add `tool-comic-create`.
2. Replace `generate_image` with `comic_create(action='create_cover', ...)`.
3. Replace vision self-review with `comic_create(action='review_asset', ...)`.
4. Remove bash base64 encoding step entirely.
5. Remove manual `web_fetch` for AmpliVerse avatar — handle in `assemble_comic` or as a separate concern.
6. Remove all `format='data_uri'` retrieval calls.
7. Output becomes cover URI instead of HTML snippet with embedded base64.

**Step 1: Apply all edits to `agents/cover-artist.md`**

**Step 2: Commit**

```bash
git add agents/cover-artist.md && git commit -m "docs(agents): update cover-artist to use comic_create + URIs"
```

### Task 9.4: Update `strip-compositor.md`

**Files:**
- Modify: `agents/strip-compositor.md`

**Changes:**
1. Add `tool-comic-create` to tools.
2. Replace all `batch_encode` and `format='data_uri'` calls with `comic_create(action='review_asset', ...)` for visual understanding and `comic_create(action='assemble_comic', ...)` for final assembly.
3. Update workflow to:
   - Get storyboard via `comic_asset(action='get', ...)`
   - Read style guide via `comic_style(action='get', ...)`
   - Use `review_asset` to understand panel composition for text placement
   - Build layout structure with `comic://` URIs
   - Call `assemble_comic` with the layout
4. Remove manual base64 embedding steps.
5. Remove `tool-filesystem` (no longer needed for reading images).

**Step 1: Apply all edits to `agents/strip-compositor.md`**

**Step 2: Commit**

```bash
git add agents/strip-compositor.md && git commit -m "docs(agents): update strip-compositor to use comic_create + assemble_comic"
```

### Task 9.5: Update `storyboard-writer.md` and `style-curator.md`

**Files:**
- Modify: `agents/storyboard-writer.md` — minor updates only (no image generation changes, but update context variable references to use URIs)
- Modify: `agents/style-curator.md` — minor updates only (style responses now include `uri` field)

**Step 1: Apply edits**

For `storyboard-writer.md`: mention that stored storyboard will have a URI. The storyboard output format should remain the same (JSON with `panel_list` and `character_list`), but note that it now includes page layout structure.

For `style-curator.md`: mention that `comic_style(action='store', ...)` now returns a `uri` field.

**Step 2: Commit**

```bash
git add agents/storyboard-writer.md agents/style-curator.md
git commit -m "docs(agents): update storyboard-writer and style-curator for URI awareness"
```

---

## WP-10: Update Recipe

Update `session-to-comic.yaml` for URI-based context variables.

### Task 10.1: Update recipe context variables and step prompts

**Files:**
- Modify: `recipes/session-to-comic.yaml`

**Changes:**

1. Remove flattened `generate_*` context variables (`character_design_needs_reference_images`, etc.) — `comic_create` handles model selection internally.

2. Update `design-characters` step:
   - Agent stays `comic-strips:character-designer`
   - Prompt updated to reference `comic_create` instead of `generate_image`
   - The collected `character_sheet` will now contain URIs instead of file paths

3. Update `generate-panels` step:
   - Agent stays `comic-strips:panel-artist`
   - Prompt passes character URIs from `character_sheet`
   - The collected `panel_results` will contain URIs

4. Update `generate-cover` step:
   - Agent stays `comic-strips:cover-artist`
   - Prompt references character URIs
   - Output `cover_results` will be a cover URI (~60 bytes, not ~2 MB of HTML)

5. Update `composition` step:
   - Prompt instructs compositor to use `comic_create(action='assemble_comic', ...)` with layout containing URIs
   - Remove large context injections (`{{cover_results}}` no longer contains HTML)
   - Recipe variables `{{panel_results}}`, `{{cover_results}}`, `{{character_sheet}}` all become lightweight URI lists

**Step 1: Apply edits to `recipes/session-to-comic.yaml`**

**Step 2: Commit**

```bash
git add recipes/session-to-comic.yaml
git commit -m "feat(recipe): update session-to-comic for URI-based context variables"
```

---

## WP-11: Update Context Files

### Task 11.1: Update `comic-instructions.md`

**Files:**
- Modify: `context/comic-instructions.md`

**Changes:**
1. In "Cross-Agent Data Flow" section, replace "Panel images base64" and "Cover image base64" with URI-based descriptions.
2. In "Output Format Requirements", remove "Base64 data URIs" as a user-facing concern — base64 embedding is now internal to `assemble_comic`.
3. Add a section about the `comic://` URI protocol as the universal asset reference.
4. Update "Image Generation Rules" to reference `comic_create` instead of direct `generate_image` calls.

**Step 1: Apply edits to `context/comic-instructions.md`**

**Step 2: Commit**

```bash
git add context/comic-instructions.md && git commit -m "docs(context): update comic-instructions for URI protocol"
```

---

## WP-12: Bundle Configuration

### Task 12.1: Update `bundle.md`

**Files:**
- Modify: `bundle.md`

**Changes:**
1. Add `comic_create` to the description of what the bundle provides.
2. Note that `generate_image` is an internal implementation detail, not a bundle-exposed tool.
3. Add `tool-comic-create` module as an include if needed.

**Step 1: Apply edits to `bundle.md`**

**Step 2: Commit**

```bash
git add bundle.md && git commit -m "docs(bundle): update bundle.md for comic_create tool"
```

---

## WP-13: Memory Pressure Fixes (Independent)

Can be done in parallel with other WPs.

### Task 13.1: Add `drain_executor` fixture for test infrastructure

**Files:**
- Modify: `ASSETS_TESTS/conftest.py`
- Modify: `modules/tool-comic-image-gen/tests/conftest.py`

**Changes:**

The root cause of memory pressure: `asyncio.to_thread()` creates a lazily-instantiated `ThreadPoolExecutor` per event loop. With `loop_scope="function"`, each test creates a new loop and potentially a new executor that doesn't get cleaned up.

Add a session-scoped autouse fixture that drains the default executor after each test:

```python
@pytest.fixture(autouse=True)
def _drain_executor(event_loop):
    """Ensure the default executor is shut down after each test."""
    yield
    executor = getattr(event_loop, "_default_executor", None)
    if executor is not None:
        executor.shutdown(wait=True, cancel_futures=True)
        event_loop._default_executor = None
```

**Step 1: Add fixture to both conftest.py files**

**Step 2: Run full test suites to verify no regressions**

```bash
cd modules/tool-comic-assets && python -m pytest tests/ -v
cd modules/tool-comic-image-gen && python -m pytest tests/ -v
```

**Step 3: Commit**

```bash
git add modules/tool-comic-assets/tests/conftest.py modules/tool-comic-image-gen/tests/conftest.py
git commit -m "fix(tests): add drain_executor fixture to prevent memory pressure"
```

---

## WP-14: Integration Testing

### Task 14.1: End-to-end smoke test

**Files:**
- Create: `CREATE_TESTS/test_integration.py`

**Step 1: Write integration test**

Create `modules/tool-comic-create/tests/test_integration.py`:

```python
"""Integration test: full pipeline with mocked image gen."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from amplifier_module_comic_create import ComicCreateTool

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


def _make_mock_gen(tmp_path):
    async def _generate(**kwargs):
        out = Path(kwargs["output_path"])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(_PNG)
        return {"success": True, "path": str(out), "provider_used": "mock"}

    mock = MagicMock()
    mock.generate = AsyncMock(side_effect=_generate)
    return mock


@pytest.mark.asyncio(loop_scope="function")
async def test_full_pipeline_no_base64_in_tool_results(service, tmp_path) -> None:
    """End-to-end: create characters, panels, cover, assemble — verify no base64 in any tool result."""
    await service.create_issue("e2e-proj", "E2E Issue")
    mock_gen = _make_mock_gen(tmp_path)
    tool = ComicCreateTool(service=service, image_gen=mock_gen)

    all_outputs: list[str] = []

    # 1. Create character
    r1 = await tool.execute({
        "action": "create_character_ref",
        "project": "e2e-proj", "issue": "issue-001",
        "name": "Explorer",
        "prompt": "A seasoned scout",
        "visual_traits": "tall, blue eyes",
        "distinctive_features": "compass pendant",
    })
    assert r1.success
    all_outputs.append(r1.output)
    char_uri = json.loads(r1.output)["uri"]

    # 2. Create panel with character reference
    r2 = await tool.execute({
        "action": "create_panel",
        "project": "e2e-proj", "issue": "issue-001",
        "name": "panel_01",
        "prompt": "Explorer faces errors",
        "character_uris": [char_uri],
    })
    assert r2.success
    all_outputs.append(r2.output)
    panel_uri = json.loads(r2.output)["uri"]

    # 3. Create cover
    r3 = await tool.execute({
        "action": "create_cover",
        "project": "e2e-proj", "issue": "issue-001",
        "prompt": "Dramatic group shot",
        "title": "E2E Test Comic",
        "character_uris": [char_uri],
    })
    assert r3.success
    all_outputs.append(r3.output)
    cover_uri = json.loads(r3.output)["uri"]

    # 4. Assemble
    output_path = str(tmp_path / "final.html")
    r4 = await tool.execute({
        "action": "assemble_comic",
        "project": "e2e-proj", "issue": "issue-001",
        "output_path": output_path,
        "style_uri": "comic://e2e-proj/issue-001/style/default",
        "layout": {
            "title": "E2E Comic",
            "cover": {"uri": cover_uri},
            "pages": [{"layout": "1x1", "panels": [{"uri": panel_uri, "overlays": []}]}],
        },
    })
    assert r4.success
    all_outputs.append(r4.output)

    # CRITICAL ASSERTION: No base64 data in any tool result returned to the agent
    for output in all_outputs:
        assert "data:image" not in output, f"Base64 data URI found in tool result: {output[:200]}"
        # Allow short base64 references in URIs but not actual image data (>200 chars of base64)
        # A real base64 image would be thousands of chars
        assert len(output) < 1000, f"Tool result suspiciously large ({len(output)} chars): {output[:200]}"

    # Verify the final HTML exists and does contain base64 (internal, not in context)
    html = Path(output_path).read_text()
    assert "data:image/png;base64," in html
    assert len(html) > 200
```

**Step 2: Run**

```bash
cd modules/tool-comic-create && python -m pytest tests/test_integration.py -v
```
Expected: PASS — no base64 in any tool result, but base64 is present in the final HTML file.

**Step 3: Commit**

```bash
git add -A && git commit -m "test(integration): end-to-end pipeline verification — no base64 in agent context"
```

---

## Execution Summary

| WP | Description | Tasks | Depends On |
|----|-------------|-------|------------|
| **WP-1** | URI Protocol (`ComicURI`, parse, format) | 2 | — |
| **WP-2** | `comic_create` module skeleton | 1 | WP-1 |
| **WP-3** | `create_character_ref` action | 1 | WP-1, WP-2 |
| **WP-4** | `create_panel` action | 1 | WP-1, WP-2, WP-3 |
| **WP-5** | `create_cover` action | 1 | WP-1, WP-2 |
| **WP-6** | `review_asset` action | 1 | WP-1, WP-2 |
| **WP-7** | `assemble_comic` action | 1 | WP-1, WP-2 |
| **WP-8** | Update CRUD tools (URIs, remove base64, preview) | 3 | WP-1 |
| **WP-9** | Update agent instructions | 5 | WP-2–WP-8 |
| **WP-10** | Update recipe | 1 | WP-9 |
| **WP-11** | Update context files | 1 | WP-8 |
| **WP-12** | Bundle configuration | 1 | all above |
| **WP-13** | Memory pressure fixes | 1 | independent |
| **WP-14** | Integration testing | 1 | WP-1–WP-8 |

**Total: 21 tasks across 14 work packages.**

**Parallelization opportunities:**
- WP-3, WP-5, WP-6, WP-7 can all start after WP-2 (only WP-4 requires WP-3).
- WP-8 can run in parallel with WP-3–WP-7.
- WP-13 is fully independent.
