# amplifier-bundle-comic-strips

Transform Amplifier sessions into AI-generated multi-page comic strips with consistent characters, dramatic storytelling, and AmpliVerse publisher branding.

## Prerequisites

- [Amplifier CLI](https://github.com/microsoft/amplifier) installed
- At least one image-capable provider configured:
  - **OpenAI** with `gpt-image-1` (recommended)
  - **Google** with Gemini Imagen
- Provider API keys configured in `~/.amplifier/settings.yaml`

## Installation

```bash
# Add and activate for current project
amplifier bundle add git+https://github.com/colombod/amplifier-bundle-comic-strips@main
amplifier bundle use comic-strips

# Or install globally so it's always available across all sessions
amplifier bundle add git+https://github.com/colombod/amplifier-bundle-comic-strips@main --app
```

## Quick Start

Generate a comic from an Amplifier session:

```bash
# Using the session-to-comic recipe (CLI)
amplifier tool invoke recipes \
  operation=execute \
  recipe_path=comic-strips:recipes/session-to-comic.yaml \
  context='{"session_file": "path/to/events.jsonl", "style": "sin-city"}'

# Or conversationally in a session
amplifier run "execute session-to-comic with session_file=./my-session.jsonl style=manga"

# Or just talk naturally
amplifier run "Turn my last session into a Sin City noir comic strip"
```

The recipe pauses at an approval gate after the storyboard. Review the character
cast and narrative arc, then approve to proceed with image generation.

## Style Gallery

28 predefined visual styles, plus custom descriptions:

| Style | Aesthetic |
|-------|-----------|
| **manga** | Japanese B&W ink wash, speed lines, expressive characters, right-to-left flow |
| **superhero** | Bold saturated colors, dynamic poses, dramatic perspective, cel-shading |
| **sin-city** | Frank Miller noir: extreme B&W contrast, bold silhouettes, selective color splashes, rain-soaked |
| **watchmen** | Muted secondary palette, rigid 3x3 grid, clinical linework, no sound effects |
| **indie** | Gritty painterly aesthetic, dark atmosphere, irregular borders, muted palette |
| **newspaper** | Clean line art, horizontal strip format, punchline pacing, daily-strip feel |
| **ligne-claire** | European clear-line (Tintin/Herge), flat bright colors, detailed backgrounds |
| **retro-americana** | Vintage halftone dots, warm palette, cheerful proportions, 1950s aesthetic |
| **berserk** | Monochrome Gothic hatching, grotesque detail, dark fantasy |
| **cuphead** | 1930s rubber-hose animation, watercolor backgrounds, vintage film grain |
| **ghibli** | Watercolor washes, earthy natural palette, magical realism, gentle forms |
| **attack-on-titan** | Gritty cross-hatching, extreme scale contrast, raw emotional intensity |
| **spider-man** | Dynamic perspective, halftone dots, red/blue web-slinger aesthetic |
| **x-men** | Jim Lee 90s, hyper-detailed crosshatching, bold team colors |
| **solo-leveling** | Dark atmospheric, supernatural energy bursts, sharp digital linework |
| **gundam** | Hard sci-fi mechanical precision, military color-blocking |
| **transformers** | Metallic rendering, faction colors, energon highlights |
| **tatsunoko** | Bold cel-shaded primaries, retro 70s anime warmth |
| **witchblade** | Nocturnal midnight palette, organic curves, dark action |
| **dylan-dog** | Strict B&W monochrome, rigid Bonelli 3-strip grid, crosshatch tonal |
| **tex-willer** | Western frontier ink-wash, earth-tone landscape panels |
| **disney-classic** | Round fluid forms, bright saturated primaries, expressive squash-and-stretch |
| **bendy** | 1930s horror cartoon, ink splatter, sepia-to-black palette |
| **hellraiser** | Body-horror precision, clinical blue-steel palette, visceral detail |
| **naruto** | Warm earthy tones, fisheye lens, feudal Japanese architecture |
| **jujutsu-kaisen** | Oppressive indigo palette, aggressive cross-hatching, inverted speech bubbles |
| **one-piece** | Vibrant saturated adventure colors, wildly exaggerated proportions |
| **go-nagai** | Stark high-contrast B&W with blood crimson, psychedelic swirl patterns |

Custom styles are also supported -- describe any aesthetic and the style-curator
agent will interpret it into a full style guide.

## Recipe Parameters

### session-to-comic

End-to-end pipeline: research, storyboard, character design, panel art, cover, composition.

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `session_file` | Yes | -- | Path to `events.jsonl` or session ID |
| `style` | No | `"superhero"` | Style name from gallery above, or any custom description |
| `output_name` | No | `comic-{timestamp}` | Output HTML filename |
| `project_name` | No | `"comic-project"` | Project name for asset tracking |
| `issue_title` | No | from research | Issue title |
| `max_characters` | No | `5-6` | Max characters to design (4-5 main + 1-2 supporting) |
| `max_pages` | No | `5` | Max story pages per issue (plus cover + cast page) |
| `panels_per_page` | No | `"3-6"` | Panels per page range. Pages with 2 panels allowed for dramatic moments |
| `saga_issue` | No | -- | Saga issue number (2, 3, ...) for multi-issue stories |
| `previous_issue_id` | No | -- | Previous issue ID for saga continuity |

**Examples:**

```bash
# Default settings
context='{"session_file": "events.jsonl", "style": "manga"}'

# Epic saga with big cast
context='{"session_file": "events.jsonl", "style": "x-men", "max_characters": "8", "max_pages": "7"}'

# Cinematic with dramatic full-spread pages
context='{"session_file": "events.jsonl", "style": "watchmen", "panels_per_page": "2-4"}'

# Dense action manga
context='{"session_file": "events.jsonl", "style": "naruto", "panels_per_page": "4-6", "max_pages": "6"}'
```

## Pipeline

The recipe runs 8 steps across 2 stages with an approval gate between them:

**Stage 1 -- Research & Storyboard** (text-only, cheap):

1. **Init Project** -- Creates project and issue with generation metadata
2. **Research** -- Analyzes session via `stories:story-researcher`, stores as asset
3. **Style Curation** -- Loads or generates style guide, stores as asset
4. **Storyboard** -- Delegates to `stories:content-strategist` + `stories:case-study-writer`, produces panel sequence with characters, dialogue, camera angles, page breaks

> **Approval gate** -- Review storyboard before committing to image generation

**Stage 2 -- Art Generation** (image generation, expensive):

5. **Character Design** -- Generates reference sheets (parallel, max 2 concurrent)
6. **Panel Art** -- Generates panels with self-review loop (parallel, max 2 concurrent)
7. **Cover Art** -- Portrait ratio cover with AmpliVerse branding (concurrent with panels)
8. **Composition** -- Assembles final HTML with SVG speech bubbles, panel shapes, visual QA

## Output Format

Each comic is a **single self-contained HTML file**:

- All images base64-embedded (works offline, no external dependencies)
- Consistent 2:3 aspect ratio pages (comic book proportions)
- 100% page coverage -- panels fill edge-to-edge with 3px gutters
- Panel clip-path shapes for visual variety (diagonal, wedge, bleed, irregular, etc.)
- SVG speech/thought/caption bubbles overlaid on panels
- Keyboard, touch, and click navigation between pages
- Cover with full-bleed image, overlaid title, and AmpliVerse branding
- Cast page with character portraits, roles, and backstory narratives

Open in any browser. No server needed.

## Agent Reference

| Agent | Role |
|-------|------|
| `style-curator` | Defines visual style from predefined pack or custom description |
| `storyboard-writer` | Selects characters, creates dramatized panel sequence with backstories |
| `character-designer` | Generates character reference sheets for visual consistency |
| `panel-artist` | Generates panel images with vision-based self-review (max 3 attempts) |
| `cover-artist` | Generates cover with AmpliVerse branding and self-review |
| `strip-compositor` | Assembles multi-page HTML with panel shapes, speech bubbles, visual QA |

## Module Reference

| Module | Purpose |
|--------|---------|
| `tool-comic-assets` | Project/issue/character/style asset management with `comic://` URI protocol |
| `tool-comic-create` | High-level comic creation: image generation, storage, review, HTML assembly |
| `tool-comic-image-gen` | Image generation bridge (OpenAI gpt-image-1, Google Gemini Imagen) |

## Examples

See [`examples/`](examples/) for a generated Sin City noir comic with full
pipeline documentation. The README there includes the exact prompt that created it.

## Dependencies

- **amplifier-bundle-stories** -- Session analysis and narrative creation
- **amplifier-bundle-browser-tester** -- Visual QA during composition

Both are automatically included when the bundle is installed.

## Known Issues

- **[Issue #90](https://github.com/microsoft-amplifier/amplifier-support/issues/90)**: Bridge tool module required until Amplifier providers support image output natively
