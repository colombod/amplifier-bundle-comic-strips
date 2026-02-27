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
- Format: PNG image fetched and embedded as base64 `<img>` tag
- NOT CSS text, NOT a colored badge, NOT a `<div>` with styling
- The actual pixel image from the GitHub avatar URL

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

## Output Format Requirements

The final comic output must meet these requirements:

- **Self-contained HTML** - Each comic is delivered as a single, self-contained HTML file with no external dependencies.
- **Base64 data URIs** - All images are embedded as base64 data URIs so the file works offline and can be shared as a single artifact.
- **CSS overlay speech bubbles and captions** - Dialogue and narration are rendered using CSS-positioned overlays on panel images, not baked into the images themselves.
- **Responsive design** - The layout adapts to different viewport sizes, from mobile to desktop, using fluid grids and media queries.
- **Cover page with branding** - The first page is a dedicated cover page displaying the AmpliVerse branding per the style-specific placement rules above.
- **Navigation controls** - Include previous/next navigation controls for paging through the comic strip panels.

## Cross-Agent Data Flow

The comic creation pipeline passes data between agents in five stages:

1. **Research JSON** - The story-researcher agent outputs structured research JSON containing session events, metrics, and narrative arcs extracted from source material.
2. **Style guide** - The style-curator agent produces a style guide defining the visual language: color palette, line weights, panel proportions, and character design rules for the chosen style.
3. **Storyboard** - The storyboard-writer agent generates a storyboard breaking the narrative into sequenced panels with dialogue, camera angles, and pacing notes.
4. **Panel images base64** - The panel-artist agent renders each panel as a base64-encoded image following the style guide and storyboard specifications.
5. **Cover image base64** - The cover-artist agent produces the cover as a base64-encoded image incorporating AmpliVerse branding per the style placement rules.

## Image Generation Rules

All image generation must follow these rules:

- **No text in images** - Never render text, labels, or dialogue inside generated images. All text is added via HTML/CSS overlays in the compositor stage.
- **Character consistency** - Maintain consistent character appearance across all panels. Use the same visual descriptors, proportions, and color references throughout.
- **Style guide template base** - Every image prompt must start from the style guide template base established by the style-curator. Do not deviate from the defined visual language.
- **Transparent or solid backgrounds** - Use transparent or solid color backgrounds for panel art to allow clean compositing. Avoid complex backgrounds unless the storyboard explicitly calls for a scene backdrop.
- **Cover as single hero image** - Generate the cover as a single hero image that captures the comic's theme in one compelling composition. Do not generate the cover as a collage or multi-panel layout.
