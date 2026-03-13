---
bundle:
  name: comic-strips
  version: 1.0.0
  description: AI-generated comic strips from Amplifier sessions and project stories

includes:
  - bundle: git+https://github.com/microsoft/amplifier-bundle-stories@bd2753ec5b69e96aa2a905f8840d257404c717dd
  - bundle: git+https://github.com/microsoft/amplifier-bundle-browser-tester@728beebcf323729e4e6664ee74d2e2d68c4bfb97#subdirectory=behaviors/browser-tester.yaml
  - bundle: comic-strips:behaviors/comic-strips
---

# Comic Strips Bundle

Transform Amplifier sessions and project stories into visually compelling multi-page comic strips with consistent characters using AI-powered visual storytelling.

## What This Bundle Provides

### Visual Styles

Six core visual styles for comic generation:

- **Manga** - Japanese-inspired sequential art with dynamic panel layouts and expressive characters
- **Superhero** - Bold, action-packed American comic book style with dramatic poses and vivid colors
- **Indie** - Hand-drawn aesthetic with unique artistic voice and experimental layouts
- **Newspaper** - Classic daily strip format with clean lines and accessible humor
- **Ligne Claire** - European clear-line style inspired by Herge and Franco-Belgian comics
- **Retro Americana** - Vintage mid-century American illustration with halftone dots and warm palettes

Plus 23 additional style variants -- see README for full gallery.

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

### Interactive Modes (5)

Five interactive modes guide comic creation through a structured workflow:

- **`/comic-brainstorm`** -- Project vision: style, issue count, narrative scope, character roster
- **`/comic-design`** -- Interactive character and storyboard work
- **`/comic-plan`** -- Layout strategy, generation budgets, kick off pipeline
- **`/comic-review`** -- Inspect results, surgical retries
- **`/comic-publish`** -- Final QA, ship it

Mode chain: brainstorm -> design -> plan -> review -> publish. Double-confirmation on all transitions.

### Automated Workflows

- **session-to-comic** - End-to-end thin orchestrator calling 3 composable sub-recipes:
  - **saga-plan** - Saga planning (text-only, low cost, approval gate)
  - **design-characters** - Character reference sheet generation (image gen, project-scoped)
  - **issue-art** - Per-issue panel art, cover, and composition (image gen, high cost)
- **issue-compose** - Reassemble HTML from existing assets (zero image gen)
- **issue-retry** - Surgical single-issue re-generation from existing storyboard and characters

## Quick Start

Create multi-page comics with consistent characters from your Amplifier sessions:

> "Turn my last debugging session into a manga-style comic strip"

> "Create a superhero comic showing how we built the authentication feature"

> "Generate a newspaper strip summarizing today's code review"

Characters are automatically given visual reference sheets so they look consistent across every panel and page.

@comic-strips:context/comic-instructions.md
