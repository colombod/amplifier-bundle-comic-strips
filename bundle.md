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

Transform Amplifier sessions and project stories into visually compelling comic strips using AI-powered visual storytelling.

## What This Bundle Provides

### Visual Styles

Six distinct visual styles for comic generation:

- **Manga** - Japanese-inspired sequential art with dynamic panel layouts and expressive characters
- **Superhero** - Bold, action-packed American comic book style with dramatic poses and vivid colors
- **Indie** - Hand-drawn aesthetic with unique artistic voice and experimental layouts
- **Newspaper** - Classic daily strip format with clean lines and accessible humor
- **Ligne Claire** - European clear-line style inspired by Herge and Franco-Belgian comics
- **Retro Americana** - Vintage mid-century American illustration with halftone dots and warm palettes

### Specialist Agents

Five dedicated agents handle different aspects of comic creation:

- **style-curator** - Selects and configures the visual style based on story content and tone
- **storyboard-writer** - Breaks narratives into panel sequences with pacing and dialogue
- **panel-artist** - Generates individual panel artwork using image generation APIs
- **cover-artist** - Creates eye-catching cover pages and title cards for comic series
- **strip-compositor** - Assembles panels, speech bubbles, and captions into final comic layouts

### Automated Workflows

- **session-to-comic** - End-to-end recipe that transforms an Amplifier session into a complete comic strip

## Quick Start

Create comics from your Amplifier sessions:

> "Turn my last debugging session into a manga-style comic strip"

> "Create a superhero comic showing how we built the authentication feature"

> "Generate a newspaper strip summarizing today's code review"

@comic-strips:context/comic-instructions.md
