# Project Asset Manager Design — `tool-comic-assets`

_Date: 2026-03-03_
_Status: Design complete, ready for implementation_
_Module: `tool-comic-assets`_
_Location: `modules/tool-comic-assets/`_

---

## Table of Contents

1. [Goal](#1-goal)
2. [Background](#2-background)
3. [Domain Model](#3-domain-model)
4. [Architecture](#4-architecture)
5. [Storage Protocol & Filesystem Layout](#5-storage-protocol--filesystem-layout)
6. [Tool API Surface](#6-tool-api-surface)
7. [Domain Object Schemas](#7-domain-object-schemas)
8. [Encoding Utilities](#8-encoding-utilities)
9. [Concurrency Strategy](#9-concurrency-strategy)
10. [Agent Integration — Per-Agent Migration](#10-agent-integration--per-agent-migration)
11. [Recipe Integration](#11-recipe-integration)
12. [Module Structure](#12-module-structure)
13. [Testing Strategy](#13-testing-strategy)
14. [Success Criteria](#14-success-criteria)
15. [Deferred to V2+](#15-deferred-to-v2)

---

## 1. Goal

Build a single service component (`ComicProjectService`) exposed through four focused tools that becomes the exclusive point of control for all comic pipeline assets — replacing direct filesystem operations with a managed, versioned, project-organized system that tracks the full creative process.

## 2. Background

### What exists today

The 6-agent pipeline handles assets through scattered filesystem operations:

| Agent | Produces | Current Method | Problems |
|---|---|---|---|
| story-researcher | research JSON | Recipe context passthrough | Large blob in context, no persistence |
| style-curator | style guide | Recipe context passthrough | No reuse across issues, large blob |
| storyboard-writer | storyboard JSON | Recipe context passthrough | Large blob, no persistence |
| character-designer | `ref_<name>.png` + JSON | `generate_image` → file on CWD | No versioning, no roster, no reuse |
| panel-artist | `panel_<NN>.png` + JSON | `generate_image` → file on CWD, reads character refs as paths | Review iterations lost, no history |
| cover-artist | `cover.png`, `avatar.png` | `generate_image`, `web_fetch`, `bash(base64 -w 0 ...)` | Platform fragility, no tracking |
| strip-compositor | final HTML | `read_file`, `bash(base64 ...)`, `write_file`, deletes intermediates | Glob-and-delete cleanup, no history |

### What's wrong

1. **No project organization.** Each pipeline run produces loose files in the CWD. No concept of projects, issues, or history.
2. **No versioning.** Character design iterations, panel review attempts — all overwrite the same file. Rejected versions are lost.
3. **No reuse.** Character designs die after each run. A new story cannot reference characters from a previous one.
4. **Scattered file operations.** Four agents implement their own file management logic, base64 encoding via shell, and cleanup.
5. **Platform fragility.** `bash(command="base64 -w 0 file.png")` fails on Windows (`-w 0` is GNU coreutils).
6. **Bloated recipe context.** Full research data, style guides, storyboards, and character sheets flow through recipe context variables between steps. This consumes context window budget and makes step prompts large.
7. **No creative process record.** Review feedback, rejected attempts, iteration history — none of it is preserved.

### What V1 delivers

- All pipeline assets managed through one service, four tools
- Projects and issues organize the creative work
- Per-project character roster with cross-project retrieval
- Per-project style guides with cross-project retrieval
- Full versioning with review metadata on every version
- Base64/data-URI encoding built into retrieval — no more shell commands
- Recipe context shrinks to compact references (project ID + issue ID) instead of full payloads
- Discovery APIs for browsing projects, issues, characters, styles, assets
- Explicit cleanup only — no automatic deletes
- Async-first, storage-protocol abstracted for future cloud migration
- Zero external dependencies beyond Python stdlib

---

## 3. Domain Model

### Hierarchy

```
Workspace (.comic-assets/)
├── Project ("AmpliVerse Origins")
│   ├── Character Roster          ← project-level, cross-project retrievable
│   │   ├── The Explorer
│   │   │   ├── manga / v1        ← versioned by style AND iteration
│   │   │   ├── manga / v2
│   │   │   └── cyberpunk / v1
│   │   └── The Debugger
│   ├── Style Guides              ← project-level, cross-project retrievable
│   │   ├── manga / v1
│   │   └── custom-noir / v1
│   └── Issues
│       ├── Issue 001
│       │   ├── research / v1
│       │   ├── storyboard / v1
│       │   ├── panels / panel_01 / v1, v2
│       │   ├── cover / v1
│       │   ├── avatar / v1
│       │   ├── qa_screenshots / ...
│       │   └── final / v1
│       └── Issue 002
└── Project ("Debug Wars")
```

### Domain Objects

#### Project

Top-level container grouping related comics. Auto-created when the first issue is created if it doesn't already exist.

```python
@dataclass
class Project:
    id: str                    # Slugified name: "ampliverse-origins"
    name: str                  # Display name: "AmpliVerse Origins"
    created_at: str            # ISO 8601 timestamp
    description: str = ""
```

#### Issue

A single comic creation run within a project. One pipeline execution produces one issue.

```python
@dataclass
class Issue:
    id: str                    # "issue-001"
    project_id: str            # Parent project
    title: str                 # "The Great Refactoring"
    created_at: str            # ISO 8601 timestamp
    description: str = ""
```

#### CharacterDesign

A composite domain object — NOT just an image. Contains the full design package: visual reference images, backstory, motivations, personality, visual traits, bundle affiliation, team markers, role. Lives at the project level (the roster). Versioned along two dimensions: **style** (manga, superhero, custom/freeform) and **version** (iteration on the design within that style).

```python
@dataclass
class CharacterDesign:
    name: str                  # "The Explorer"
    project_id: str            # Which project roster this belongs to
    style: str                 # Freeform: "manga", "cyberpunk", "custom-noir"
    version: int               # Auto-incremented per (name, style) pair
    created_at: str            # ISO 8601
    origin_issue_id: str       # Which issue triggered creation

    # Design metadata (always returned)
    role: str                  # "protagonist", "antagonist", "supporting"
    character_type: str        # "main" or "supporting"
    bundle: str                # "foundation", "comic-strips", etc.
    visual_traits: str         # Key visual characteristics
    team_markers: str          # Bundle-affiliation visual elements
    distinctive_features: str  # Unique identifying features
    backstory: str = ""        # Brief background story
    motivations: str = ""      # Character motivations
    personality: str = ""      # Personality traits

    # Binary payload (only returned when include='full')
    image_path: str | None = None  # Relative path within managed storage

    # Review metadata
    review_status: str = ""    # "accepted", "rejected", ""
    review_feedback: str = ""  # Reviewer's notes on this version
    metadata: dict[str, Any] = field(default_factory=dict)  # Extensible
```

#### StyleGuide

A full style definition: prompt templates, color palettes, panel conventions, character rendering rules. Project-level, reusable across issues and cross-project retrievable.

```python
@dataclass
class StyleGuide:
    name: str                  # "manga", "custom-noir", etc. (freeform)
    project_id: str            # Which project created this
    version: int               # Auto-incremented per (name,) within project
    created_at: str            # ISO 8601
    origin_issue_id: str       # Which issue triggered creation

    # Full definition (structured content, not binary)
    definition: dict[str, Any] # Complete style guide as structured data

    # Review metadata
    review_status: str = ""
    review_feedback: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
```

#### Asset

A typed artifact within an issue. All versioned. Covers both structured content (research, storyboard) and binary content (panels, cover, avatar).

```python
ASSET_TYPES = frozenset({
    "research",         # story-researcher output (structured JSON)
    "storyboard",       # storyboard-writer output (structured JSON)
    "panel",            # panel-artist output (image + metadata)
    "cover",            # cover-artist output (image + metadata)
    "avatar",           # branding asset (image, project-level candidate)
    "qa_screenshot",    # visual review screenshots
    "final",            # assembled HTML comic
})

@dataclass
class Asset:
    name: str                  # "panel_01", "cover", "research", "storyboard"
    asset_type: str            # One of ASSET_TYPES
    project_id: str
    issue_id: str
    version: int               # Auto-incremented per (name, asset_type, issue)
    created_at: str            # ISO 8601
    mime_type: str             # "image/png", "application/json", "text/html"
    size_bytes: int            # Payload size

    # Relative path within managed storage (for binary assets)
    storage_path: str | None = None

    # Structured content (for JSON assets like research, storyboard)
    content: dict[str, Any] | str | None = None

    # Review metadata
    review_status: str = ""    # "accepted", "rejected", ""
    review_feedback: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
```

### Versioning

Every `store` operation creates a new version automatically. Version numbers are auto-incremented within their scope:

- **Characters**: per `(name, style)` within a project
- **Style guides**: per `(name,)` within a project
- **Assets**: per `(name, asset_type)` within an issue

Each version carries its own metadata, including review feedback:

```
Panel "panel_01" in Issue 001:
├── v1: { image: ..., review_status: "rejected",
│          review_feedback: "face not visible, wrong palette" }
├── v2: { image: ..., review_status: "rejected",
│          review_feedback: "better but team markers missing" }
└── v3: { image: ..., review_status: "accepted",
│          review_feedback: "consistent with style guide" }
```

The `update_metadata` operation attaches review feedback to an existing version after the review loop evaluates it.

---

## 4. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Tool Layer (4 tools)                          │
│                                                                 │
│  ComicProjectTool    ComicCharacterTool    ComicAssetTool       │
│  (comic_project)     (comic_character)     (comic_asset)        │
│                                                                 │
│  ComicStyleTool                                                 │
│  (comic_style)                                                  │
│                                                                 │
│  Thin wrappers: validate input, dispatch to service, format     │
│  ToolResult response. Each has a small, focused input_schema.   │
├─────────────────────────────────────────────────────────────────┤
│                   ComicProjectService                           │
│                                                                 │
│  Single class. All business logic: versioning, roster mgmt,     │
│  manifest I/O, name sanitization, encoding dispatch.            │
│                                                                 │
│  STATELESS about "current" project/issue. Every method          │
│  receives project_id and/or issue_id explicitly.                │
│  Recipe/agent context holds the current IDs.                    │
├─────────────────────────────────────────────────────────────────┤
│                    StorageProtocol                               │
│  (typing.Protocol — async interface)                            │
│                                                                 │
│  write_bytes · write_text · read_bytes · read_text              │
│  exists · delete · list_dir · abs_path                          │
├─────────────────────────────────────────────────────────────────┤
│              FileSystemStorage (V1)                              │
│  All I/O through asyncio.to_thread(). Root at .comic-assets/    │
│  in CWD (configurable). Simple file ops, no TOCTOU patterns.    │
│                                                                 │
│              CloudStorage (future — same protocol)               │
└─────────────────────────────────────────────────────────────────┘
```

### Key Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| **4 tools, 1 service** | Multiple thin tool facades, one service class | Smaller input schemas per tool → fewer LLM errors. Service is single class → one place for business logic |
| **Stateless service** | No `_active_issue`, no `init()` | Eliminates race conditions under `parallel:2`. Recipe context holds current IDs, passes them explicitly |
| **Store accepts path OR data** | `source_path` param or `data` param | `generate_image` writes to CWD (tool we don't control in V1), but structured content can be stored directly without intermediate file |
| **Metadata-only by default** | `get` returns metadata unless `include='full'` | Prevents agents from accidentally flooding context with base64. Opt-in to payloads |
| **No automatic deletes** | Cleanup is always explicit | Preserves full history. Cleanup is a conscious decision in the recipe with user approval |
| **Async-first** | All service + storage methods are async | Ready for cloud backends. Filesystem ops wrapped in `to_thread()` |
| **Zero external deps** | stdlib only | Module installs cleanly. Only needs Python 3.11+ (matches `tool-comic-image-gen`) |
| **Per-project roster with cross-project retrieval** | Characters and styles scoped to projects, but any project can read from another | Clear ownership (characters belong where created) with flexible reuse |

### mount() Entry Point

```python
async def mount(coordinator: Any, config: Any = None) -> None:
    """Module entry point — create service, register four tools."""
    cfg = config or {}
    root = cfg.get("storage_root", ".comic-assets")

    storage = FileSystemStorage(root=root)
    service = ComicProjectService(storage=storage)

    tools = [
        ComicProjectTool(service),
        ComicCharacterTool(service),
        ComicAssetTool(service),
        ComicStyleTool(service),
    ]
    for tool in tools:
        await coordinator.mount("tools", tool, name=tool.name)
```

---

## 5. Storage Protocol & Filesystem Layout

### StorageProtocol

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class StorageProtocol(Protocol):
    """Async storage interface. V1 is filesystem; future is cloud."""

    async def write_bytes(self, rel_path: str, data: bytes) -> int:
        """Write binary data. Creates parent dirs. Returns bytes written."""
        ...

    async def write_text(self, rel_path: str, text: str) -> int:
        """Write text data (UTF-8). Creates parent dirs. Returns bytes written."""
        ...

    async def read_bytes(self, rel_path: str) -> bytes:
        """Read binary data. Raises FileNotFoundError if missing."""
        ...

    async def read_text(self, rel_path: str) -> str:
        """Read text data (UTF-8). Raises FileNotFoundError if missing."""
        ...

    async def exists(self, rel_path: str) -> bool:
        """Check if path exists."""
        ...

    async def delete(self, rel_path: str) -> bool:
        """Delete file or directory tree. Returns True if something was deleted."""
        ...

    async def list_dir(self, rel_path: str) -> list[str]:
        """List immediate children of a directory. Returns names, not full paths."""
        ...

    async def abs_path(self, rel_path: str) -> str:
        """Resolve to absolute path. For generating paths to pass to other tools."""
        ...
```

### FileSystemStorage

```python
import asyncio
from pathlib import Path

class FileSystemStorage:
    """V1 storage backend — local filesystem via asyncio.to_thread()."""

    def __init__(self, root: str = ".comic-assets") -> None:
        self._root = Path(root).resolve()

    async def write_bytes(self, rel_path: str, data: bytes) -> int:
        def _write() -> int:
            p = self._root / rel_path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            return len(data)
        return await asyncio.to_thread(_write)

    async def write_text(self, rel_path: str, text: str) -> int:
        def _write() -> int:
            p = self._root / rel_path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
            return len(text.encode("utf-8"))
        return await asyncio.to_thread(_write)

    async def read_bytes(self, rel_path: str) -> bytes:
        return await asyncio.to_thread(
            (self._root / rel_path).read_bytes
        )

    async def read_text(self, rel_path: str) -> str:
        return await asyncio.to_thread(
            lambda: (self._root / rel_path).read_text(encoding="utf-8")
        )

    async def exists(self, rel_path: str) -> bool:
        return await asyncio.to_thread(
            (self._root / rel_path).exists
        )

    async def delete(self, rel_path: str) -> bool:
        def _delete() -> bool:
            p = self._root / rel_path
            if not p.exists():
                return False
            if p.is_dir():
                import shutil
                shutil.rmtree(p)
            else:
                p.unlink()
            return True
        return await asyncio.to_thread(_delete)

    async def list_dir(self, rel_path: str) -> list[str]:
        def _list() -> list[str]:
            p = self._root / rel_path
            if not p.is_dir():
                return []
            return sorted(e.name for e in p.iterdir())
        return await asyncio.to_thread(_list)

    async def abs_path(self, rel_path: str) -> str:
        return str(self._root / rel_path)
```

### Filesystem Layout

```
.comic-assets/
├── workspace.json                              ← workspace index for discovery
├── projects/
│   ├── ampliverse-origins/
│   │   ├── project.json                        ← project manifest
│   │   │
│   │   ├── characters/
│   │   │   ├── the_explorer/
│   │   │   │   ├── manga_v1/
│   │   │   │   │   ├── metadata.json           ← CharacterDesign fields (no binary)
│   │   │   │   │   └── reference.png           ← the image
│   │   │   │   ├── manga_v2/
│   │   │   │   │   ├── metadata.json
│   │   │   │   │   └── reference.png
│   │   │   │   └── cyberpunk_v1/
│   │   │   │       ├── metadata.json
│   │   │   │       └── reference.png
│   │   │   └── the_debugger/
│   │   │       └── manga_v1/
│   │   │           ├── metadata.json
│   │   │           └── reference.png
│   │   │
│   │   ├── styles/
│   │   │   ├── manga_v1/
│   │   │   │   └── definition.json             ← full StyleGuide definition
│   │   │   └── custom_noir_v1/
│   │   │       └── definition.json
│   │   │
│   │   └── issues/
│   │       ├── issue-001/
│   │       │   ├── issue.json                  ← issue manifest
│   │       │   ├── research/
│   │       │   │   └── v1/
│   │       │   │       └── data.json           ← structured content
│   │       │   ├── storyboard/
│   │       │   │   └── v1/
│   │       │   │       └── data.json
│   │       │   ├── panels/
│   │       │   │   ├── panel_01_v1/
│   │       │   │   │   ├── metadata.json
│   │       │   │   │   └── image.png
│   │       │   │   ├── panel_01_v2/
│   │       │   │   │   ├── metadata.json
│   │       │   │   │   └── image.png
│   │       │   │   └── panel_02_v1/
│   │       │   │       ├── metadata.json
│   │       │   │       └── image.png
│   │       │   ├── cover/
│   │       │   │   └── cover_v1/
│   │       │   │       ├── metadata.json
│   │       │   │       └── image.png
│   │       │   ├── avatar/
│   │       │   │   └── avatar_v1/
│   │       │   │       ├── metadata.json
│   │       │   │       └── image.png
│   │       │   ├── qa_screenshots/
│   │       │   │   ├── panel_01_review_v1/
│   │       │   │   │   └── image.png
│   │       │   │   └── cover_review_v1/
│   │       │   │       └── image.png
│   │       │   └── final/
│   │       │       └── v1/
│   │       │           └── comic.html
│   │       └── issue-002/
│   │           └── ...
│   │
│   └── debug-wars/
│       ├── project.json
│       ├── characters/
│       ├── styles/
│       └── issues/
│
└── (no files outside projects/ — everything is project-scoped)
```

### Manifest Files

**workspace.json** — discovery index:

```json
{
  "version": 1,
  "projects": ["ampliverse-origins", "debug-wars"],
  "updated_at": "2026-03-03T10:00:00Z"
}
```

**project.json** — project manifest:

```json
{
  "version": 1,
  "id": "ampliverse-origins",
  "name": "AmpliVerse Origins",
  "created_at": "2026-03-03T10:00:00Z",
  "description": "",
  "issues": ["issue-001", "issue-002"],
  "characters": ["the_explorer", "the_debugger"],
  "styles": ["manga", "custom_noir"]
}
```

**issue.json** — issue manifest:

```json
{
  "version": 1,
  "id": "issue-001",
  "project_id": "ampliverse-origins",
  "title": "The Great Refactoring",
  "created_at": "2026-03-03T10:00:00Z",
  "assets": {
    "research": { "latest_version": 1 },
    "storyboard": { "latest_version": 1 },
    "panel:panel_01": { "latest_version": 2 },
    "panel:panel_02": { "latest_version": 1 },
    "cover:cover": { "latest_version": 1 },
    "avatar:avatar": { "latest_version": 1 },
    "final:comic": { "latest_version": 1 }
  }
}
```

---

## 6. Tool API Surface

Four tools, 17 operations total. Each tool has a focused input schema.

### 6.1 comic_project

Project and issue lifecycle + discovery.

```python
class ComicProjectTool:
    name = "comic_project"
    description = (
        "Manage comic projects and issues. Create issues (auto-creates "
        "project if needed), list projects/issues, get issue details, "
        "and explicitly clean up stored assets."
    )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "create_issue",
                        "list_projects",
                        "list_issues",
                        "get_issue",
                        "cleanup_issue",
                        "cleanup_project",
                    ],
                    "description": "Operation to perform.",
                },
                "project": {
                    "type": "string",
                    "description": "Project name or ID.",
                },
                "issue": {
                    "type": "string",
                    "description": "Issue ID (for get/cleanup).",
                },
                "title": {
                    "type": "string",
                    "description": "Issue title (for create_issue).",
                },
                "description": {
                    "type": "string",
                    "description": "Optional description.",
                },
            },
            "required": ["action"],
        }
```

**Operations:**

| Action | Required Params | Returns |
|---|---|---|
| `create_issue` | `project`, `title` | `{ project_id, issue_id, created }` |
| `list_projects` | — | `{ projects: [{ id, name, issue_count, character_count }] }` |
| `list_issues` | `project` | `{ issues: [{ id, title, created_at, asset_count }] }` |
| `get_issue` | `project`, `issue` | `{ id, title, created_at, assets: { type: count } }` |
| `cleanup_issue` | `project`, `issue` | `{ deleted_files, freed_bytes }` |
| `cleanup_project` | `project` | `{ deleted_files, freed_bytes }` |

**Example calls:**

```python
# Start a new comic — creates project if it doesn't exist
comic_project(
    action="create_issue",
    project="AmpliVerse Origins",
    title="The Great Refactoring"
)
# → { "project_id": "ampliverse-origins", "issue_id": "issue-001", "created": true }

# Discovery: what projects exist?
comic_project(action="list_projects")
# → { "projects": [
#       { "id": "ampliverse-origins", "name": "AmpliVerse Origins",
#         "issue_count": 2, "character_count": 4 }
#   ] }

# Explicit cleanup with user approval
comic_project(action="cleanup_issue", project="ampliverse-origins", issue="issue-001")
# → { "deleted_files": 23, "freed_bytes": 15728640 }
```

### 6.2 comic_character

Character designs, roster management, cross-project retrieval.

```python
class ComicCharacterTool:
    name = "comic_character"
    description = (
        "Store, retrieve, and browse character designs in the project "
        "roster. Characters are composite: metadata + reference images, "
        "versioned by style. Supports cross-project retrieval."
    )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "store",
                        "get",
                        "list",
                        "list_versions",
                        "update_metadata",
                    ],
                    "description": "Operation to perform.",
                },
                "project": {
                    "type": "string",
                    "description": "Project name or ID.",
                },
                "issue": {
                    "type": "string",
                    "description": "Origin issue ID (for store).",
                },
                "name": {
                    "type": "string",
                    "description": "Character name.",
                },
                "style": {
                    "type": "string",
                    "description": "Style label (freeform: 'manga', 'cyberpunk', etc.).",
                },
                "version": {
                    "type": "integer",
                    "description": "Specific version. Omit for latest.",
                },
                "include": {
                    "type": "string",
                    "enum": ["metadata", "full"],
                    "default": "metadata",
                    "description": "Return metadata only (default) or include binary payload.",
                },
                "format": {
                    "type": "string",
                    "enum": ["path", "base64", "data_uri"],
                    "default": "path",
                    "description": "Payload format when include=full.",
                },
                # Fields for store action
                "role": { "type": "string" },
                "character_type": { "type": "string", "enum": ["main", "supporting"] },
                "bundle": { "type": "string" },
                "visual_traits": { "type": "string" },
                "team_markers": { "type": "string" },
                "distinctive_features": { "type": "string" },
                "backstory": { "type": "string" },
                "motivations": { "type": "string" },
                "personality": { "type": "string" },
                "source_path": {
                    "type": "string",
                    "description": "Path to image file on disk (from generate_image output).",
                },
                "data": {
                    "type": "string",
                    "description": "Image as base64 string (alternative to source_path).",
                },
                # Fields for update_metadata action
                "review_status": { "type": "string", "enum": ["accepted", "rejected"] },
                "review_feedback": { "type": "string" },
                "metadata": { "type": "object" },
            },
            "required": ["action", "project"],
        }
```

**Operations:**

| Action | Required Params | Returns |
|---|---|---|
| `store` | `project`, `issue`, `name`, `style`, design fields, `source_path` or `data` | `{ name, style, version, storage_path }` |
| `get` | `project`, `name` | Character design (metadata or full) |
| `list` | `project` | `{ characters: [{ name, styles, latest_versions }] }` |
| `list_versions` | `project`, `name` | `{ versions: [{ style, version, review_status, created_at }] }` |
| `update_metadata` | `project`, `name`, `style`, `version` | `{ updated: true }` |

**Example calls:**

```python
# character-designer stores a new character design
comic_character(
    action="store",
    project="ampliverse-origins",
    issue="issue-001",
    name="The Explorer",
    style="manga",
    role="protagonist",
    character_type="main",
    bundle="foundation",
    visual_traits="seasoned scout in worn leather jacket, alert eyes, compass pendant",
    team_markers="blue accent with compass insignia on jacket shoulder",
    distinctive_features="leather field bag, binoculars holstered on belt",
    backstory="A veteran pathfinder who navigates complex codebases",
    source_path="ref_the_explorer.png"
)
# → { "name": "the_explorer", "style": "manga", "version": 1,
#     "storage_path": "projects/ampliverse-origins/characters/the_explorer/manga_v1/reference.png" }

# panel-artist gets metadata for prompt crafting (no image data)
comic_character(
    action="get",
    project="ampliverse-origins",
    name="The Explorer",
    style="manga",
    include="metadata"
)
# → { "name": "The Explorer", "style": "manga", "version": 2,
#     "role": "protagonist", "visual_traits": "...", "team_markers": "...",
#     "distinctive_features": "...", "review_status": "accepted",
#     "image_path": null }   ← no binary payload

# panel-artist gets full path for reference_images parameter
comic_character(
    action="get",
    project="ampliverse-origins",
    name="The Explorer",
    style="manga",
    include="full",
    format="path"
)
# → { ...all metadata...,
#     "image_path": "/absolute/path/to/.comic-assets/projects/ampliverse-origins/characters/the_explorer/manga_v2/reference.png" }

# character-designer fetches from ANOTHER project as reference material
comic_character(
    action="get",
    project="debug-wars",
    name="The Explorer",
    style="cyberpunk",
    include="full",
    format="path"
)
# → character design from a different project, for use as reference

# character-designer records review feedback on the version it just evaluated
comic_character(
    action="update_metadata",
    project="ampliverse-origins",
    name="The Explorer",
    style="manga",
    version=1,
    review_status="rejected",
    review_feedback="face not visible, wrong color palette"
)
# → { "updated": true }

# Browse the full roster
comic_character(action="list", project="ampliverse-origins")
# → { "characters": [
#       { "name": "The Explorer", "styles": ["manga", "cyberpunk"],
#         "latest_versions": { "manga": 2, "cyberpunk": 1 } },
#       { "name": "The Debugger", "styles": ["manga"],
#         "latest_versions": { "manga": 1 } }
#   ] }
```

### 6.3 comic_asset

Issue-scoped assets: panels, covers, research, storyboards, QA screenshots, final.

```python
class ComicAssetTool:
    name = "comic_asset"
    description = (
        "Store, retrieve, and browse issue-scoped assets (panels, cover, "
        "research, storyboard, QA screenshots, final comic). All assets "
        "are versioned. Returns metadata by default — opt in to payloads."
    )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "store",
                        "get",
                        "list",
                        "batch_encode",
                        "update_metadata",
                    ],
                    "description": "Operation to perform.",
                },
                "project": {
                    "type": "string",
                    "description": "Project name or ID.",
                },
                "issue": {
                    "type": "string",
                    "description": "Issue ID.",
                },
                "type": {
                    "type": "string",
                    "enum": [
                        "research", "storyboard", "panel", "cover",
                        "avatar", "qa_screenshot", "final",
                    ],
                    "description": "Asset type.",
                },
                "name": {
                    "type": "string",
                    "description": "Asset name (e.g., 'panel_01', 'cover').",
                },
                "version": {
                    "type": "integer",
                    "description": "Specific version. Omit for latest.",
                },
                "include": {
                    "type": "string",
                    "enum": ["metadata", "full"],
                    "default": "metadata",
                    "description": "Return metadata only (default) or include payload.",
                },
                "format": {
                    "type": "string",
                    "enum": ["path", "base64", "data_uri"],
                    "default": "path",
                    "description": "Payload format when include=full.",
                },
                # For store — binary assets
                "source_path": {
                    "type": "string",
                    "description": "Path to file on disk (from generate_image).",
                },
                "data": {
                    "type": "string",
                    "description": "Content as base64 (binary) or JSON string (structured).",
                },
                # For store — structured assets (research, storyboard)
                "content": {
                    "type": "object",
                    "description": "Structured content (for research, storyboard).",
                },
                # For update_metadata
                "review_status": { "type": "string", "enum": ["accepted", "rejected"] },
                "review_feedback": { "type": "string" },
                "metadata": { "type": "object" },
            },
            "required": ["action", "project", "issue"],
        }
```

**Operations:**

| Action | Required Params | Returns |
|---|---|---|
| `store` | `project`, `issue`, `type`, `name`, (`source_path` or `data` or `content`) | `{ name, type, version, storage_path, size_bytes }` |
| `get` | `project`, `issue`, `type`, `name` | Asset (metadata or full) |
| `list` | `project`, `issue` | `{ assets: [{ name, type, latest_version, review_status }] }`, optionally filtered by `type` |
| `batch_encode` | `project`, `issue`, `type`, `format` | `{ items: [{ name, version, data_uri_or_base64 }] }` sorted by name |
| `update_metadata` | `project`, `issue`, `type`, `name`, `version` | `{ updated: true }` |

**Example calls:**

```python
# story-researcher stores research data (structured JSON, no file)
comic_asset(
    action="store",
    project="ampliverse-origins",
    issue="issue-001",
    type="research",
    name="research",
    content={
        "title": "The Great Refactoring",
        "subtitle": "A tale of code and courage",
        "timeline": [...],
        "key_moments": [...],
        "characters": [...],
        "metrics": {...},
        "outcome": "..."
    }
)
# → { "name": "research", "type": "research", "version": 1, "size_bytes": 4523 }

# storyboard-writer stores the storyboard
comic_asset(
    action="store",
    project="ampliverse-origins",
    issue="issue-001",
    type="storyboard",
    name="storyboard",
    content={
        "title": "The Great Refactoring",
        "panel_count": 6,
        "character_list": [...],
        "panel_list": [...]
    }
)
# → { "name": "storyboard", "type": "storyboard", "version": 1, "size_bytes": 8192 }

# panel-artist stores a panel image (from generate_image output on disk)
comic_asset(
    action="store",
    project="ampliverse-origins",
    issue="issue-001",
    type="panel",
    name="panel_01",
    source_path="panel_01.png"
)
# → { "name": "panel_01", "type": "panel", "version": 1,
#     "storage_path": "projects/ampliverse-origins/issues/issue-001/panels/panel_01_v1/image.png",
#     "size_bytes": 524288 }

# panel-artist stores v2 after review rejection
comic_asset(
    action="store",
    project="ampliverse-origins",
    issue="issue-001",
    type="panel",
    name="panel_01",
    source_path="panel_01.png"
)
# → { "name": "panel_01", "type": "panel", "version": 2, ... }

# panel-artist records review result on v1
comic_asset(
    action="update_metadata",
    project="ampliverse-origins",
    issue="issue-001",
    type="panel",
    name="panel_01",
    version=1,
    review_status="rejected",
    review_feedback="face occluded by speech bubble, wrong color palette"
)

# strip-compositor gets all panels as data URIs in one call
comic_asset(
    action="batch_encode",
    project="ampliverse-origins",
    issue="issue-001",
    type="panel",
    format="data_uri"
)
# → { "items": [
#       { "name": "panel_01", "version": 2, "data_uri": "data:image/png;base64,iVBOR..." },
#       { "name": "panel_02", "version": 1, "data_uri": "data:image/png;base64,iVBOR..." },
#       { "name": "panel_03", "version": 1, "data_uri": "data:image/png;base64,iVBOR..." }
#   ] }
#   ↑ sorted by name for deterministic panel ordering

# strip-compositor gets the storyboard to read dialogue and captions
comic_asset(
    action="get",
    project="ampliverse-origins",
    issue="issue-001",
    type="storyboard",
    name="storyboard",
    include="full"
)
# → { "name": "storyboard", "type": "storyboard", "version": 1,
#     "content": { "title": "...", "panel_list": [...], "character_list": [...] } }

# List everything in an issue
comic_asset(action="list", project="ampliverse-origins", issue="issue-001")
# → { "assets": [
#       { "name": "research", "type": "research", "latest_version": 1 },
#       { "name": "storyboard", "type": "storyboard", "latest_version": 1 },
#       { "name": "panel_01", "type": "panel", "latest_version": 2, "review_status": "accepted" },
#       { "name": "panel_02", "type": "panel", "latest_version": 1 },
#       { "name": "cover", "type": "cover", "latest_version": 1 },
#       ...
#   ] }

# List only panels
comic_asset(action="list", project="ampliverse-origins", issue="issue-001", type="panel")
```

### 6.4 comic_style

Style guide management with cross-project retrieval.

```python
class ComicStyleTool:
    name = "comic_style"
    description = (
        "Store, retrieve, and browse style guide definitions. "
        "Style guides are full visual language definitions reusable "
        "across issues and retrievable across projects."
    )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["store", "get", "list"],
                    "description": "Operation to perform.",
                },
                "project": {
                    "type": "string",
                    "description": "Project name or ID.",
                },
                "issue": {
                    "type": "string",
                    "description": "Origin issue ID (for store).",
                },
                "name": {
                    "type": "string",
                    "description": "Style name (freeform: 'manga', 'custom-noir', etc.).",
                },
                "version": {
                    "type": "integer",
                    "description": "Specific version. Omit for latest.",
                },
                "include": {
                    "type": "string",
                    "enum": ["metadata", "full"],
                    "default": "metadata",
                    "description": "Return metadata only or full definition.",
                },
                "definition": {
                    "type": "object",
                    "description": "Full style guide definition (for store).",
                },
                "review_status": { "type": "string" },
                "review_feedback": { "type": "string" },
                "metadata": { "type": "object" },
            },
            "required": ["action", "project"],
        }
```

**Operations:**

| Action | Required Params | Returns |
|---|---|---|
| `store` | `project`, `issue`, `name`, `definition` | `{ name, version }` |
| `get` | `project`, `name` | Style guide (metadata or full definition) |
| `list` | `project` | `{ styles: [{ name, latest_version, origin_issue }] }` |

**Example calls:**

```python
# style-curator stores the full style guide
comic_style(
    action="store",
    project="ampliverse-origins",
    issue="issue-001",
    name="manga",
    definition={
        "image_prompt_template": "...",
        "color_palette": { "primary": "#...", "accent": "#..." },
        "panel_conventions": { "gutter": "8px", "border_radius": "4px" },
        "character_rendering": { ... },
        "text_treatment": { "font_family": "...", "bubble_style": "..." }
    }
)
# → { "name": "manga", "version": 1 }

# Any downstream agent retrieves the full style guide
comic_style(
    action="get",
    project="ampliverse-origins",
    name="manga",
    include="full"
)
# → { "name": "manga", "version": 1, "definition": { ...full guide... } }

# Reuse style guide from another project
comic_style(
    action="get",
    project="debug-wars",
    name="cyberpunk",
    include="full"
)
# → full style guide from a different project
```

---

## 7. Domain Object Schemas

### ComicProjectService

The single class that holds all business logic. Every method is async and receives explicit project/issue IDs.

```python
class ComicProjectService:
    """Core service — all business logic for comic asset management.

    Stateless about 'current' project/issue. Every method receives
    project_id and/or issue_id explicitly from the caller.
    """

    def __init__(self, storage: StorageProtocol) -> None:
        self._storage = storage
        self._locks: dict[str, asyncio.Lock] = {}
        self._meta_lock = asyncio.Lock()

    # ── Helpers ────────────────────────────────────────────────

    async def _get_lock(self, project_id: str) -> asyncio.Lock:
        """Get or create a per-project lock (protected by meta-lock)."""
        async with self._meta_lock:
            if project_id not in self._locks:
                self._locks[project_id] = asyncio.Lock()
            return self._locks[project_id]

    def _slugify(self, name: str) -> str:
        """Sanitize name for filesystem paths. Lowercase, replace spaces with underscores,
        strip non-alphanumeric except hyphens and underscores."""
        ...

    # ── Project & Issue ────────────────────────────────────────

    async def create_issue(
        self, project_name: str, title: str, description: str = ""
    ) -> dict[str, Any]:
        """Create an issue within a project. Auto-creates project if needed.
        Returns { project_id, issue_id, created }."""
        ...

    async def list_projects(self) -> list[dict[str, Any]]:
        """List all projects with summary metadata."""
        ...

    async def list_issues(self, project_id: str) -> list[dict[str, Any]]:
        """List all issues in a project with summary metadata."""
        ...

    async def get_issue(self, project_id: str, issue_id: str) -> dict[str, Any]:
        """Get issue details including asset counts by type."""
        ...

    async def cleanup_issue(
        self, project_id: str, issue_id: str
    ) -> dict[str, Any]:
        """Delete all stored files for an issue. Returns { deleted_files, freed_bytes }."""
        ...

    async def cleanup_project(self, project_id: str) -> dict[str, Any]:
        """Delete all stored files for a project. Returns { deleted_files, freed_bytes }."""
        ...

    # ── Characters ─────────────────────────────────────────────

    async def store_character(
        self,
        project_id: str,
        issue_id: str,
        name: str,
        style: str,
        *,
        role: str,
        character_type: str,
        bundle: str,
        visual_traits: str,
        team_markers: str,
        distinctive_features: str,
        backstory: str = "",
        motivations: str = "",
        personality: str = "",
        source_path: str | None = None,
        data: bytes | None = None,
    ) -> dict[str, Any]:
        """Store a character design in the project roster.
        Accepts image from source_path (disk) or data (bytes).
        Auto-increments version per (name, style).
        Returns { name, style, version, storage_path }."""
        ...

    async def get_character(
        self,
        project_id: str,
        name: str,
        *,
        style: str | None = None,
        version: int | None = None,
        include: str = "metadata",
        format: str = "path",
    ) -> dict[str, Any]:
        """Retrieve a character design. Defaults to latest version of specified style.
        include='metadata' returns everything except binary payload.
        include='full' returns payload in requested format (path/base64/data_uri)."""
        ...

    async def list_characters(self, project_id: str) -> list[dict[str, Any]]:
        """List all characters in the project roster with style/version summaries."""
        ...

    async def list_character_versions(
        self, project_id: str, name: str
    ) -> list[dict[str, Any]]:
        """List all versions/styles for a specific character."""
        ...

    async def update_character_metadata(
        self,
        project_id: str,
        name: str,
        style: str,
        version: int,
        *,
        review_status: str | None = None,
        review_feedback: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update metadata on an existing character version (review feedback etc.)."""
        ...

    # ── Assets ─────────────────────────────────────────────────

    async def store_asset(
        self,
        project_id: str,
        issue_id: str,
        asset_type: str,
        name: str,
        *,
        source_path: str | None = None,
        data: bytes | None = None,
        content: dict[str, Any] | str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Store an issue-scoped asset. Accepts:
        - source_path: file on disk (for generate_image output)
        - data: raw bytes (binary content without intermediate file)
        - content: structured data (for research, storyboard — stored as JSON)
        Auto-increments version per (name, asset_type) within the issue.
        Returns { name, type, version, storage_path, size_bytes }."""
        ...

    async def get_asset(
        self,
        project_id: str,
        issue_id: str,
        asset_type: str,
        name: str,
        *,
        version: int | None = None,
        include: str = "metadata",
        format: str = "path",
    ) -> dict[str, Any]:
        """Retrieve an asset. Defaults to latest version.
        include='metadata' returns everything except binary payload.
        include='full' returns payload in requested format."""
        ...

    async def list_assets(
        self,
        project_id: str,
        issue_id: str,
        *,
        asset_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """List assets in an issue. Optionally filter by type."""
        ...

    async def batch_encode(
        self,
        project_id: str,
        issue_id: str,
        asset_type: str,
        *,
        format: str = "data_uri",
    ) -> list[dict[str, Any]]:
        """Encode latest version of all assets of a type.
        Returns list sorted by name for deterministic ordering.
        Uses bounded asyncio.gather (semaphore, max 4 concurrent)."""
        ...

    async def update_asset_metadata(
        self,
        project_id: str,
        issue_id: str,
        asset_type: str,
        name: str,
        version: int,
        *,
        review_status: str | None = None,
        review_feedback: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update metadata on an existing asset version."""
        ...

    # ── Styles ─────────────────────────────────────────────────

    async def store_style(
        self,
        project_id: str,
        issue_id: str,
        name: str,
        definition: dict[str, Any],
        *,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Store a style guide definition. Auto-increments version per (name,).
        Returns { name, version }."""
        ...

    async def get_style(
        self,
        project_id: str,
        name: str,
        *,
        version: int | None = None,
        include: str = "metadata",
    ) -> dict[str, Any]:
        """Retrieve a style guide. include='full' returns the complete definition."""
        ...

    async def list_styles(self, project_id: str) -> list[dict[str, Any]]:
        """List style guides in a project."""
        ...
```

---

## 8. Encoding Utilities

Standalone functions replacing every `bash(command="base64 ...")` call. Used by `ComicProjectService` internally and available for import.

```python
# encoding.py

import base64
import mimetypes
from pathlib import Path


def guess_mime(file_path: str) -> str:
    """Guess MIME type from file extension. Defaults to application/octet-stream."""
    mime, _ = mimetypes.guess_type(file_path)
    return mime or "application/octet-stream"


def bytes_to_base64(data: bytes) -> str:
    """Encode bytes to base64 string."""
    return base64.b64encode(data).decode("ascii")


def bytes_to_data_uri(data: bytes, mime_type: str) -> str:
    """Encode bytes to data URI: data:<mime>;base64,<encoded>"""
    return f"data:{mime_type};base64,{bytes_to_base64(data)}"


def file_to_base64(file_path: str) -> str:
    """Read file and return base64 string. Blocking — call via to_thread."""
    return bytes_to_base64(Path(file_path).read_bytes())


def file_to_data_uri(file_path: str) -> str:
    """Read file and return data URI. Blocking — call via to_thread."""
    data = Path(file_path).read_bytes()
    mime = guess_mime(file_path)
    return bytes_to_data_uri(data, mime)


def base64_to_bytes(encoded: str) -> bytes:
    """Decode base64 string to bytes."""
    return base64.b64decode(encoded)
```

---

## 9. Concurrency Strategy

### The Problem

The recipe runs steps with `parallel: 2`. Character-designer and panel-artist may execute concurrently, both storing assets to the same project. Strip-compositor's `batch_encode` reads multiple assets concurrently.

### The Solution

**ComicProjectService is stateless per-request** — it holds no mutable request state, so concurrent calls are inherently safe at the service level.

**Storage-level concurrency** uses async locks per project:

```
┌─────────────────────────────────────────────┐
│              _meta_lock                     │
│  Protects the _locks dict itself            │
│  Held only during dict lookup/creation      │
│  (~microseconds)                            │
├─────────────────────────────────────────────┤
│         _locks[project_id]                  │
│  Per-project lock for manifest writes       │
│  Held during: read manifest → update →      │
│  write manifest + write file (~5ms)         │
│  NOT held during bulk reads (batch_encode)  │
└─────────────────────────────────────────────┘
```

**Lock acquisition flow for `store` operations:**

```python
async def store_asset(self, project_id, issue_id, asset_type, name, ...):
    lock = await self._get_lock(project_id)
    async with lock:
        # 1. Read issue manifest
        manifest = await self._read_issue_manifest(project_id, issue_id)
        # 2. Determine next version
        key = f"{asset_type}:{name}"
        current = manifest["assets"].get(key, {}).get("latest_version", 0)
        version = current + 1
        # 3. Write asset data to storage
        rel_path = f"projects/{project_id}/issues/{issue_id}/{asset_type}s/{name}_v{version}/..."
        await self._storage.write_bytes(rel_path, data)
        # 4. Update manifest
        manifest["assets"][key] = {"latest_version": version}
        await self._write_issue_manifest(project_id, issue_id, manifest)
    return {"name": name, "type": asset_type, "version": version, ...}
```

**Read operations (get, list, batch_encode):**
- Do NOT acquire the project lock
- Read directly from storage
- Manifest reads use a snapshot — if a concurrent write is in progress, the read sees the pre-write state (acceptable for the pipeline's use case)

**batch_encode concurrency:**
- Uses `asyncio.Semaphore(4)` to bound concurrent file reads + base64 encodes
- Prevents excessive memory usage when encoding many panels simultaneously

**Deadlock freedom:**
- Locks are never nested (no lock A acquired while holding lock B)
- Meta-lock is always released before project-lock is acquired
- Hold times are minimal (~5ms for a manifest read-update-write cycle)

---

## 10. Agent Integration — Per-Agent Migration

Every agent is migrated to use the asset manager tools. After migration, the only direct file operation remaining in the entire pipeline is strip-compositor's `write_file` for final comic delivery to the user-specified path.

### story-researcher

**Before:** Returns `research_data` as JSON through recipe context output.

**After:** Stores research data through `comic_asset`, returns a compact reference.

```python
# Agent calls:
comic_asset(
    action="store",
    project="{{project_id}}",
    issue="{{issue_id}}",
    type="research",
    name="research",
    content={ "title": "...", "timeline": [...], "key_moments": [...], ... }
)
# Returns to recipe: { "type": "research", "name": "research", "version": 1 }
# Instead of the entire research JSON blob
```

**Tools after migration:** `comic_asset`, `read_file` (to read session file), `load_skill`

### style-curator

**Before:** Returns `style_guide` as text/JSON through recipe context output.

**After:** Stores the full style guide definition through `comic_style`, returns a reference.

```python
# Agent calls:
comic_style(
    action="store",
    project="{{project_id}}",
    issue="{{issue_id}}",
    name="manga",
    definition={ "image_prompt_template": "...", "color_palette": {...}, ... }
)
# Returns to recipe: { "name": "manga", "version": 1 }
```

**Tools after migration:** `comic_style`, `comic_asset` (to read research data for context), `load_skill`

### storyboard-writer

**Before:** Returns `storyboard` as JSON through recipe context output. Receives full `research_data` and `style_guide` blobs in prompt.

**After:** Reads research and style guide from the asset manager. Stores storyboard through `comic_asset`. Returns compact reference.

```python
# Agent reads inputs:
comic_asset(action="get", project="{{project_id}}", issue="{{issue_id}}",
            type="research", name="research", include="full")
comic_style(action="get", project="{{project_id}}", name="{{style_name}}",
            include="full")

# Agent stores output:
comic_asset(
    action="store",
    project="{{project_id}}",
    issue="{{issue_id}}",
    type="storyboard",
    name="storyboard",
    content={ "title": "...", "character_list": [...], "panel_list": [...] }
)
# Returns: { "type": "storyboard", "version": 1 }
```

**Tools after migration:** `comic_asset`, `comic_style`, `load_skill`, `delegate`

### character-designer

**Before:** Calls `generate_image` → writes `ref_<name>.png` to CWD → returns character sheet JSON through recipe context.

**After:** Calls `generate_image` (still writes to CWD — we don't control this tool in V1), then stores the image + full character design through `comic_character`. May read existing characters from the roster as reference for new designs.

```python
# Agent reads style guide:
comic_style(action="get", project="{{project_id}}", name="{{style_name}}",
            include="full")

# Optionally reads existing character as reference for new version/style:
comic_character(action="get", project="{{project_id}}", name="The Explorer",
                style="manga", include="full", format="path")

# Agent calls generate_image (unchanged):
generate_image(prompt="...", output_path="ref_the_explorer.png", size="portrait")

# Agent stores the complete character design:
comic_character(
    action="store",
    project="{{project_id}}",
    issue="{{issue_id}}",
    name="The Explorer",
    style="manga",
    role="protagonist",
    character_type="main",
    bundle="foundation",
    visual_traits="seasoned scout in worn leather jacket...",
    team_markers="blue accent with compass insignia...",
    distinctive_features="leather field bag, binoculars...",
    backstory="A veteran pathfinder who navigates complex codebases",
    source_path="ref_the_explorer.png"
)
# Returns: { "name": "the_explorer", "style": "manga", "version": 1 }
```

**Tools after migration:** `comic_character`, `comic_style`, `generate_image`, `load_skill`

### panel-artist

**Before:** Reads character `reference_image` paths from character sheet JSON in context. Calls `generate_image`. Returns panel result JSON.

**After:** Gets character metadata for prompt crafting (metadata only — no image payload in context). Gets character image path only when passing to `generate_image`. Stores panel through `comic_asset`. Records review feedback as version metadata.

```python
# Agent reads character metadata for prompt crafting (no image bytes in context):
comic_character(action="get", project="{{project_id}}", name="The Explorer",
                style="manga", include="metadata")
# → { "visual_traits": "...", "team_markers": "...", "distinctive_features": "..." }

# Agent gets character image PATH for generate_image reference_images param:
comic_character(action="get", project="{{project_id}}", name="The Explorer",
                style="manga", include="full", format="path")
# → { ..., "image_path": "/abs/path/to/reference.png" }

# Agent generates the panel:
generate_image(
    prompt="...",
    output_path="panel_01.png",
    size="landscape",
    reference_images=["/abs/path/to/reference.png"]
)

# Agent stores the panel:
comic_asset(action="store", project="{{project_id}}", issue="{{issue_id}}",
            type="panel", name="panel_01", source_path="panel_01.png")
# → version 1

# Agent self-reviews using vision... if rejected:
comic_asset(action="update_metadata", project="{{project_id}}", issue="{{issue_id}}",
            type="panel", name="panel_01", version=1,
            review_status="rejected",
            review_feedback="face occluded by speech bubble")

# Regenerate → store again (auto version 2):
comic_asset(action="store", project="{{project_id}}", issue="{{issue_id}}",
            type="panel", name="panel_01", source_path="panel_01.png")
# → version 2

# Mark v2 as accepted:
comic_asset(action="update_metadata", project="{{project_id}}", issue="{{issue_id}}",
            type="panel", name="panel_01", version=2,
            review_status="accepted",
            review_feedback="consistent with style guide")
```

**Tools after migration:** `comic_asset`, `comic_character`, `comic_style`, `generate_image`, `load_skill`

### cover-artist

**Before:** Calls `generate_image` for cover, `web_fetch` for avatar, `bash(base64 ...)` for encoding. Returns cover HTML snippet.

**After:** Stores cover image and avatar through `comic_asset`. No more bash for base64 — encoding is built into `get` with `format='data_uri'`.

```python
# Agent reads character metadata for the cover composition:
comic_character(action="list", project="{{project_id}}")
# Decides which characters to feature

# Agent reads style guide:
comic_style(action="get", project="{{project_id}}", name="{{style_name}}",
            include="full")

# Agent reads research for title/theme:
comic_asset(action="get", project="{{project_id}}", issue="{{issue_id}}",
            type="research", name="research", include="full")

# Agent generates cover:
generate_image(prompt="...", output_path="cover.png", size="portrait",
               reference_images=[...])

# Agent stores cover:
comic_asset(action="store", project="{{project_id}}", issue="{{issue_id}}",
            type="cover", name="cover", source_path="cover.png")

# Agent fetches avatar (web_fetch still needed for the URL):
web_fetch(url="https://github.com/microsoft-amplifier.png",
          save_to_file="avatar.png")

# Agent stores avatar:
comic_asset(action="store", project="{{project_id}}", issue="{{issue_id}}",
            type="avatar", name="avatar", source_path="avatar.png")

# Self-review + update_metadata for review feedback (same pattern as panel-artist)
```

**Tools after migration:** `comic_asset`, `comic_character`, `comic_style`, `generate_image`, `web_fetch`, `load_skill`

### strip-compositor

**Before:** Reads all PNGs via `read_file`, base64-encodes via `bash(base64 -w 0 ...)`, writes final HTML via `write_file`, deletes intermediates via `bash(rm ...)`.

**After:** Gets all data through the asset manager. `batch_encode` replaces all bash base64 calls. Only `write_file` remains for final delivery. No more cleanup — that's an explicit recipe step.

```python
# Get all panels as data URIs in one call:
comic_asset(action="batch_encode", project="{{project_id}}", issue="{{issue_id}}",
            type="panel", format="data_uri")
# → sorted list of { name, version, data_uri }

# Get cover as data URI:
comic_asset(action="get", project="{{project_id}}", issue="{{issue_id}}",
            type="cover", name="cover", include="full", format="data_uri")

# Get avatar as data URI:
comic_asset(action="get", project="{{project_id}}", issue="{{issue_id}}",
            type="avatar", name="avatar", include="full", format="data_uri")

# Get storyboard for dialogue/captions:
comic_asset(action="get", project="{{project_id}}", issue="{{issue_id}}",
            type="storyboard", name="storyboard", include="full")

# Get character metadata for intro page (no images needed — metadata only):
comic_character(action="list", project="{{project_id}}")

# Get style guide for layout/fonts/colors:
comic_style(action="get", project="{{project_id}}", name="{{style_name}}",
            include="full")

# Get research data for title and metadata:
comic_asset(action="get", project="{{project_id}}", issue="{{issue_id}}",
            type="research", name="research", include="full")

# Assemble HTML...

# Store the final HTML in the asset manager:
comic_asset(action="store", project="{{project_id}}", issue="{{issue_id}}",
            type="final", name="comic", data="<base64 of HTML>")

# Deliver to user-specified location (ONLY write_file in entire pipeline):
write_file(file_path="{{output_path}}", content="<assembled HTML>")

# QA screenshots stored as assets:
comic_asset(action="store", project="{{project_id}}", issue="{{issue_id}}",
            type="qa_screenshot", name="cover_review",
            source_path="screenshot.png")
```

**Tools after migration:** `comic_asset`, `comic_character`, `comic_style`, `write_file` (final delivery only), `load_skill`, `delegate` (to browser-tester:visual-documenter for QA)

### Tools Removed From Agents After Migration

| Agent | Removed Tools | Reason |
|---|---|---|
| cover-artist | `bash` | base64 encoding now in `comic_asset(format='data_uri')` |
| strip-compositor | `bash`, `read_file` | base64 via `batch_encode`, reads via `comic_asset(action='get')` |
| All agents | unnecessary `write_file` | All asset writes through asset manager |

**Only `write_file` usage remaining:** strip-compositor writing the final HTML to the user-requested output path.

---

## 11. Recipe Integration

### Context Variables

Recipe context shrinks dramatically. Instead of passing full research data, style guides, storyboards, and character sheets between steps, the recipe passes compact references.

**Before (current recipe):**

```yaml
context:
  session_file: ""
  style: "superhero"
  output_name: ""
  # ... requirement flags ...

# Steps pass full blobs:
#   research_data (large JSON), style_guide (large text),
#   storyboard (large JSON), character_sheet (large array)
```

**After:**

```yaml
context:
  session_file: ""
  style: "superhero"
  output_name: ""
  # Asset manager references (set by init-project step):
  project_id: ""
  issue_id: ""
  style_name: ""
```

### Recipe Structure (V2 with Asset Manager)

```yaml
name: "session-to-comic"
version: "6.0.0"

context:
  session_file: ""
  style: "superhero"
  output_name: ""
  project_name: "AmpliVerse Comics"
  project_id: ""
  issue_id: ""
  style_name: ""

stages:
  - name: "research-and-storyboard"
    steps:
      # NEW: Initialize project and issue
      - id: "init-project"
        agent: "comic-strips:story-researcher"
        prompt: |
          Initialize the comic project by calling:
          comic_project(action="create_issue",
                        project="{{project_name}}",
                        title="Comic from {{session_file}}")
          Return the project_id and issue_id.
        output: "project_init"
        # project_id and issue_id flow into context

      - id: "research"
        agent: "stories:story-researcher"
        prompt: |
          Analyze {{session_file}} and store results:
          comic_asset(action="store", project="{{project_id}}",
                      issue="{{issue_id}}", type="research", ...)
        output: "research_ref"

      - id: "style-curation"
        agent: "comic-strips:style-curator"
        prompt: |
          Read research data from the asset manager.
          Create style guide for style "{{style}}".
          Store via comic_style.
        output: "style_ref"

      - id: "storyboard"
        agent: "comic-strips:storyboard-writer"
        prompt: |
          Read research data and style guide from the asset manager.
          Create storyboard. Store via comic_asset.
          Return the character_list and panel_list for the foreach loops.
        output: "storyboard"
        parse_json: true

    approval:
      required: true
      prompt: |
        Storyboard complete. Review before expensive image generation.
        Project: {{project_id}}, Issue: {{issue_id}}
        (Use comic_asset to inspect storyboard details if needed)

  - name: "art-generation"
    steps:
      - id: "design-characters"
        foreach: "{{storyboard.character_list}}"
        as: character_item
        agent: "comic-strips:character-designer"
        parallel: 2
        prompt: |
          Design character {{character_item.name}}.
          Read style guide from comic_style.
          Generate image, store via comic_character.
          Project: {{project_id}}, Issue: {{issue_id}}
        collect: "character_refs"

      - id: "generate-panels"
        foreach: "{{storyboard.panel_list}}"
        as: panel_item
        depends_on: ["design-characters"]
        agent: "comic-strips:panel-artist"
        parallel: 2
        prompt: |
          Generate panel {{panel_item.index}}.
          Read character designs from comic_character (metadata for prompts, paths for reference_images).
          Read style guide from comic_style.
          Store panel via comic_asset. Record review feedback via update_metadata.
          Project: {{project_id}}, Issue: {{issue_id}}
        collect: "panel_refs"

      - id: "generate-cover"
        depends_on: ["design-characters"]
        agent: "comic-strips:cover-artist"
        prompt: |
          Generate cover art.
          Read research, characters, style guide from asset manager.
          Store cover and avatar via comic_asset.
          Project: {{project_id}}, Issue: {{issue_id}}
        output: "cover_ref"

      - id: "composition"
        depends_on: ["generate-panels", "generate-cover"]
        agent: "comic-strips:strip-compositor"
        prompt: |
          Assemble final comic HTML.
          Read ALL inputs from asset manager:
          - batch_encode panels, get cover/avatar as data_uri
          - get storyboard, character list, style guide, research
          Store final HTML via comic_asset.
          Write to user path: {{output_name}}
          Project: {{project_id}}, Issue: {{issue_id}}
        output: "final_output"

      # NEW: Optional cleanup step
      - id: "cleanup"
        agent: "comic-strips:strip-compositor"
        depends_on: ["composition"]
        condition: "{{cleanup_requested}}"
        prompt: |
          Clean up intermediate files from CWD (leftover from generate_image).
          The asset manager has all assets safely stored.
          Remove: ref_*.png, panel_*.png, cover.png, avatar.png
```

---

## 12. Module Structure

```
modules/tool-comic-assets/
├── amplifier_module_comic_assets/
│   ├── __init__.py              # Tool classes + mount()          (~150 lines)
│   ├── service.py               # ComicProjectService             (~500 lines)
│   ├── models.py                # Domain model dataclasses        (~120 lines)
│   ├── storage.py               # StorageProtocol + FileSystem    (~100 lines)
│   ├── encoding.py              # Base64 encode/decode utilities  (~40 lines)
│   └── _version.py              # __version__ = "0.1.0"
├── tests/
│   ├── conftest.py              # Fixtures: temp storage, service
│   ├── test_models.py           # Dataclass serialization
│   ├── test_storage.py          # FileSystemStorage operations
│   ├── test_service.py          # Service business logic
│   ├── test_encoding.py         # Base64 utilities
│   ├── test_tools.py            # Tool dispatch + schema validation
│   └── test_concurrency.py      # Parallel store, batch_encode
├── pyproject.toml
└── pyrightconfig.json
```

**Estimated total:** ~910 source lines, ~600 test lines.

### pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "amplifier-module-tool-comic-assets"
version = "0.1.0"
requires-python = ">=3.11"
# Zero external dependencies — stdlib only
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-asyncio>=0.24"]

[project.entry-points."amplifier.modules"]
tool-comic-assets = "amplifier_module_comic_assets:mount"

[tool.hatch.build.targets.wheel]
packages = ["amplifier_module_comic_assets"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--import-mode=importlib"
asyncio_mode = "strict"
```

### Behavior YAML Update

```yaml
# behaviors/comic-strips.yaml — add the new tool module
tools:
  - module: tool-comic-image-gen
    source: git+https://github.com/colombod/amplifier-bundle-comic-strips@main#subdirectory=modules/tool-comic-image-gen
  - module: tool-comic-assets
    source: git+https://github.com/colombod/amplifier-bundle-comic-strips@main#subdirectory=modules/tool-comic-assets
  - module: tool-skills
    source: git+https://github.com/microsoft/amplifier-module-tool-skills@main
    config:
      skills:
        - "git+https://github.com/colombod/amplifier-bundle-comic-strips@main#subdirectory=skills"
```

---

## 13. Testing Strategy

### Unit Tests

**test_models.py** — Domain model serialization:
- Dataclass to dict and back
- Slug generation from display names (spaces, special chars, unicode)
- Version auto-increment logic

**test_storage.py** — FileSystemStorage:
- write_bytes / read_bytes round-trip
- write_text / read_text round-trip (UTF-8)
- Parent directory auto-creation
- exists / delete / list_dir
- FileNotFoundError on missing paths
- abs_path resolution

**test_encoding.py** — Base64 utilities:
- bytes_to_base64 / base64_to_bytes round-trip
- file_to_base64 / file_to_data_uri
- guess_mime for .png, .json, .html, unknown
- data URI format correctness

**test_service.py** — ComicProjectService business logic:
- `create_issue` creates project + issue on first call
- `create_issue` reuses existing project on second call
- `store_character` auto-increments version per (name, style)
- `store_asset` auto-increments version per (name, type, issue)
- `get_character` returns metadata only by default
- `get_character` with `include='full'` returns image path/base64/data_uri
- `get_character` with version=None returns latest
- `get_character` cross-project retrieval
- `store` from source_path reads file and stores bytes
- `store` from data parameter stores directly
- `store` from content parameter stores as JSON
- `update_metadata` modifies existing version without creating new one
- `list_*` operations return correct summaries
- `batch_encode` returns sorted by name
- `cleanup_issue` removes files and updates manifests
- `cleanup_project` removes entire project tree

**test_tools.py** — Tool dispatch:
- Each tool routes actions correctly to service methods
- Missing required params return error ToolResult
- Invalid action values return error ToolResult
- Input schema validation per tool

**test_concurrency.py** — Parallel safety:
- Two concurrent `store_asset` calls to same issue get different versions
- Two concurrent `store_character` calls to same project get different versions
- `batch_encode` with semaphore doesn't exceed max concurrency
- Lock contention doesn't cause deadlocks

### Integration Tests

- Full pipeline simulation: create_issue → store research → store style → store storyboard → store characters → store panels (with review loop) → batch_encode → store final
- Cross-project character retrieval end-to-end
- Cleanup after full pipeline run

---

## 14. Success Criteria

1. **All 6 pipeline agents use asset manager tools exclusively.** No direct `bash`, `read_file` for asset operations. Only `write_file` in strip-compositor for final delivery.
2. **Character designs are composite domain objects** with metadata + images, versioned by style, living in the project roster.
3. **Review feedback stored as version metadata.** Full creative process history preserved — every rejected attempt, every review note.
4. **Cross-project retrieval works** for characters and style guides. Any project can fetch from any other project.
5. **Discovery APIs work.** Agents can browse all projects, issues, characters, styles, assets, versions.
6. **Metadata-only by default.** `get` returns metadata unless `include='full'` is explicitly set. No accidental context flooding.
7. **Recipe context shrinks.** Steps pass `project_id` + `issue_id` references instead of full JSON/text payloads.
8. **Concurrent execution works.** `parallel:2` character-designer and panel-artist runs operate correctly under async locks.
9. **Explicit cleanup only.** No automatic deletes anywhere. Cleanup is a conscious operation.
10. **All async, protocol-abstracted.** Storage backend swappable. Every I/O call is async.
11. **Zero external dependencies.** Module runs on stdlib only (Python 3.11+).
12. **Four focused tools, one service.** Small input schemas, clear responsibilities, single source of business logic.

---

## 15. Deferred to V2+

| Feature | Rationale for Deferral |
|---|---|
| **Cloud/remote storage backend** | Protocol is ready. V1 validates the abstraction with filesystem. Cloud implementation is a new `StorageProtocol` class, not a redesign. |
| **generate_image writing directly to asset manager** | Requires changes to the image gen tool. V1 flow (generate → store from path) works. |
| **Metadata search/query** | "Find characters by trait", "find panels by review status". Useful but not needed for pipeline execution. List + filter in the agent is sufficient for V1 scale. |
| **Asset export/import between workspaces** | Clipboard-style sharing. V1's cross-project retrieval covers the same-workspace case. |
| **Version rollback/restore** | "Revert to version N." V1 tracks all versions; rollback is just "get version N, store as N+1." |
| **Asset browser UI** | Visual tool for browsing the managed workspace. V1 uses discovery APIs through agent tools. |
| **Automatic CWD cleanup of generate_image intermediates** | After store-from-path, the source file in CWD is no longer needed. V1 leaves them; explicit cleanup step handles it. |
| **Style guide diffing** | Compare two style guide versions. V1 stores versions; diffing is a future tool operation. |
