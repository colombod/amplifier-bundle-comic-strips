# amplifier-bundle-comic-strips

Transform Amplifier sessions into AI-generated multi-page comic strips with consistent characters, dramatic storytelling, and AmpliVerse publisher branding.

This is a thin Amplifier bundle that orchestrates six specialized agents and a bridge tool module to turn any Amplifier session transcript into a self-contained HTML comic book.

## Prerequisites

- [Amplifier CLI](https://github.com/microsoft/amplifier) installed
- At least one image-capable provider configured:
  - **OpenAI** with `gpt-image-1` (recommended)
  - **Google** with Gemini Imagen
- Provider API keys configured in `~/.amplifier/settings.yaml`

## Installation

```bash
amplifier bundle add git+https://github.com/colombod/amplifier-bundle-comic-strips@main
amplifier bundle use comic-strips
```

## Quick Start

Generate a comic from an Amplifier session:

```bash
# Using the session-to-comic recipe
amplifier run "execute session-to-comic with session_file=<SESSION_ID> style=superhero output_name=my-comic"

# Or interactively
amplifier run "Turn my last session into a manga-style comic strip"
```

## Style Gallery

Six predefined visual styles:

| Style | Description |
|-------|-------------|
| **manga** | Japanese-inspired B&W ink wash, speed lines, expressive characters, right-to-left panel flow |
| **superhero** | Bold saturated colors, dynamic poses, dramatic perspective, muscular proportions, cel-shading |
| **indie** | Gritty painterly aesthetic, dark atmosphere, irregular panel borders, muted palette |
| **newspaper** | Clean simple line art, 3-4 panel horizontal strip format, punchline pacing, daily-strip feel |
| **ligne-claire** | European clear-line style (Tintin/Herge), flat bright colors, detailed backgrounds, uniform line weight |
| **retro-americana** | Vintage halftone dots, warm palette, cheerful proportions, 1950s Americana aesthetic |

Custom styles are also supported -- describe the aesthetic and the style-curator agent will interpret it into a full style guide.

## Agent Reference

| Agent | Role | Model Tier |
|-------|------|------------|
| `style-curator` | Defines visual style from predefined pack or custom description | Strong (Sonnet, GPT-5) |
| `storyboard-writer` | Selects characters from session transcript, creates dramatized panel sequence | Strong (Sonnet, GPT-5) |
| `character-designer` | Generates character reference sheets for visual consistency (3-6 selected characters) | Strong (Sonnet, GPT-5) |
| `panel-artist` | Generates panel images with vision-based self-review quality loop (max 3 attempts) | Strong + Tool (Sonnet, GPT-5) |
| `cover-artist` | Generates cover with AmpliVerse branding and self-review (max 3 attempts) | Strong + Tool (Sonnet, GPT-5) |
| `strip-compositor` | Assembles multi-page HTML with visual QA, assembly review, and cleanup | Budget (Haiku, GPT-5 Mini) |

## Recipe Reference

### session-to-comic

End-to-end pipeline that transforms a session into a comic:

1. **Research** -- Extracts structured data from session (via `stories:story-researcher`)
2. **Style Curation** -- Defines visual language from style name or custom description
3. **Storyboard** -- Selects characters, creates dramatized panel sequence with page breaks
4. **Character Design** -- Generates reference sheets for 3-6 selected characters
5. **Panel Art** -- Generates panels with vision-based self-review (max 3 attempts each)
6. **Cover Art** -- Generates cover with AmpliVerse branding (max 3 attempts)
7. **Composition** -- Assembles HTML, runs visual QA (max 2 iterations), cleans up intermediate files

#### Context Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `session_file` | Yes | -- | Path to events.jsonl session file or session ID |
| `style` | No | `"superhero"` | Style name (manga, superhero, indie, newspaper, ligne-claire, retro-americana) or custom description |
| `output_name` | No | `comic-{timestamp}` | Custom output filename |

## Bridge Tool Module

`modules/tool-comic-image-gen/` provides the `generate_image` tool as a temporary bridge. This exists because Amplifier providers don't yet support image output through `complete()` (tracked in [Issue #90](https://github.com/microsoft-amplifier/amplifier-support/issues/90)).

The bridge tool directly calls provider APIs (OpenAI `gpt-image-1` or Google Gemini) to generate images, bypassing the normal Amplifier provider pipeline. Once providers support native image output, this module will be removed.

## Dependencies

- **amplifier-bundle-stories** -- Data gathering (story-researcher and other analysis agents)
- **amplifier-bundle-browser-tester** -- Visual QA (visual-documenter agent for assembly review)

Both are automatically included when the bundle is installed.

## AmpliVerse Branding

All generated comics include AmpliVerse publisher branding on the cover page. The logo is the actual Amplifier GitHub avatar image (`https://github.com/microsoft-amplifier.png`) embedded as a base64 `<img>` tag -- not CSS text or a colored badge.

## Known Issues

- **[Issue #90](https://github.com/microsoft-amplifier/amplifier-support/issues/90)**: Bridge tool module required until Amplifier providers support image output natively
