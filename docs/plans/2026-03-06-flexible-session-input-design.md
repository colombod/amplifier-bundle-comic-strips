# Flexible Session Input Design

## Goal

Replace the rigid `session_file` (single events.jsonl path) input in the `session-to-comic` recipe with a flexible `source` input that accepts project names, session IDs, file paths, descriptive phrases, or any combination — letting the `stories:story-researcher` agent discover and gather the relevant session data using its native tools.

## Background

The current `session-to-comic` recipe requires a `session_file` context variable pointing to a specific `events.jsonl` file path. This is limiting in several ways:

- Users must know the exact filesystem path to a session file before invoking the recipe.
- It only supports a single session — no way to synthesize a comic from multiple sessions or an entire project's history.
- It couples the recipe interface to Amplifier's internal storage layout, which is fragile.

Other recipes in the stories bundle (`blog-post-generator`, `weekly-digest`) already solve this differently: they give the researcher a human-friendly handle (a feature name, a date range) and trust it to discover data through git/gh CLI, grep, and delegation — not through hardcoded path knowledge.

## Approach

**Approach A — "Artistic and creative inclined":** Add a new discovery step using `stories:story-researcher` as the discovery agent. The researcher already has bash (git/gh CLI), grep, read_file, and task (delegation to `foundation:explorer`). It can explore creatively and filter sessions by narrative importance, not just recency or size. This aligns with how the stories bundle's own recipes work and avoids coupling to Amplifier internals.

## Architecture

The change introduces a new pipeline step (`discover-sessions`) between the existing `init-project` and `research` steps. This step acts as a resolution layer — it translates a human-friendly `source` string into consolidated session data stored as a comic asset. The downstream `research` step then consumes that asset instead of reading a raw file path.

```
User input (source)
       │
       ▼
┌──────────────┐
│ Init Project │  Step 0 — style-curator
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ Discover Sessions│  Step 0a — stories:story-researcher  ◄── NEW
└──────┬───────────┘
       │  {{session_data}} URI
       ▼
┌──────────────┐
│   Research   │  Step 1 — stories:story-researcher
└──────┬───────┘
       │
       ▼
   (rest of pipeline unchanged)
```

## Components

### New Input Contract

The `source` context variable replaces `session_file` as the primary input. It accepts any of these forms — the researcher does not need to be told which form it received; it inspects the string and figures it out:

| Input Form | Example |
|---|---|
| Project name (human-friendly) | `comic-strip-bundle` |
| Directory path | `~/.amplifier/projects/-home-dicolomb-comic-strip-bundle/` |
| Single session file | `~/.amplifier/sessions/abc123/events.jsonl` |
| Session ID | `6c586a77-de22-48ed-9dd3-5ba0b957af30` |
| Multiple session IDs (comma-separated) | `abc123,def456,ghi789` |
| Multiple paths (comma-separated) | `path1.jsonl,path2.jsonl` |
| Descriptive phrase | `the context-intelligence project` |

### New Recipe Step — "discover-sessions" (Step 0a)

**Position:** Between `init-project` (Step 0) and `research` (Step 1).

**Agent:** `stories:story-researcher` — has bash (git/gh CLI), grep, read_file, and task (delegation to `foundation:explorer`).

**What the step does:**

1. Receives `{{source}}` — the flexible input from the user.
2. Resolves it to concrete session data using its native tools — `git log`, `gh` CLI, `grep`, `find`, delegation to `foundation:explorer`. The prompt does **not** hardcode Amplifier internal paths.
3. Reads and consolidates the key data from discovered sessions (session metadata, agent activity, tool calls, user prompts, outcomes).
4. Stores the consolidated research material as a comic asset via `comic_asset(action='store', ...)`.
5. Returns the asset URI as `{{session_data}}`.

**What it does NOT do:** Comic-specific extraction (characters, panel moments, narrative arcs). That stays in the existing research step. The discover step is purely "find the data and consolidate it."

**Step prompt guidance:**

> You are given a source describing what to research: `{{source}}`
>
> This could be a project name, a session ID, file paths, or a descriptive phrase. Discover and gather the relevant Amplifier session data — agent activity, tool usage, key moments, outcomes, and metrics.
>
> Use your tools to find the data. If you need deeper exploration, delegate to foundation:explorer. Synthesize across multiple sessions if the source spans more than one.
>
> Store the consolidated research material using comic_asset and return the URI.

This follows the pattern established by the stories bundle's own recipes (`blog-post-generator`, `weekly-digest`) which give the researcher a human-friendly handle and trust it to discover data through its native tools — not through hardcoded path knowledge.

### Updated Context Variables and Backward Compatibility

New context variable `source` replaces `session_file` as the primary input:

```yaml
context:
  source: ""              # Required: project name, session ID(s), file path(s), or descriptive phrase
  session_file: ""        # Deprecated: backward-compatible alias for source (single file path)
  style: "superhero"
  # ... rest unchanged
```

**Resolution logic:** The `discover-sessions` step receives both `{{source}}` and `{{session_file}}`. If `source` is provided, use it. If only `session_file` is provided, use that instead. This means all existing invocations that pass `session_file=` continue to work unchanged.

**Invocation examples:**

```bash
# Old way (still works):
execute session-to-comic with session_file=./events.jsonl style=naruto

# New ways:
execute session-to-comic with source=comic-strip-bundle style=naruto
execute session-to-comic with source=abc123,def456 style=naruto
execute session-to-comic with source="the context-intelligence project" style=ghibli
```

### Updated Research Step

The existing research step changes its prompt from:

```
Analyze the Amplifier session at: {{session_file}}
```

to:

```
Analyze the session data at: {{session_data}}
```

Where `{{session_data}}` is the URI returned by the discover step. The research step loads the consolidated asset via `comic_asset(action='get')` and extracts comic-specific structures from there. It no longer touches `session_file` or `source` directly.

## Data Flow

```
User provides: source="comic-strip-bundle" style=naruto

Step 0  (init-project):     Creates project/issue in asset manager
                             │
Step 0a (discover-sessions): Receives {{source}} + {{session_file}}
                             Resolves to concrete session files via git/gh/grep/explorer
                             Consolidates data → comic_asset(action='store')
                             Returns {{session_data}} URI
                             │
Step 1  (research):          Loads {{session_data}} via comic_asset(action='get')
                             Extracts characters, panel moments, narrative arcs
                             Stores comic-specific research as assets
                             │
Steps 2-7:                   Pipeline continues unchanged
```

## Updated Pipeline Flow

The recipe goes from 9 steps to 10. The new step slots between init-project and research:

**Stage 1 — Research & Storyboard (text-only, low cost):**

| Step | Name | Agent |
|---|---|---|
| 0 | Init Project | style-curator |
| 0a | Discover Sessions **NEW** | stories:story-researcher |
| 1 | Research | stories:story-researcher |
| 2 | Style Curation | style-curator |
| 3 | Storyboard | storyboard-writer |
| 3a | Validate Storyboard | style-curator |
| 3b | Update Issue Title | style-curator |
| — | **APPROVAL GATE** | — |

**Stage 2 — Art Generation (image generation, high cost):**

| Step | Name | Agent |
|---|---|---|
| 4 | Character Design | character-designer |
| 5 | Panel Art | panel-artist |
| 6 | Cover Art | cover-artist |
| 7 | Composition | strip-compositor |

**Dot file changes (`pipeline-flow.dot`):**
- Add `discover_sessions` node between `init` and `research`, numbered "0a", with agent `stories:story-researcher` and annotation "resolves {{source}} to session data".
- New edge: `init -> discover_sessions -> research`.
- Add a data flow annotation showing `{{source}}` entering discover_sessions and `{{session_data}}` (URI) flowing to research.
- The rest of the pipeline stays the same.

**`comic-instructions.md` changes:**
- The Cross-Agent Data Flow section gets a new stage 0 at the beginning describing the discovery pattern — the researcher receives a human-friendly source handle and uses git/gh CLI, grep, and delegation to `foundation:explorer` to locate and consolidate session data before the comic-specific extraction begins.

## Error Handling

- **Source is empty and session_file is empty:** The discover step should fail immediately with a clear error message indicating that one of the two inputs is required.
- **Source cannot be resolved:** If the researcher cannot find any sessions matching the source string, it should fail with a descriptive error explaining what it tried and what it couldn't find, rather than producing an empty asset.
- **Partial resolution:** If some session IDs in a comma-separated list are found but others are not, the researcher should consolidate what it found and note the missing sessions in the asset metadata.

## Testing Strategy

- **Backward compatibility:** Verify that existing invocations using `session_file=path/to/events.jsonl` continue to work unchanged through the new pipeline.
- **Single project name:** Test with `source=comic-strip-bundle` — verify the researcher discovers and consolidates the correct sessions.
- **Multiple session IDs:** Test with `source=id1,id2,id3` — verify all sessions are found and consolidated.
- **Descriptive phrase:** Test with `source="the context-intelligence project"` — verify creative resolution works.
- **File path passthrough:** Test with `source=path/to/events.jsonl` — verify direct file paths still work through the new step.
- **Pipeline integration:** Run a full `session-to-comic` execution with the new `source` input and verify the research step correctly consumes the `{{session_data}}` URI from the discover step.

## Open Questions

1. **Timeout adjustment:** Should there be a timeout adjustment for the discover step? If the researcher is scanning a large project with hundreds of sessions, it may need more time than the current research step's 900s timeout.
2. **Retry logic:** Should the discover step have retry logic? If the researcher can't find sessions for a project name, should it retry with different search strategies or fail immediately with a helpful error?
3. **Version bump:** Should the recipe version bump to v7.7.0 or v8.0.0? This is an additive feature (new step, new context variable, backward compatible) so v7.7.0 seems appropriate.

## Files That Will Change

| File | Change |
|---|---|
| `recipes/session-to-comic.yaml` | New context variable, new step, research step prompt update, version bump, changelog |
| `docs/diagrams/pipeline-flow.dot` | New `discover_sessions` node and edges |
| `context/comic-instructions.md` | Updated Cross-Agent Data Flow section |
| `examples/README.md` | Updated invocation examples if any reference `session_file` |
