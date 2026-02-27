---
name: comic-storytelling
description: "Use when breaking a technical session into comic panels: selecting characters from transcripts, transforming technical dialogue into drama, choosing narrative pacing, mapping bundles to visual affiliations, and compressing complex sessions into visual stories."
version: "2.0.0"
---

# Comic Storytelling for Technical Narratives

## Character Selection from Session Transcript

Every session transcript contains agents, tools, and users. Not all of them belong in the comic. Follow this 5-step selection process:

1. **Rank agents by activity**: Count tool calls, delegations, and lines of dialogue per agent. Rank highest-first — the most active agents are your protagonist candidates.
2. **Identify key moments**: Find the turning points — breakthroughs, failures, pivots, discoveries. Which agents were involved in those moments?
3. **Select 3-4 main characters**: Pick the agents who drove the story forward. These get speech bubbles, expressions, and character arcs.
4. **Select 1-2 supporting characters**: Pick agents who appeared at critical moments but didn't drive the plot. They get cameos or single-panel appearances.
5. **Cut everyone else**: If an agent only ran background tasks or appeared once with no impact, they don't get drawn. Ruthlessly cut everyone else to keep the cast tight.

## Bundle-as-Affiliation Mapping

Each agent's parent bundle determines their visual team affiliation. Use the comic style to express team identity:

| Style | Team Expression | Uniform Motif | Badge/Emblem | Color Palette |
|-------|----------------|---------------|--------------|---------------|
| Superhero | Agents from the same bundle wear matching suits with unique accents | Capes, masks, chest emblems | Bundle logo as chest symbol | Bold primaries per bundle |
| Manga | Bundle members share a school, guild, or faction | Matching uniforms with personal flair | Faction crest on sleeve | Warm/cool split by team |
| Newspaper | Same-department colleagues in a newsroom | Matching press badges, desk proximity | Department nameplate | Grayscale with accent per desk |
| Indie | Loose collective, shared aesthetic but individual expression | Coordinated color palettes, shared accessories | Hand-drawn pins or patches | Muted earth tones, per-group hue |
| Ligne Claire | Agency or organization members with clean uniform lines | Matching outfits with thin black outlines | Minimalist logo badge | Flat colors, one accent per org |
| Retro Americana | Team members in a classic adventure squad | Matching jackets or hats with team insignia | Retro shield or star badge | Saturated vintage palette per team |

## Antagonists Are NOT Characters

Session obstacles are **environmental threats**, NOT characters with portraits, profiles, or dialogue. Do NOT create villain characters from errors or failures.

Instead, depict obstacles as:

- **Walls** — permission denied, auth failures, blocked APIs
- **Barriers** — incompatible versions, missing dependencies, type mismatches
- **Storms** — rate limit floods, timeout cascades, network instability
- **Explosions** — crash dumps, stack overflows, out-of-memory kills

Obstacles are scenery that characters react to. They have no speech bubbles, no motivations, no backstory. They are forces of nature the heroes must overcome.

## Transcript-to-Drama Transformation

Technical transcripts are full of precise data that makes terrible dialogue. Transform facts into drama:

### Transformation Rules

| Technical Fact | BAD (Literal Dialogue) | GOOD (Dramatic Dialogue) |
|---------------|------------------------|--------------------------|
| Session ID / UUID | "Running session UUID abc-123-def-456..." | "Another mission begins!" |
| File path | "Editing src/auth/middleware/validate.ts..." | "The authentication gates need reinforcing!" |
| Test results | "47 tests passed, 3 failed in test_auth.py" | "Almost there... but three guards still won't let us through!" |
| Token usage | "Used 150,000 tokens across 12 turns" | "We're burning through energy fast — need to wrap this up!" |
| Rate limits | "429 Too Many Requests, retrying in 30s..." | "The floodgates slammed shut! We need to wait for the storm to pass!" |
| Delegation | "Delegating to foundation:bug-hunter with context_depth=recent" | "Calling in the specialist — they'll know what to track!" |
| Config change | "Setting timeout=30000 in config.yaml" | "Buying ourselves more time..." |
| Git commit | "Committed abc1234: feat: add retry logic" | "Another victory sealed — this one's in the books!" |

### Where Facts Belong

Not all facts disappear — they just move to the right place:

- **Caption boxes** are for facts: timestamps, file names, session context, technical narration. Captions are the narrator's voice and carry factual exposition. Example: *"In the auth module, 3:42 PM..."*
- **Dialogue bubbles** are for emotion and character: reactions, decisions, exclamations. Dialogue expresses what characters feel and choose, never raw data. Example: *"This is the one — I can feel it!"*

Rule: If it came from a log line, it goes in a caption box. If it expresses a character's reaction, it goes in dialogue.

### Visual Metaphors for Technical Events

| Technical Event | Visual Metaphor |
|----------------|----------------|
| Successful deployment | Rocket launch, bridge completion, door opening to light |
| Test failure | Crack in armor, shield breaking, bridge collapse |
| Rate limiting | Floodwall rising, storm barrier, traffic jam |
| Debugging | Magnifying glass, following footprints, detective investigation |
| Refactoring | Rebuilding a structure, forging new armor, renovation montage |
| Delegation to agent | Summoning a specialist, calling reinforcements, signal flare |
| Cache hit | Finding treasure in a chest, shortcut through a mountain |
| Timeout | Hourglass shattering, clock melting, sand running out |

## Compressing Technical Stories

Technical sessions often span hours with dozens of steps. Compress to 4-8 panels using these rules (see Panel Count Guidelines below for exact ranges by complexity):

1. **Identify the arc**: Every story has Challenge -> Approach -> Resolution. Find these three beats.
2. **Pick the peaks**: Select 2-3 key moments of highest drama (breakthroughs, failures, discoveries)
3. **Cut the routine**: Skip file edits, routine commands, incremental progress. Keep only turning points.
4. **Personify the agents**: Agents and tools become characters. "The Bug Hunter tracked down the issue" is more visual than "pytest found a failing test."

## Panel Count Guidelines

| Story Complexity | Panel Count | Structure |
|-----------------|-------------|-----------|
| Simple (one problem, one fix) | 3-4 | Setup, Action, Resolution |
| Medium (problem + iteration) | 5-6 | Setup, First Try, Failure, New Approach, Success, Celebration |
| Complex (multi-agent, long session) | 7-8 | Establishing, Challenge, Team Assembly, Multiple Attempts, Breakthrough, Resolution, Impact, Epilogue |
| Epic (major feature journey) | 10-12 | Full chapter with multiple scenes and transitions |

## Dialogue vs Caption vs Silent

| Panel Type | When to Use | Example |
|-----------|------------|---------|
| **Dialogue** (speech bubbles) | Character interaction, explanation, humor | Agent says "I found the bug in line 42!" |
| **Caption** (narrator box) | Context, time jumps, technical explanation | "Meanwhile, the test suite was running..." |
| **Silent** (no text) | Emotional beats, dramatic pauses, visual punchlines | Agent staring at a wall of error messages |
| **Sound effect** | Action moments, emphasis | "DEPLOY!" "CRASH!" "SUCCESS!" |

## Pacing Rules

- **Opening panel**: Wide establishing shot. Set the scene. Caption for context.
- **Rising action**: Smaller panels, faster pace. Dialogue-heavy.
- **Climax**: Largest panel on the page. Maximum visual impact.
- **Resolution**: Return to medium panels. Calmer pace.
- **Final panel**: Punchline, reflection, or cliffhanger. Often the most memorable.

## Story Archetypes for Technical Comics

1. **The Quest**: User has a goal -> Agents assemble -> Overcome obstacles -> Achieve victory
2. **The Mystery**: Bug appears -> Investigation -> Red herrings -> Eureka moment -> Fix
3. **The Transformation**: Old system -> Pain points -> New approach -> Before/After reveal
4. **The Race**: Deadline pressure -> Rapid iteration -> Close calls -> Just-in-time finish
