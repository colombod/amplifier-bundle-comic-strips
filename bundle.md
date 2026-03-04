---
bundle:
  name: comic-strips
  version: 1.0.0
  description: AI-generated comic strips from Amplifier sessions and project stories

includes:
  - bundle: git+https://github.com/microsoft/amplifier-bundle-stories@main
  - bundle: git+https://github.com/microsoft/amplifier-bundle-browser-tester@main#subdirectory=behaviors/browser-tester.yaml
  - bundle: comic-strips:behaviors/comic-strips
---

# Comic Strips Bundle

Transform Amplifier sessions and project stories into visually compelling multi-page comic strips with consistent characters using AI-powered visual storytelling.

## What This Bundle Provides

### Visual Styles

Six distinct visual styles for comic generation:

- **Manga** - Japanese-inspired sequential art with dynamic panel layouts and expressive characters
- **Superhero** - Bold, action-packed American comic book style with dramatic poses and vivid colors
- **Indie** - Hand-drawn aesthetic with unique artistic voice and experimental layouts
- **Newspaper** - Classic daily strip format with clean lines and accessible humor
- **Ligne Claire** - European clear-line style inspired by Herge and Franco-Belgian comics
- **Retro Americana** - Vintage mid-century American illustration with halftone dots and warm palettes

### Specialist Agents (6)

Six dedicated agents handle different aspects of comic creation:

- **style-curator** - Visual style definition and adaptation
- **storyboard-writer** - Panel breakdown, dialogue, pacing, and page layout structure
- **character-designer** - Visual character reference sheets for consistency
- **panel-artist** - Panel image generation with character references
- **cover-artist** - Cover page image generation with character references
- **strip-compositor** - Multi-page HTML assembly with SVG layouts and visual QA

### Tools

- **`comic_create`** - High-level image creation tool with five actions: `create_character_ref`, `create_panel`, `create_cover`, `review_asset`, and `assemble_comic`. This is the primary interface for all image generation and comic assembly. All binary operations (image generation, base64 encoding, file I/O) are internal to this tool — agents work with `comic://` URIs only.
- **`comic_asset` / `comic_character` / `comic_style` / `comic_project`** - CRUD tools for comic metadata and text content. All responses include a `uri` field using the `comic://` URI protocol.

> **`comic://` URI v2 — Two scopes:**
> - **Project-scoped** (characters, styles — shared across all issues):
>   `comic://project/characters/name` and `comic://project/styles/name`
> - **Issue-scoped** (panels, covers, storyboards, and other per-issue assets):
>   `comic://project/issues/issue/panels/name` and `comic://project/issues/issue/covers/name`

> **Note:** `generate_image` is an internal implementation detail of `comic_create`. It is not exposed to agents and does not appear in agent tool lists. Agents never call `generate_image` directly.

### Automated Workflows

- **session-to-comic** - End-to-end recipe that transforms an Amplifier session into a complete comic strip

## Quick Start

Create multi-page comics with consistent characters from your Amplifier sessions:

> "Turn my last debugging session into a manga-style comic strip"

> "Create a superhero comic showing how we built the authentication feature"

> "Generate a newspaper strip summarizing today's code review"

Characters are automatically given visual reference sheets so they look consistent across every panel and page.

@comic-strips:context/comic-instructions.md
