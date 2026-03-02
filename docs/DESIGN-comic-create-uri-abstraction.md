# Comic URI Protocol and `comic_create` Abstraction Layer

## Goal

Eliminate base64 image data from LLM conversation context by introducing a `comic://` URI protocol and a high-level `comic_create` tool that keeps all binary operations internal to the tool layer.

## Background

The comic-strips pipeline has a critical architectural flaw: base64-encoded image data leaks into LLM conversation context through tool results, causing approximately 15-16 MB of binary data to enter the strip-compositor's context for a typical 6-panel comic.

### Confirmed Leak Vectors

| Vector | Agent | Mechanism | Estimated Size |
|--------|-------|-----------|----------------|
| `batch_encode` all panels | strip-compositor | `comic_asset(action='batch_encode', format='data_uri')` returns all panel data URIs in one tool result | ~8 MB |
| Character reference images | strip-compositor | `comic_character(action='get', format='data_uri')` x 4-6 characters | ~4-6 MB |
| Cover + avatar retrieval | strip-compositor, cover-artist | `comic_asset(action='get', format='data_uri')` | ~2-3 MB |
| `{{cover_results}}` recipe variable | recipe state passed to compositor prompt | Cover-artist returns HTML with embedded base64 as its output text | ~2-3 MB |

### What Is Already Clean

- **`generate_image` tool** -- writes to disk, returns only `{"path": "/abs/path/image.png"}`. Zero base64 leak.
- **Panel-artist** -- uses `format='path'` for character references, passes paths to `generate_image`.
- **Character-designer** -- generates reference sheets, stores via `comic_character`.
- **Recipe `{{character_sheet}}`** -- contains only path strings, not base64.

The leak is entirely on the **retrieval and assembly side**, not the generation side.

## Approach

### Core Principle

**Agents reason about comic concepts using identifiers. Tools handle all binary operations internally. Image bytes never enter conversation context or recipe state.**

Text and metadata (style guides, storyboard specs, character descriptions) flow through agent context because that is creative context agents need for decision-making. Binary image data stays internal to tools.

### Design Strategy

Rather than patching individual leak points, we raise the abstraction level of the tools themselves. Agents work with **identifiers** (project IDs, character IDs, panel IDs, asset URIs) and the tools handle all image plumbing internally. A new `comic://` URI protocol provides a universal, human-readable reference format that flows between agents, recipe stages, and tool calls.

## Architecture

### Layering

```
Agents see:        comic_create    (URIs in, URIs out)
                   comic_asset / comic_character / comic_style / comic_project
                                   (text/metadata CRUD, URI-native)

Tools use          generate_image  (prompt + paths -> file on disk)
internally:        storage layer   (read/write bytes)
                   encoding        (base64 for HTML assembly)
                   vision API      (for review_asset)
```

Agents work in **comic domain concepts**. Tools work in **files and APIs**. Clean separation.

## Components

### The `comic://` URI Protocol

Universal asset reference format used everywhere in the system.

**Format:**

```
comic://project/issue/type/name
comic://project/issue/type/name?v=2
```

**Rules:**
- Fully qualified: project, issue, type, and name are always present
- Version is a query parameter `?v=N`
- Absence of version means latest
- Human-readable in logs, recipe context, and debugging output

**Asset types:** `panel`, `cover`, `avatar`, `character`, `storyboard`, `style`, `research`, `final`

**Examples:**

```
comic://my-comic/issue-001/panel/panel_01
comic://my-comic/issue-001/character/the-explorer
comic://my-comic/issue-001/cover/cover
comic://my-comic/issue-001/character/the-explorer?v=2
comic://my-comic/issue-001/storyboard/main
comic://my-comic/issue-001/style/manga
```

### New Tool: `comic_create`

High-level orchestration tool with five actions. Binary stays internal; agents receive only URIs and text.

#### Action: `create_character_ref`

**Called by:** character-designer

**Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `project` | string | yes | Project identifier |
| `issue` | string | yes | Issue identifier |
| `name` | string | yes | Character name/slug |
| `visual_traits` | string | yes | Visual description of the character |
| `distinctive_features` | string | yes | Features that make the character recognizable |
| `personality` | string | no | Personality context for expression choices |
| `prompt` | string | yes | Generation prompt for the reference sheet |

**Internally:** Composes prompt from style guide and traits, calls `generate_image`, stores result in character roster.

**Returns:**

```json
{"uri": "comic://proj/issue/character/name", "version": 1}
```

#### Action: `create_panel`

**Called by:** panel-artist

**Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `project` | string | yes | Project identifier |
| `issue` | string | yes | Issue identifier |
| `name` | string | yes | Panel name (e.g. `panel_03`) |
| `prompt` | string | yes | Scene description for image generation |
| `character_uris` | list[string] | no | List of `comic://` character URIs to include |
| `size` | string | no | `landscape`, `portrait`, or `square` (default: `square`) |
| `camera_angle` | string | no | Camera framing hint (e.g. `medium-shot`, `close-up`, `wide`) |

**Internally:** Resolves each character URI to get reference image paths from storage, fetches style guide, calls `generate_image` with `reference_images`, stores result as a panel asset.

**Returns:**

```json
{"uri": "comic://proj/issue/panel/panel_03", "version": 1}
```

#### Action: `create_cover`

**Called by:** cover-artist

**Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `project` | string | yes | Project identifier |
| `issue` | string | yes | Issue identifier |
| `prompt` | string | yes | Cover concept description |
| `character_uris` | list[string] | no | Featured character URIs |
| `title` | string | yes | Comic title text |
| `subtitle` | string | no | Subtitle or issue tagline |

**Internally:** Same pattern as `create_panel` -- resolve refs, generate, store.

**Returns:**

```json
{"uri": "comic://proj/issue/cover/cover", "version": 1}
```

#### Action: `review_asset`

**Called by:** panel-artist, cover-artist, strip-compositor

**Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `uri` | string | yes | `comic://` URI of the asset to review |
| `prompt` | string | yes | What to evaluate (consistency, framing, style adherence, etc.) |
| `reference_uris` | list[string] | no | Additional `comic://` URIs for visual comparison |

**Internally:** Resolves target URI to image path on disk, optionally resolves reference URIs, sends all images plus review prompt to a vision-capable model, returns text-only assessment.

**Returns:**

```json
{
  "uri": "comic://proj/issue/panel/panel_03",
  "passed": false,
  "feedback": "Character proportions differ from reference -- head is too large relative to body. Framing is correct."
}
```

**Use cases:**
- **Self-review loop:** Agent creates an asset, reviews it, regenerates with refined prompt if needed.
- **Visual composition analysis:** Compositor uses it to understand panel layout before placing text overlays (where characters are, where negative space exists).
- **Cross-reference consistency:** Passing character reference URIs alongside a panel to check character consistency.

#### Action: `assemble_comic`

**Called by:** strip-compositor

**Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `project` | string | yes | Project identifier |
| `issue` | string | yes | Issue identifier |
| `output_path` | string | yes | Where to write the final HTML file |
| `style_uri` | string | yes | Style guide URI for CSS/layout conventions |
| `layout` | object | yes | Structured layout definition (see Layout Schema) |

**Internally:** Resolves every `comic://` URI in the layout structure to stored images, base64 encodes them, renders SVG/CSS text overlays with bubble shapes and tails, produces self-contained HTML with page navigation.

**Returns:**

```json
{"output_path": "/path/to/final-comic.html", "pages": 4, "images_embedded": 12}
```

### `assemble_comic` Layout Schema

The compositor provides structured layout data with precise text overlay positioning. The agent decides the creative layout; the tool handles rendering.

```json
{
  "title": "The Great Debug",
  "style_uri": "comic://proj/issue/style/manga",
  "cover": {
    "uri": "comic://proj/issue/cover/cover",
    "title": "The Great Debug",
    "subtitle": "Issue #1",
    "branding": "AmpliVerse"
  },
  "pages": [
    {
      "layout": "manga-dynamic-4",
      "panels": [
        {
          "uri": "comic://proj/issue/panel/panel_01",
          "shape": "tall-left",
          "overlays": [
            {
              "type": "speech",
              "shape": "oval",
              "tail": {"points_to": {"x": 65, "y": 40}},
              "position": {"x": 10, "y": 5, "width": 35, "height": 20},
              "text": "Something's wrong with the auth module!",
              "font_size": "medium"
            },
            {
              "type": "caption",
              "shape": "rectangular",
              "position": {"x": 0, "y": 0, "width": 100, "height": 12},
              "text": "Meanwhile, in the codebase...",
              "style": "narrator"
            }
          ]
        },
        {
          "uri": "comic://proj/issue/panel/panel_02",
          "shape": "wide-top-right",
          "overlays": [
            {
              "type": "thought",
              "shape": "cloud",
              "tail": {"points_to": {"x": 30, "y": 50}},
              "position": {"x": 55, "y": 10, "width": 40, "height": 25},
              "text": "I've seen this pattern before..."
            }
          ]
        }
      ]
    }
  ]
}
```

**Overlay positioning:** All coordinates are percentages (0-100) relative to panel dimensions. Resolution-independent.

**Callout shapes:**

| Shape | Use |
|-------|-----|
| `oval` | Normal speech |
| `cloud` | Thought bubble |
| `rectangular` | Narrator caption |
| `jagged` | Shouting / exclamation |
| `whisper` | Dashed outline, quiet speech |

**Tail direction:** The `points_to` field specifies where the tail aims within the panel (pointing to the speaking character), rendered as SVG.

**Page layouts:** Defined per style. Manga has irregular dynamic shapes, newspaper strips have equal fixed rectangles, superhero comics have dramatic diagonals. The storyboard-writer selects layout identifiers informed by the style guide's panel conventions.

**Compositor workflow:**
1. Get panel URIs and storyboard from recipe context
2. Read storyboard text (dialogue, captions per panel)
3. Read style guide (bubble conventions, layout rules)
4. For each panel: call `review_asset` to understand visual composition (character positions, negative space)
5. Make precise text placement decisions based on visual analysis
6. Call `assemble_comic` with the complete layout structure

### Changes to Existing Tools

#### `comic_asset`

- All responses include a `uri` field
- Accept `uri` as input (alternative to decomposed `project` + `issue` + `type` + `name`)
- **New action: `preview`** -- resolves URI to disk path and returns a platform-appropriate viewer command hint
- **Removed:** `format='base64'` and `format='data_uri'` options from all actions
- **Removed:** `batch_encode` action entirely
- Encoding logic remains in `encoding.py` for `assemble_comic`'s internal use, but is no longer reachable by agents through tool calls

**`preview` action returns:**

```json
{
  "uri": "comic://proj/issue/panel/panel_03",
  "path": "/absolute/path/to/panel_03.png",
  "type": "image/png",
  "hint": "open /absolute/path/to/panel_03.png"
}
```

The hint adapts to platform: `open` on macOS, `xdg-open` on Linux. For HTML assets it opens the browser; for images it opens the default image viewer.

#### `comic_character`

- All responses include a `uri` field
- Accept `uri` as input
- **Removed:** `format='base64'` and `format='data_uri'` options

#### `comic_style`

- All responses include a `uri` field
- No other changes (already text-only)

#### `comic_project`

- No changes needed

### `generate_image` -- Internalized

`generate_image` is removed from the bundle's exposed tool list. It becomes an internal implementation detail of `comic_create`. Agents never see it, never call it, never need to know it exists.

The module remains installed as a dependency; only the tool registration is removed from the bundle surface.

### Storyboard Asset -- Expanded

The storyboard asset now includes page layout structure (panel shapes, arrangement, spatial flow) informed by style guide conventions. This is not a new asset type; it is the same `comic_asset(type='storyboard')` with richer structured content.

The storyboard-writer reads the style guide to learn the panel shape vocabulary available for the chosen style, then makes narrative-informed spatial decisions: splash panels for dramatic reveals, tight panels for rapid-fire dialogue, irregular grids for dynamic action.

## Data Flow

### Recipe Context Variables

All recipe context variables carry URIs and text metadata only. No binary data flows through recipe state.

| Variable | Content | Approximate Size |
|----------|---------|-----------------|
| `{{style_guide}}` | Style URI string | ~60 bytes |
| `{{character_sheet}}` | List of character URIs | ~200-400 bytes |
| `{{storyboard}}` | Storyboard URI | ~60 bytes |
| `{{panel_results}}` | List of panel URIs | ~300-500 bytes |
| `{{cover_results}}` | Cover URI | ~60 bytes |

**Total recipe state: ~1 KB** (down from ~15-16 MB).

### Agent Tool Assignments

| Agent | Tools | Notes |
|-------|-------|-------|
| character-designer | `comic_create` + `comic_style` | Reads style for creative direction, calls `create_character_ref` |
| panel-artist | `comic_create` + `comic_style` | Reads style for prompt crafting, calls `create_panel` + `review_asset` |
| cover-artist | `comic_create` + `comic_style` | Reads style for prompt crafting, calls `create_cover` + `review_asset` |
| strip-compositor | `comic_create` + `comic_style` + `comic_asset` | Reads style for CSS/layout, reads storyboard via `comic_asset`, uses `review_asset` for visual understanding, calls `assemble_comic` |
| storyboard-writer | `comic_asset` + `comic_style` | Reads style for layout conventions, stores storyboard (unchanged pattern) |
| style-curator | `comic_style` | Creates style guides (unchanged) |

Creation agents each go from 3-4 tools down to 2, significantly reducing hallucination surface.

### End-to-End Flow Example

```
1. style-curator    -> comic_style(store)          -> "comic://proj/issue/style/manga"
2. storyboard-writer -> comic_asset(store)          -> "comic://proj/issue/storyboard/main"
3. character-designer -> comic_create(create_char)   -> "comic://proj/issue/character/explorer"
4. panel-artist      -> comic_create(create_panel)   -> "comic://proj/issue/panel/panel_01"
   panel-artist      -> comic_create(review_asset)   -> {passed: false, feedback: "..."}
   panel-artist      -> comic_create(create_panel)   -> "comic://proj/issue/panel/panel_01?v=2"
   panel-artist      -> comic_create(review_asset)   -> {passed: true}
5. cover-artist      -> comic_create(create_cover)   -> "comic://proj/issue/cover/cover"
6. strip-compositor  -> comic_asset(get storyboard)  -> layout structure with panel sequence
   strip-compositor  -> comic_create(review_asset)   -> visual composition descriptions per panel
   strip-compositor  -> comic_create(assemble_comic) -> "/path/to/final.html"
```

At no point does any agent see image bytes. URIs flow forward through recipe context. Each agent resolves what it needs through tool calls.

## Error Handling

- **URI resolution failure:** Tool returns a clear error with the unresolvable URI. Agent can retry or report.
- **Generation failure:** `comic_create` returns error with provider details. Agent can retry with adjusted prompt.
- **Review failure:** If the vision model is unavailable, `review_asset` returns error. Agent can proceed without review or retry.
- **Assembly failure:** If any URI in the layout cannot be resolved, `assemble_comic` reports which URIs failed before producing partial output.
- **Version not found:** Explicit `?v=N` for a non-existent version returns a clear error listing available versions.

## Testing Strategy

- **URI parsing:** Unit tests for `comic://` URI parsing, resolution, and version handling.
- **Action isolation:** Each `comic_create` action tested independently with mocked `generate_image` and storage layers.
- **Integration:** End-to-end test creating a character, panel, and cover, then assembling -- verifying no base64 appears in any tool result.
- **Regression:** Verify `format='base64'`/`format='data_uri'` parameters are rejected with clear errors.
- **Memory:** Monitor context size during a full pipeline run to confirm the ~15 MB reduction.
- **Review loop:** Test `review_asset` with reference URIs, verifying images are sent to vision API and only text returns.

## Implementation Priority

| Priority | Task |
|----------|------|
| P0 | Implement `comic://` URI parsing and resolution |
| P0 | Implement `comic_create` tool with all 5 actions |
| P0 | Update existing CRUD tools to include URI in responses and accept URI as input |
| P0 | Remove `format='base64'` / `format='data_uri'` and `batch_encode` |
| P0 | Remove `generate_image` from bundle tool list |
| P0 | Update all 6 agent instructions |
| P0 | Update recipe YAML for URI-based context variables |
| P0 | Update `comic-instructions.md` context file |
| P1 | Update storyboard schema to include page layout structure |
| P1 | Memory pressure fixes (drain_executor fixture, loop_scope change) |
| P1 | Commit and push all pending fixes from session b34f828e |
| P2 | Verification reviews (serial, not parallel) |
| P2 | End-to-end smoke test with new architecture |

## Open Questions

- Exact set of page layout identifiers per style (to be defined when implementing storyboard expansion).
- Whether `review_asset` should support configurable vision model selection or always use a default.
- Detailed schema validation rules for the `assemble_comic` layout input.
