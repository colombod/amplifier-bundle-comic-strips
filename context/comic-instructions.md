# Comic Strip Creation Guidelines

Shared instructions for all comic-strip agents in the AmpliVerse ecosystem.

## AmpliVerse Branding

### Required on Every Cover

- **Publisher name**: AmpliVerse
- **Logo**: ![AmpliVerse Logo](https://github.com/microsoft-amplifier.png)

Every comic strip cover must include AmpliVerse branding. The placement varies by visual style to maintain aesthetic coherence:

| Style | Branding Placement |
|---|---|
| Manga | Vertical along spine right side |
| Superhero | Top-left corner box |
| Indie | Subtle watermark in gutter |
| Newspaper | Masthead across top |
| Ligne Claire | Top-center clean banner |
| Retro Americana | Circular badge top-right |

### Logo Requirements (Non-Negotiable)

The AmpliVerse logo MUST be the actual Amplifier GitHub avatar image:
- Source: `https://github.com/microsoft-amplifier.png`
- Format: PNG image embedded as base64 `<img>` tag in the final HTML
- NOT CSS text, NOT a colored badge, NOT a `<div>` with styling
- The actual pixel image from the GitHub avatar URL
- Base64 embedding is handled internally by `comic_create(action='assemble_comic')` — agents specify branding via the layout schema, not manually

## Character Selection Rules

Characters represent agents from the actual session transcript, not inventions.

- **Main characters (4-5 default)**: Agents with the most tool calls and delegation activity that drove key moments
- **Supporting characters (1-2)**: Agents with one meaningful moment but not central
- **Total default: 5-6 characters.** Recipe param `max_characters` can override.
- **Antagonists**: Real session obstacles (errors, rate limits, failures) visualized as ENVIRONMENTAL THREATS -- walls, storms, barriers. NOT as characters with portraits or dialogue.
- **Cut entirely**: Agents that appeared briefly or did routine work

### Bundle-as-Affiliation Mapping

Agents from the same bundle share visual team markers (color accents, insignia, uniform elements). Different bundles have distinct visual identities.

## Issue Budget Standards

Every comic issue has default budgets. The user can override these via recipe params.

| Budget Item | Default | Override Param | Notes |
|---|---|---|---|
| Cover | 1 page | — | Always present, always first page |
| Cast page | 1 page | — | Always present, shows character backstories |
| Story pages | 5 | `max_pages` | Adjustable per story needs |
| Panels per page | 3-6 | `panels_per_page` | Pages with 2 panels allowed for dramatic full-spread moments |
| Characters | 5-6 (4-5 main + 1-2 supporting) | `max_characters` | Curate the most interesting cast |

### Why Budgets

- **Predictable output**: Consistent issue size. No 20-page monsters.
- **Readable panels**: 3-6 panels per page balances density with readability. 2-panel pages for impact.
- **Bounded cost**: Image generation is capped by pages x panels-per-page + characters + cover.
- **Multi-issue by design**: When a story is too rich for one issue, split into a saga.
- **User-steerable**: All limits can be adjusted via recipe context params when needed.

### Page Structure

A standard issue follows this structure:

| Page | Content | Typical Panels |
|---|---|---|
| 1 | Cover | 1 (hero image) |
| 2 | Cast | Character portraits + backstories |
| 3 | Setup / Challenge | 3-6 (or 2 for a dramatic full-spread opening) |
| 4 | Rising Action / Approach | 3-6 |
| 5 | Climax / Turning Point | 3-6 (or 2 for maximum impact) |
| 6 | Resolution / Results | 3-6 |

### Sagas (Multi-Issue Stories)

When a story exceeds one issue's budget, it becomes a **saga** -- multiple issues in the same project sharing characters, style, and narrative continuity.

- A saga is a project with multiple issues. No special entity needed.
- Characters are project-scoped -- designed once, reused across issues.
- Styles are project-scoped -- consistent visual language across issues.
- Each issue is a standalone HTML file with its own cover.
- The storyboard-writer decides if a saga is needed and plans the split.
- Each issue must have its own complete mini-arc (setup, tension, resolution or cliffhanger).

## Evidence-Based Storytelling

All comic narratives must follow these rules:

- **Trace to research data** - Every story element must trace back to actual research data from session analysis or project artifacts. Cite the source session, commit, or metric.
- **Never fabricate** - Do not fabricate events, dialogue, or outcomes. All depicted scenarios must reflect real actions that occurred in the source material.
- **Visualize technical concepts** - Transform abstract technical concepts (deployments, refactors, debugging) into visual metaphors that are accurate and accessible.
- **Characters represent agents not real people** - Comic characters depict Amplifier agents, tools, and system components. They do not represent or caricature real individuals.

### Dialogue Rules

- **Speech bubbles contain ONLY natural character dialogue** -- characters speak as characters, not as data readouts
- **NEVER in speech bubbles**: UUIDs, session IDs, file paths, line numbers, token counts, raw error messages, JSON
- **Factual anchors in CAPTION BOXES only** -- the narrator provides metrics and context, characters provide drama

## The `comic://` URI Protocol

All assets in the pipeline are referenced using `comic://` URIs. These identifiers flow between agents, recipe stages, and tool calls. Image bytes never enter conversation context.

**Two scopes — choose based on asset lifetime:**

**Characters and styles are project-scoped** (shared and reusable across all issues within a project):
```
comic://project/characters/name
comic://project/styles/name
comic://project/characters/name?v=N
```

**Panels, covers, storyboards, and other per-issue assets are issue-scoped** (bound to a specific issue):
```
comic://project/issues/issue/panels/name
comic://project/issues/issue/covers/name
comic://project/issues/issue/storyboards/name
comic://project/issues/issue/research/name
comic://project/issues/issue/finals/name
comic://project/issues/issue/panels/name?v=N
```

**Examples:**
```
comic://my-comic/characters/the-explorer
comic://my-comic/characters/the-explorer?v=2
comic://my-comic/styles/manga
comic://my-comic/issues/issue-001/panels/panel_01
comic://my-comic/issues/issue-001/covers/cover
comic://my-comic/issues/issue-001/storyboards/main
```

**Collection names are always plural:** `characters`, `styles`, `panels`, `covers`, `storyboards`, `research`, `finals`, `avatars`.

**Rules:**
- Absence of `?v=N` means latest version
- Human-readable in logs, recipe context, and debugging output
- Tools resolve URIs to disk paths internally — agents never handle file paths or bytes directly
- Characters and styles are **project-scoped**: no issue segment, reusable across all issues
- Panels, covers, and other assets are **issue-scoped**: always include the `issues/<issue>/` segment

## Output Format Requirements

The final comic output must meet these requirements:

- **Self-contained HTML** - Each comic is delivered as a single, self-contained HTML file with no external dependencies. `comic_create(action='assemble_comic')` produces this file.
- **Base64 data URIs** - All images are embedded as base64 data URIs so the file works offline. Base64 encoding is an internal concern of `assemble_comic` — agents never encode images themselves.
- **CSS overlay speech bubbles and captions** - Dialogue and narration are rendered using CSS-positioned overlays on panel images, not baked into the images themselves. Agents specify overlays in the layout JSON passed to `assemble_comic`.
- **Responsive design** - The layout adapts to different viewport sizes, from mobile to desktop, using fluid grids and media queries.
- **Cover page with branding** - The first page is a dedicated cover page displaying the AmpliVerse branding per the style-specific placement rules above.
- **Navigation controls** - Include previous/next navigation controls for paging through the comic strip panels.

## Cross-Agent Data Flow

The comic creation pipeline passes data between agents in seven stages:

0. **Session Discovery** *(new in v7.7.0)* - The `discover-sessions` step receives a flexible `{{source}}` input — a project name, session ID(s), file path(s), or descriptive phrase. The `stories:story-researcher` agent discovers and consolidates the relevant Amplifier session data using its native tools (git/gh CLI, grep, `read_file`, delegation to `foundation:explorer`). It stores the consolidated material as a comic asset and returns a `comic://` URI (`{{session_data}}`). This decouples the pipeline from Amplifier's internal storage layout — the researcher explores creatively rather than following hardcoded paths.
1. **Research JSON** - The story-researcher agent loads the consolidated session data via `comic_asset(action='get', uri='{{session_data}}')` and extracts structured research JSON containing session events, metrics, and narrative arcs for comic creation.
2. **Style URI** *(project-scoped)* - The style-curator agent stores a structured style guide and returns a project-scoped `comic://` URI (e.g., `comic://proj/styles/manga`). Styles are shared across all issues of a project. All downstream agents retrieve the style via `comic_style(action='get')`.
3. **Storyboard + Character URIs** *(storyboard is issue-scoped; characters are project-scoped)* - The storyboard-writer agent calls `comic_create(action='list_layouts')` to discover valid layout IDs, then generates a storyboard with panel sequence, dialogue, camera angles, page layout structure, page breaks, and a `character_list` defining the cast. It stores the storyboard at an issue-scoped URI (e.g., `comic://proj/issues/issue-001/storyboards/storyboard`). The `character_list` is then fed to character-designer, which creates a project-scoped character URI for each character (e.g., `comic://proj/characters/the-explorer`). These project-scoped URIs act as cast bindings — they tie the visual reference to the character across any panel or issue.
4. **Layout Validation** *(deterministic checkpoint)* - After storyboard generation, a `validate-storyboard` step calls `comic_create(action='validate_storyboard')` to check all `page_layouts` layout IDs against the renderer's template dictionary. Invalid IDs are rejected with suggestions before any image generation starts. The validation result is shown in the approval gate so the human reviewer can see whether layouts are valid.
5. **Panel URIs** *(issue-scoped)* - The panel-artist agent renders each panel via `comic_create(action='create_panel')` and returns an issue-scoped `comic://` URI per panel (e.g., `comic://proj/issues/issue-001/panels/panel_01`). No image bytes flow through recipe context.
6. **Cover URI** *(issue-scoped)* - The cover-artist agent produces the cover via `comic_create(action='create_cover')` and returns an issue-scoped `comic://` URI (e.g., `comic://proj/issues/issue-001/covers/cover`). No image bytes flow through recipe context.

**Characters and styles are project-scoped** — defined once, shared across all issues.
**Panels, covers, storyboards, and other assets are issue-scoped** — each issue has its own set.

All recipe context variables carry URIs and text metadata only. Total recipe state is approximately 1 KB.

## Image Generation Rules

All image generation must follow these rules:

- **No text in images** - Never render text, labels, or dialogue inside generated images. All text is added via HTML/CSS overlays by `assemble_comic`.
- **Character consistency** - Maintain consistent character appearance across all panels. Use the same visual descriptors, proportions, and color references throughout. Pass character URIs to `comic_create` so it can include reference images internally.
- **Style guide template base** - Every image prompt must start from the style guide template base established by the style-curator. Do not deviate from the defined visual language.
- **Transparent or solid backgrounds** - Use transparent or solid color backgrounds for panel art to allow clean compositing. Avoid complex backgrounds unless the storyboard explicitly calls for a scene backdrop.
- **Cover as single hero image** - Generate the cover as a single hero image that captures the comic's theme in one compelling composition. Do not generate the cover as a collage or multi-panel layout.
- **Use `comic_create` for all generation** - Agents call `comic_create(action='create_character_ref')`, `comic_create(action='create_panel')`, or `comic_create(action='create_cover')`. The `generate_image` tool is an internal implementation detail of `comic_create` — agents never call it directly.
