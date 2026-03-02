# URI v2 Design — Project-Scoped vs Issue-Scoped Resources

## Goal

Replace the fixed 4-segment `comic://` URI scheme with a scope-aware format that correctly distinguishes project-wide resources (characters, styles) from issue-specific assets (panels, covers, storyboards), eliminating a class of silent routing bugs and enabling explicit cross-issue character reuse.

## Background

The v1 URI scheme (`comic://project/issue/type/name`) forces every resource into a 4-segment format regardless of actual scope. Characters and styles are stored and retrieved at the project level — `get_character(project, name)` has no `issue` parameter — yet the URI embeds an `issue` segment that is silently ignored during resolution. This creates several concrete problems:

1. **False implication of scope** — `comic://my-comic/issue-001/character/explorer` looks issue-scoped but resolves project-wide. Two different URIs (`issue-001` vs `issue-002`) resolve to the same character.
2. **Dead parameter flow** — `_parse_uri_params` extracts `issue` from character URIs, but `get_character` and `get_style` never consume it.
3. **No cast binding model** — there is no way to distinguish "project roster character" from "characters used in a specific issue." Cross-issue reuse works by accident.
4. **Misleading provenance in list results** — `list_characters` bakes `origin_issue_id` into URIs as though it were a routing key.

## Approach

Split the URI format into two shapes based on the actual storage and retrieval model:

- **Project-scoped** resources get a short path: `comic://project/collection/name`
- **Issue-scoped** resources get a longer path: `comic://project/issues/issue-name/collection/name`

The second path segment determines routing: if it is a known project-scoped collection (`characters`, `styles`), the URI is project-scoped. If it is `issues`, the URI is issue-scoped and the third segment identifies the issue. This makes the URI an honest reflection of the data model — no dead segments, no silent ignoring.

The storyboard becomes the **cast binding** for an issue, carrying versioned project-scoped character URIs in its `character_list`. This eliminates the need for a separate "issue cast" entity while making "which characters at which versions for this issue" a trivial storyboard read.

## Architecture

### URI Format

**Project-scoped** (3 path segments after scheme):
```
comic://project/collection/name[?v=N]
```

**Issue-scoped** (5 path segments after scheme):
```
comic://project/issues/issue-name/collection/name[?v=N]
```

Version is always an optional query parameter. Absence means latest.

### URI Examples

| Resource | URI | Scope |
|----------|-----|-------|
| Character (latest) | `comic://my-comic/characters/explorer` | Project |
| Character (pinned) | `comic://my-comic/characters/explorer?v=2` | Project |
| Style guide | `comic://my-comic/styles/manga` | Project |
| Panel | `comic://my-comic/issues/the-revenge/panels/panel_01` | Issue |
| Cover | `comic://my-comic/issues/the-revenge/covers/cover` | Issue |
| Storyboard | `comic://my-comic/issues/the-revenge/storyboards/main` | Issue |
| Research | `comic://my-comic/issues/the-revenge/research/session-data` | Issue |
| Final comic | `comic://my-comic/issues/the-revenge/finals/comic` | Issue |
| Avatar | `comic://my-comic/issues/the-revenge/avatars/ampliverse_logo` | Issue |
| QA Screenshot | `comic://my-comic/issues/the-revenge/qa_screenshots/layout-check` | Issue |

### Collection Names

All collection names are pluralized for consistency with the path-based URI style:

| Collection | Scope | v1 Singular | v2 Plural |
|------------|-------|-------------|-----------|
| Characters | Project | `character` | `characters` |
| Styles | Project | `style` | `styles` |
| Panels | Issue | `panel` | `panels` |
| Covers | Issue | `cover` | `covers` |
| Storyboards | Issue | `storyboard` | `storyboards` |
| Research | Issue | `research` | `research` |
| Finals | Issue | `final` | `finals` |
| Avatars | Issue | `avatar` | `avatars` |
| QA Screenshots | Issue | `qa_screenshot` | `qa_screenshots` |

## Components

### `ComicURI` Dataclass

```python
PROJECT_SCOPED_TYPES = frozenset({"characters", "styles"})
ISSUE_SCOPED_TYPES = frozenset({
    "panels", "covers", "storyboards", "research",
    "finals", "avatars", "qa_screenshots",
})

@dataclass(frozen=True, slots=True)
class ComicURI:
    project: str
    asset_type: str           # "characters", "styles", "panels", etc.
    name: str
    issue: str | None = None  # None for project-scoped, present for issue-scoped
    version: int | None = None

    @property
    def is_project_scoped(self) -> bool:
        return self.issue is None

    @property
    def is_issue_scoped(self) -> bool:
        return self.issue is not None

    @property
    def is_latest(self) -> bool:
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
```

### Parser Logic

```python
def parse_comic_uri(raw: str) -> ComicURI:
    parsed = urlparse(raw)
    if parsed.scheme != "comic":
        raise InvalidComicURI(f"Expected 'comic' scheme, got '{parsed.scheme}'")

    segments = [s for s in parsed.path.strip("/").split("/")]
    # First segment after authority is always project
    # parsed.netloc = project, segments = rest of path

    project = parsed.netloc
    if not project:
        raise InvalidComicURI("Missing project in URI")

    # Parse version from query string
    version = None
    if parsed.query:
        qs = parse_qs(parsed.query)
        if "v" in qs:
            version = int(qs["v"][0])

    if len(segments) == 2 and segments[0] in PROJECT_SCOPED_TYPES:
        # comic://project/characters/name
        return ComicURI(project=project, asset_type=segments[0],
                        name=segments[1], version=version)

    if len(segments) == 4 and segments[0] == "issues":
        # comic://project/issues/issue-name/panels/name
        if segments[2] not in ISSUE_SCOPED_TYPES:
            raise InvalidComicURI(f"Unknown issue-scoped type: '{segments[2]}'")
        return ComicURI(project=project, issue=segments[1],
                        asset_type=segments[2], name=segments[3],
                        version=version)

    raise InvalidComicURI(f"Cannot parse URI: '{raw}'")
```

### Builder Methods

```python
@classmethod
def for_character(cls, project: str, name: str, *, version: int | None = None) -> "ComicURI":
    """Project-scoped character URI. No issue segment."""
    return cls(project=project, asset_type="characters", name=name, version=version)

@classmethod
def for_style(cls, project: str, name: str, *, version: int | None = None) -> "ComicURI":
    """Project-scoped style URI. No issue segment."""
    return cls(project=project, asset_type="styles", name=name, version=version)

@classmethod
def for_asset(cls, project: str, issue: str, asset_type: str, name: str,
              *, version: int | None = None) -> "ComicURI":
    """Issue-scoped asset URI."""
    return cls(project=project, issue=issue, asset_type=asset_type,
               name=name, version=version)
```

Note: `for_character` and `for_style` no longer accept an `issue` parameter — it was never a routing key, and the v2 URI makes that explicit.

### Storyboard as Cast Binding

The storyboard's `character_list` uses versioned project-scoped character URIs, making it the authoritative record of which characters at which versions appear in a given issue:

```json
{
  "character_list": [
    {"uri": "comic://my-comic/characters/explorer?v=2", "role": "protagonist"},
    {"uri": "comic://my-comic/characters/bug-hunter?v=1", "role": "supporting"}
  ],
  "pages": [
    {
      "layout": "manga-dynamic-4",
      "panels": [
        {
          "name": "panel_01",
          "characters": ["comic://my-comic/characters/explorer?v=2"],
          "scene": "Explorer faces a wall of errors",
          "camera": "medium-shot",
          "shape": "tall-left"
        }
      ]
    }
  ]
}
```

This answers three queries trivially:
- **"What characters exist in this project?"** — `comic_character(action='list', project='my-comic')`
- **"What characters are in this issue?"** — read the storyboard's `character_list`
- **"What version of Explorer does issue-002 use?"** — storyboard has `explorer?v=2`

No separate "issue cast" entity is needed. The storyboard IS the cast binding.

## Data Flow

### Character Creation (project-scoped)

```
character-designer
  → comic_create(action='create_character_ref', project='my-comic', name='explorer', ...)
    → internally: generate_image → store_character(project, name, style)
  ← {"uri": "comic://my-comic/characters/explorer", "version": 1}
```

The returned URI has no issue segment. The character exists at the project level, available to any issue.

### Panel Creation (issue-scoped, referencing project characters)

```
panel-artist
  → comic_create(action='create_panel',
      project='my-comic', issue='the-revenge', name='panel_01',
      prompt='Explorer faces errors',
      character_uris=['comic://my-comic/characters/explorer?v=2'])
    → internally: resolve character URI (project-scoped) → get image path
    → internally: generate_image with ref images → store_asset(project, issue, 'panel', name)
  ← {"uri": "comic://my-comic/issues/the-revenge/panels/panel_01", "version": 1}
```

The tool transparently handles both project-scoped character URIs and issue-scoped asset URIs.

### Assembly (resolves both scopes)

```
strip-compositor
  → comic_create(action='assemble_comic',
      project='my-comic', issue='the-revenge',
      layout={
        "cover": {"uri": "comic://my-comic/issues/the-revenge/covers/cover"},
        "pages": [
          {
            "layout": "2x2",
            "panels": [
              {"uri": "comic://my-comic/issues/the-revenge/panels/panel_01", ...}
            ]
          }
        ],
        "characters": [
          {"uri": "comic://my-comic/characters/explorer?v=2"}
        ]
      })
    → internally: resolve all URIs (both scopes) → base64 encode → produce HTML
  ← {"output_path": "/path/to/final.html", "pages": 3, "images_embedded": 8}
```

### Recipe Context Variables

All recipe context variables use the new URI format:

```yaml
# Project-scoped — no issue in URI
character_sheet:
  - "comic://my-comic/characters/explorer?v=1"
  - "comic://my-comic/characters/bug-hunter?v=1"
style_guide: "comic://my-comic/styles/manga?v=1"

# Issue-scoped — issue in URI
panel_results:
  - "comic://my-comic/issues/the-revenge/panels/panel_01?v=1"
  - "comic://my-comic/issues/the-revenge/panels/panel_02?v=1"
cover_results: "comic://my-comic/issues/the-revenge/covers/cover?v=1"
```

## Service Layer Changes

### `store_character`

`issue_id` parameter becomes optional. It is stored in `metadata.json` as `origin_issue_id` for provenance only — it is NOT part of the URI:

```python
async def store_character(self, project_id, name, style, *, issue_id=None, ...)
    # issue_id → metadata["origin_issue_id"] (provenance only)
    # URI returned: comic://project/characters/name?v=N (no issue)
```

### `get_character`

Unchanged — already project-scoped with no `issue` parameter.

### `list_characters`

URI generation simplified. No more `origin_issue_id` lookup for URI construction:

```python
uri = ComicURI.for_character(project_id, char_slug, version=latest_version)
```

### `store_style` / `get_style` / `list_styles`

Same pattern as characters: `issue_id` optional for provenance, URI is project-scoped.

### Issue-Scoped Methods

`store_asset`, `get_asset`, `list_assets` — unchanged in behavior, but URI generation uses the new 5-segment format:

```python
uri = ComicURI.for_asset(project_id, issue_id, asset_type, name, version=version)
# → comic://project/issues/issue/panels/name?v=N
```

## Tool Layer Changes

### `_parse_uri_params`

Updated to handle both URI formats:

- Project-scoped URI → sets `project`, `type`, `name` in params. Does NOT set `issue`.
- Issue-scoped URI → sets `project`, `issue`, `type`, `name` in params.
- Explicit params always win over URI-derived params (via `setdefault`).

### `comic_create` Actions

| Action | Character URIs Accepted | URI Returned |
|--------|------------------------|--------------|
| `create_character_ref` | N/A | `comic://project/characters/name?v=N` |
| `create_panel` | Project-scoped character URIs | `comic://project/issues/issue/panels/name?v=N` |
| `create_cover` | Project-scoped character URIs | `comic://project/issues/issue/covers/name?v=N` |
| `review_asset` | Both scopes (target + refs) | Echo of input URI |
| `assemble_comic` | Both scopes in layout | N/A (returns `output_path`) |

### `preview` Action on `comic_asset`

Handles both URI formats — resolves project-scoped URIs via `get_character`/`get_style`, issue-scoped URIs via `get_asset`.

## Error Handling

- **Invalid scheme** — `InvalidComicURI` with message identifying the bad scheme
- **Wrong segment count** — `InvalidComicURI` with the raw URI for debugging
- **Unknown collection name** — `InvalidComicURI` listing valid collections
- **Empty segments** — `InvalidComicURI` identifying which segment is empty
- **Project-scoped type with `issues/` prefix** — `InvalidComicURI` explaining the type is project-scoped
- **Issue-scoped type without `issues/` prefix** — `InvalidComicURI` explaining the type requires an issue

## Testing Strategy

### Unit Tests for `ComicURI`

- Parse 3-segment project-scoped URIs (characters, styles)
- Parse 5-segment issue-scoped URIs (all issue types)
- Parse with and without `?v=N`
- Reject wrong scheme, empty segments, unknown types
- Reject project-scoped type in issue-scoped format and vice versa
- `__str__` round-trips for both formats
- `__repr__` wraps `__str__`
- `is_project_scoped` / `is_issue_scoped` / `is_latest` properties
- Builder methods produce correct URIs and reject wrong scope

### Integration Tests

- `create_character_ref` returns project-scoped URI
- `create_panel` with project-scoped character URIs resolves correctly
- `assemble_comic` resolves mix of project-scoped and issue-scoped URIs
- `list_characters` returns project-scoped URIs without issue segment
- `list_assets` returns issue-scoped URIs with issue segment
- CRUD tools accept both URI formats via `_parse_uri_params`

## Migration from v1

| v1 URI | v2 URI | Change |
|--------|--------|--------|
| `comic://proj/issue-001/character/explorer` | `comic://proj/characters/explorer` | Dropped issue, pluralized type |
| `comic://proj/issue-001/style/manga` | `comic://proj/styles/manga` | Dropped issue, pluralized type |
| `comic://proj/issue-001/panel/panel_01` | `comic://proj/issues/issue-001/panels/panel_01` | Added `issues/` prefix, pluralized type |
| `comic://proj/issue-001/cover/cover` | `comic://proj/issues/issue-001/covers/cover` | Added `issues/` prefix, pluralized type |
| `comic://proj/issue-001/storyboard/main` | `comic://proj/issues/issue-001/storyboards/main` | Added `issues/` prefix, pluralized type |

All existing code referencing v1 URIs must be updated. There is no backward-compatibility layer — v1 URIs will fail to parse under the v2 parser.

## Implementation Priority

| Priority | Task |
|----------|------|
| P0 | Update `ComicURI` dataclass — `issue` becomes `Optional[str]`, add `is_project_scoped`/`is_issue_scoped` |
| P0 | Update parser — handle 3-segment and 5-segment formats |
| P0 | Update `__str__` — format based on scope |
| P0 | Update builders — `for_character`/`for_style` drop `issue` param |
| P0 | Update `store_character`/`store_style` — `issue_id` optional, URI without issue |
| P0 | Update `list_characters`/`list_styles` — URI without issue |
| P0 | Update `_parse_uri_params` — handle both formats |
| P0 | Update `comic_create` actions — new URI formats |
| P0 | Update all existing tests for v2 URIs |
| P1 | Update agent instructions for new URI format |
| P1 | Update recipe for new URI format |
| P1 | Update `context/comic-instructions.md` |

## Open Questions

None. The design was fully validated through brainstorming with the user.
