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

---

## comic-strips-bundle-creation-jjk.html

**Style:** Jujutsu Kaisen (Gege Akutami manga)
**Source:** comic-strip-bundle development sessions
**Recipe version:** session-to-comic v7.4.0
**Generated:** 2026-03-03

### What it is

A 19-panel, 3-page comic strip titled "Forging the Comic Engine" -- subtitled
"Five hours that tempered an engine without producing a blade." Generated from
the same Amplifier development sessions that built the comic-strips bundle, but
rendered in the Jujutsu Kaisen manga aesthetic: high-contrast ink work, dynamic
action poses, cursed-energy visual metaphors, and intense panel compositions.

The story follows The Orchestrator -- a relentless engineer coding through
midnight -- and three agents (The Self-Clone, The Explorer, The Session Analyst)
through a five-hour battle against session crashes, interference, and forge
failures. The Session Analyst's repeated defeats reveal the system's need for
resilience, culminating in the Orchestrator cloning themselves to push through.

### The exact prompt that created it

From an Amplifier session with the `comic-strips` bundle active:

```
execute session-to-comic with session_file=combined-sessions.jsonl style=jujutsu-kaisen output_name=comic-strips-bundle-creation-jjk project_name=jjk-e2e
```

### Characters

| Character | Role | Description |
|-----------|------|-------------|
| The Orchestrator | Protagonist | Relentless engineer commanding hundreds of operations, clones themselves when allies fall |
| The Self-Clone | Specialist | A focused echo with surgical precision and a perfect delegation record |
| The Explorer | Scout | Methodical mapper of uncharted territory, speaks in structured reports |
| The Session Analyst | Specialist | Forensic investigator struck down three times, revealing the need for resilience |

### What the output demonstrates

| Feature | Detail |
|---------|--------|
| 11 pages, 19 panels | Cover + character intro + 3 story pages |
| 4 characters | All AI agents rendered as JJK-style sorcerers |
| JJK manga aesthetic | High-contrast ink, dynamic poses, cursed-energy motifs |
| Non-rectangular panels | 5 clip-path panels for dynamic composition |
| 21 speech bubbles | Positioned dialogue overlays |
| Full-bleed cover | Portrait image with title overlaid |
| AmpliVerse branding | Publisher badge on cover |
| Compact file | 3.7 MB -- images already JPEG-compressed |
| Self-contained | Single HTML file, all images base64-embedded, works offline |

### Opening it

```bash
# macOS
open examples/comic-strips-bundle-creation-jjk.html

# Linux
xdg-open examples/comic-strips-bundle-creation-jjk.html

# or just drag the file into any browser
```

Use arrow keys, click the nav buttons, or tap the page dots to navigate.

---

## ghibli-context-intelligence-comic.html

**Style:** Studio Ghibli (Miyazaki watercolor)
**Source:** context-intelligence-second-pass project sessions
**Recipe version:** session-to-comic v7.5.0
**Generated:** 2026-03-04

### What it is

A 34-panel, 10-page comic strip generated from the Amplifier sessions that built
the context-intelligence bundle -- the CXDB-backed session recording and analysis
system for the Amplifier ecosystem. Rendered in Studio Ghibli's watercolor
illustration style: soft earthy palettes, hand-painted backgrounds with dappled
golden-hour light, gentle rounded character designs, and magical realism where
technical concepts become nature metaphors.

The story follows Diego (the lead developer) and a team of AI agents through a
gauntlet of production bugs -- silent connection failures, ghost contexts, and a
hidden socket leak -- culminating in a kintsugi-style repair and Brian's PR
review that made the code community-ready. Two human characters, seven total cast
members, and a narrative arc from quiet workshop morning to triumphant green test
wall.

### What makes this example special

This comic demonstrates **v7.5.0 features** not present in the sin-city example:

| Feature | Detail |
|---------|--------|
| **story_hints** | Rich narrative guidance passed through to storyboard-writer -- emphasis on multiple humans, difficulties, and community impact |
| **character_hints** | Ghibli-specific character direction -- nature spirits, expressive body language, watercolor aesthetics |
| **Style cohesion** | All 7 characters share Ghibli visual DNA (round faces, large expressive eyes, soft watercolor rendering) thanks to the new style cohesion directive |
| **All 28 style packs** | The `ghibli` style pack loaded from its authored `.md` file instead of falling through to custom generation |
| **Two human characters** | Diego (the builder) and Brian (the reviewer) -- demonstrating multi-human narrative |

### The exact prompt that created it

From an Amplifier session with the `comic-strips` bundle active:

```
execute session-to-comic with \
  session_file=~/.amplifier/projects/-home-dicolomb-context-intelligence-second-pass/sessions/59cb8e3f-48a2-422a-867d-f78a98b2a75b/events.jsonl \
  style=ghibli \
  output_name=ghibli-context-intelligence-comic \
  project_name=ghibli-context-intelligence \
  issue_title="The Quiet Revolution - Building Context Intelligence" \
  max_characters=7 \
  max_pages=10 \
  panels_per_page=3-6 \
  story_hints="This comic tells the story of building the context-intelligence bundle... emphasis on multiple humans providing feedback, the difficulties, and the final triumph for the community" \
  character_hints="Studio Ghibli character aesthetics are CRITICAL... Diego as a determined craftsperson, Brian as a thoughtful reviewer, AI agents as nature spirits in the Ghibli tradition"
```

(Full story_hints and character_hints were ~2000 words of creative direction --
see the session log for the complete text.)

### How it was created

The full pipeline ran autonomously through 8 steps:

```
Step 1: init-project
  Agent: style-curator
  Created project "ghibli-context-intelligence" with generation metadata

Step 2: research
  Agent: stories:story-researcher
  Analyzed 125 MB session log from the context-intelligence-second-pass project
  Extracted: agent activity, tool calls, narrative beats, key decisions
  Stored research as asset, passed only the URI downstream (~70 bytes)

Step 3: style-curation
  Agent: style-curator
  Loaded ghibli.md style pack (NEW: all 28 packs now have explicit mappings)
  Produced style guide with Character Rendering cohesion section
  Stored style definition as versioned asset

Step 4: storyboard
  Agent: storyboard-writer
  Applied story_hints to both Phase 1 (narrative arc) and Phase 2 (panel layout)
  Delegated to stories:content-strategist + stories:case-study-writer
  Produced structured JSON: 34 panels, 7 characters (4 main + 3 supporting),
  10 story pages, scene descriptions, dialogue, camera angles, emotional beats

  --- APPROVAL GATE ---
  Human reviewed storyboard before committing to image generation

Step 5: design-characters (parallel, max 2 concurrent)
  Agent: character-designer (foreach character)
  Applied character_hints to all 7 character designs
  NEW: Style cohesion directive included in every prompt --
  all characters share Ghibli visual DNA from Character Rendering section
  Generated reference sheets for: Diego, The Explorer, The Builder,
  The Critic, Brian, The Dreamer, The Keeper

Step 6: generate-panels (parallel, max 2 concurrent)
  Agent: panel-artist (foreach panel)
  Generated 34 panel images using gpt-image-1
  Character reference images passed for visual consistency
  Cover generated concurrently by cover-artist

Step 7: generate-cover
  Agent: cover-artist
  Portrait ratio (1024x1536), all 4 main characters featured

Step 8: composition
  Agent: strip-compositor
  12 pages total (cover + character intro + 10 story pages)
  42 images embedded (34 panels + 1 cover + 7 character refs)
  82% non-rectangular panel shapes
  Visual QA score: 7.5/10
```

### What the output demonstrates

| Feature | Detail |
|---------|--------|
| 12 pages, 34 panels | Full 10-page story plus cover and character intro |
| 7 characters | 2 humans (Diego, Brian) + 5 AI agents as Ghibli-style characters |
| Ghibli watercolor aesthetic | Soft palettes, golden-hour light, nature metaphors |
| Style cohesion | All characters share round faces, large eyes, watercolor rendering |
| Story hints applied | Narrative emphasizes human feedback, difficulties, community triumph |
| Character hints applied | Diego as craftsperson, Brian as reviewer, agents as nature spirits |
| Nature metaphors | Errors as storms, tests as blooming gardens, fixes as kintsugi |
| Full-bleed cover | Portrait image with all main characters, title overlaid |
| Cast page | 7 characters with portraits, roles, and narrative backstories |
| SVG speech bubbles | Positioned via vision-informed composition analysis |
| Zero text in images | Code-level enforcement on every image generation prompt |
| AmpliVerse branding | Publisher badge on cover |
| Self-contained | Single HTML file (~16 MB compressed), all images base64-embedded, works offline |

### Opening it

```bash
# macOS
open examples/ghibli-context-intelligence-comic.html

# Linux
xdg-open examples/ghibli-context-intelligence-comic.html

# or just drag the file into any browser
```

Use arrow keys, click the nav buttons, or tap the page dots to navigate.
