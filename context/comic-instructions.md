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

- **Main characters (3-4 max)**: Agents with the most tool calls and delegation activity that drove key moments
- **Supporting characters (1-2)**: Agents with one meaningful moment but not central
- **Antagonists**: Real session obstacles (errors, rate limits, failures) visualized as ENVIRONMENTAL THREATS -- walls, storms, barriers. NOT as characters with portraits or dialogue.
- **Cut entirely**: Agents that appeared briefly or did routine work

### Bundle-as-Affiliation Mapping

Agents from the same bundle share visual team markers (color accents, insignia, uniform elements). Different bundles have distinct visual identities.

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

**Format:** `comic://project/issue/type/name` or `comic://project/issue/type/name?v=N`

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

**Rules:**
- Absence of `?v=N` means latest version
- Human-readable in logs, recipe context, and debugging output
- Tools resolve URIs to disk paths internally — agents never handle file paths or bytes directly

## Output Format Requirements

The final comic output must meet these requirements:

- **Self-contained HTML** - Each comic is delivered as a single, self-contained HTML file with no external dependencies. `comic_create(action='assemble_comic')` produces this file.
- **Base64 data URIs** - All images are embedded as base64 data URIs so the file works offline. Base64 encoding is an internal concern of `assemble_comic` — agents never encode images themselves.
- **CSS overlay speech bubbles and captions** - Dialogue and narration are rendered using CSS-positioned overlays on panel images, not baked into the images themselves. Agents specify overlays in the layout JSON passed to `assemble_comic`.
- **Responsive design** - The layout adapts to different viewport sizes, from mobile to desktop, using fluid grids and media queries.
- **Cover page with branding** - The first page is a dedicated cover page displaying the AmpliVerse branding per the style-specific placement rules above.
- **Navigation controls** - Include previous/next navigation controls for paging through the comic strip panels.

## Cross-Agent Data Flow

The comic creation pipeline passes data between agents in five stages:

1. **Research JSON** - The story-researcher agent outputs structured research JSON containing session events, metrics, and narrative arcs extracted from source material.
2. **Style URI** - The style-curator agent stores a structured style guide and returns a `comic://` URI (e.g., `comic://proj/issue/style/manga`). All downstream agents retrieve it via `comic_style(action='get')`.
3. **Storyboard URI** - The storyboard-writer agent generates a storyboard with panel sequence, dialogue, camera angles, page layout structure, and page breaks, stores it, and returns a `comic://` URI.
4. **Panel URIs** - The panel-artist agent renders each panel via `comic_create(action='create_panel')` and returns a `comic://` URI per panel. No image bytes flow through recipe context.
5. **Cover URI** - The cover-artist agent produces the cover via `comic_create(action='create_cover')` and returns a `comic://` URI. No image bytes flow through recipe context.

All recipe context variables carry URIs and text metadata only. Total recipe state is approximately 1 KB.

## Image Generation Rules

All image generation must follow these rules:

- **No text in images** - Never render text, labels, or dialogue inside generated images. All text is added via HTML/CSS overlays by `assemble_comic`.
- **Character consistency** - Maintain consistent character appearance across all panels. Use the same visual descriptors, proportions, and color references throughout. Pass character URIs to `comic_create` so it can include reference images internally.
- **Style guide template base** - Every image prompt must start from the style guide template base established by the style-curator. Do not deviate from the defined visual language.
- **Transparent or solid backgrounds** - Use transparent or solid color backgrounds for panel art to allow clean compositing. Avoid complex backgrounds unless the storyboard explicitly calls for a scene backdrop.
- **Cover as single hero image** - Generate the cover as a single hero image that captures the comic's theme in one compelling composition. Do not generate the cover as a collage or multi-panel layout.
- **Use `comic_create` for all generation** - Agents call `comic_create(action='create_character_ref')`, `comic_create(action='create_panel')`, or `comic_create(action='create_cover')`. The `generate_image` tool is an internal implementation detail of `comic_create` — agents never call it directly.
