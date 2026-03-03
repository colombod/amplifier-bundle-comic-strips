# Example Comics

Generated comic strips demonstrating the comic-strips bundle pipeline.
Each HTML file is self-contained — open directly in a browser.

## sin-city-comic.html

**Style:** Sin City (Frank Miller noir)
**Source:** comic-strip-bundle development sessions
**Recipe version:** session-to-comic v7.4.0
**Generated:** 2026-03-03

### What it is

A 10-panel comic strip generated from the actual Amplifier sessions that built
the comic-strips bundle itself. The story dramatizes the development journey —
agents debugging, designing, and iterating — rendered in Frank Miller's Sin City
noir aesthetic: stark black-and-white contrast, bold silhouettes, rain-soaked
cityscapes, and hardboiled first-person narration.

### The exact prompt that created it

From an Amplifier session with the `comic-strips` bundle active:

```
amplifier tool invoke recipes \
  operation=execute \
  recipe_path=amplifier-bundle-comic-strips/recipes/session-to-comic.yaml \
  context='{"session_file": "combined-sessions.jsonl", "style": "sin-city", "output_name": "sin-city-comic", "project_name": "sin-city-e2e"}'
```

Or conversationally in a session:

```
execute session-to-comic with session_file=combined-sessions.jsonl style=sin-city output_name=sin-city-comic project_name=sin-city-e2e
```

The recipe pauses at an approval gate after the storyboard is complete. Review
the character cast and narrative arc, then approve to proceed with image
generation.

### How it was created

The full pipeline ran autonomously through 8 steps:

```
Step 1: init-project
  Agent: style-curator
  Created project "sin-city-e2e" with generation metadata
  (session file, style, recipe version stored in issue manifest)

Step 2: research
  Agent: stories:story-researcher
  Analyzed a 123 MB session log (combined-sessions.jsonl)
  Extracted: agent activity, tool calls, narrative beats, key decisions
  Stored research as asset, passed only the URI downstream (~70 bytes)

Step 3: style-curation
  Agent: style-curator
  Loaded the sin-city.md style pack
  Stored style definition as versioned asset

Step 4: storyboard
  Agent: storyboard-writer
  Delegated to stories:content-strategist + stories:case-study-writer
  Produced structured JSON: 10 panels, 4 characters with backstories,
  scene descriptions, dialogue, camera angles, emotional beats,
  page breaks

  --- APPROVAL GATE ---
  Human reviewed storyboard before committing to image generation

Step 5: design-characters (parallel, max 2 concurrent)
  Agent: character-designer (foreach character)
  Generated reference sheets for: The Orchestrator, The Explorer,
  The Oracle, The Human
  Each stored as project-scoped asset with comic:// URI

Step 6: generate-panels (parallel, max 2 concurrent)
  Agent: panel-artist (foreach panel)
  Generated 10 panel images using gpt-image-1
  Each prompt enforced "no text in image" at code level
  Character reference images passed for visual consistency
  Cover generated concurrently by cover-artist

Step 7: generate-cover
  Agent: cover-artist
  Portrait ratio (1024x1536) — proper comic book proportions
  All major characters featured, no text baked into image

Step 8: composition
  Agent: strip-compositor
  Reviewed each panel's visual composition via vision API
  Built layout JSON with speech bubbles, captions, panel shapes
  Called assemble_comic to render final self-contained HTML
  Visual QA via browser-tester:visual-documenter
```

### What the output demonstrates

| Feature | Detail |
|---------|--------|
| 100% page coverage | Panels fill every page edge-to-edge, 3px gutter |
| Consistent page sizing | All pages use 2:3 aspect ratio |
| Panel shape variety | 70% non-rectangular: diagonal, irregular, wedge, bleed, rounded |
| Full-bleed cover | Portrait image fills entire cover page, title overlaid |
| Cinematic cast page | Characters with portrait, role, and backstory narrative |
| SVG speech bubbles | 28 overlays — speech, thought, captions, narration |
| Zero text in images | Code-level enforcement on every image generation prompt |
| AmpliVerse branding | Publisher badge on cover |
| Self-contained | Single HTML file, all images base64-embedded, works offline |

### Opening it

```bash
# macOS
open examples/sin-city-comic.html

# Linux
xdg-open examples/sin-city-comic.html

# or just drag the file into any browser
```

Use arrow keys, click the nav buttons, or tap the page dots to navigate.
