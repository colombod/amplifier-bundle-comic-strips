# Composable Pipeline Architecture Design

## Goal

Transform the monolithic `session-to-comic` pipeline into a composable family of recipes where each stage can run independently from stored assets, with version-aware change detection and explicit intent-driven regeneration.

## Background

The current pipeline has three architectural problems that block practical use:

1. **Character recreation** — every run creates new character versions (v=6, v=7, v=8) instead of reusing existing characters for the same style. This causes visual inconsistency across runs and wastes generation calls.

2. **No stage isolation** — if research and storyboard are already done, you can't just redo characters or panels. Everything runs from scratch, even when only one stage needs work.

3. **No persistence/resumability from assets** — research, storyboard, characters, and style are all stored as `comic://` assets, but no recipe reads them back to pick up from where you left off. The asset store is write-only in practice.

These problems compound: a failed panel generation means re-running the entire pipeline, which recreates characters (breaking visual consistency), which produces different results each time.

## Approach: Explicit Intent + Version Awareness + `built_from` Metadata

The system uses **explicit intent** (the user says what to redo) combined with **version-aware metadata** (each asset tracks what it was built from) to decide what to regenerate and what to reuse.

This avoids the complexity of content-hashing while giving precise staleness detection. The user stays in control — the system warns about stale assets but doesn't silently regenerate.

## Architecture

### The Composable Recipe Family

The monolithic `session-to-comic.yaml` is decomposed into independently runnable recipes that share the asset store as their persistence layer:

```
┌─────────────────────────────────────────────────────┐
│              session-to-comic.yaml                   │
│           (thin orchestrator — calls ↓)              │
└──────┬──────────────┬───────────────┬───────────────┘
       │              │               │
       ▼              ▼               ▼
 saga-plan.yaml  design-characters  issue-art.yaml
                    .yaml           (foreach issue)
                                         │
                                         ▼
                                   issue-compose.yaml
                                   (composition only)
```

Each recipe reads its inputs from the **asset store** (`comic://` URIs), not from recipe context variables. This is the fundamental shift: from a context-passing pipeline to an asset-store-driven pipeline.

| Recipe | Inputs | Outputs | Standalone? |
|--------|--------|---------|-------------|
| `saga-plan.yaml` | `source`, `style`, `project_id` (optional) | Research, style guide, storyboard, issues | Yes |
| `design-characters.yaml` | `project_id` | Character reference sheets + per-issue variants | Yes |
| `issue-art.yaml` | `project_id`, `issue_id` | Panels, cover, final HTML for one issue | Yes |
| `issue-compose.yaml` | `project_id`, `issue_id` | Re-composed HTML (no image generation) | Yes |
| `issue-retry.yaml` | `project_id`, `issue_id` | Re-generated art for one failed issue | Yes |
| `session-to-comic.yaml` | `source`, `style` | Full saga end-to-end | Orchestrates all above |

### Change Detection via `built_from` Metadata

Every generated asset stores metadata recording exactly what it was built from:

```json
{
  "version": 1,
  "built_from": {
    "storyboard": "comic://project/issues/issue-001/storyboards/storyboard?v=2",
    "character_uris": {
      "the-architect": "comic://project/characters/the-architect?v=3",
      "the-implementer": "comic://project/characters/the-implementer?v=5"
    },
    "style": "comic://project/styles/transformers?v=1"
  }
}
```

This enables answering questions at any time:

- "What character versions were used to build this panel?" → `built_from.character_uris`
- "Is this panel stale after a character redesign?" → compare `built_from` version with latest
- "Which panels need regeneration?" → find panels where `built_from.storyboard` version < current storyboard version

### Three Safety Behaviors

Each composable recipe applies three rules when deciding whether to generate or reuse:

1. **Reuse explicitly** — the asset exists AND its `built_from` versions match the current upstream versions. Skip generation entirely.

2. **Warn about staleness** — the asset exists BUT its `built_from` references an older upstream version than what's current. The recipe warns the user but does not regenerate unless asked.

3. **Regenerate explicitly** — the user passed `force=true`, or there is no existing asset to reuse. Generate from scratch.

## Components

### `saga-plan.yaml` — Stage 1 as Standalone Recipe

Encompasses discover, research, style curation, storyboard creation, validation, and issue creation. This is the current Stage 1 extracted into its own recipe.

**Reuse behavior:** If a storyboard already exists for the project, skip (unless `force=true`). Always creates issues if they're missing.

**Inputs:** `source` (session material), `style` (art style), `project_id` (optional — auto-generated if not provided).

**Outputs stored:** Research asset, style guide, storyboard (per-issue), issues created in the project.

### `design-characters.yaml` — Stage 2 as Standalone Recipe

Reads the character roster from the stored storyboard and generates reference sheets. The critical difference from the current implementation: **character reuse is the default behavior**.

**Character reuse logic:**

```
For each character in storyboard.character_roster[]:

  1. Check: does comic://project/characters/{slug} exist?
     → If NO: generate from scratch (new character)

  2. Check: does the existing character have a version in the current style?
     → If NO: generate a new style variant

  3. Check: does the roster entry have needs_redesign=true?
     → If YES: generate a new variant linked to existing
     → If NO: reuse the existing URI (skip generation)

  4. Check: does per_issue have entries with needs_new_variant=true?
     → For each: generate a variant for that issue only
```

This logic runs once per character in the roster and produces the minimum number of image generation calls needed.

**Inputs:** `project_id` (reads storyboard from assets).

**Outputs stored:** Character reference sheets with `built_from` metadata linking to storyboard version and style version.

### `issue-art.yaml` — Per-Issue Art Generation

Generates panels, cover, and final HTML for a single issue. Reads the storyboard and character URIs from the asset store.

**Inputs:** `project_id`, `issue_id`.

**Outputs stored:** Panel images, cover image, assembled HTML — each with `built_from` metadata.

### `issue-compose.yaml` — Composition-Only Recipe (New)

Runs ONLY the composition/assembly step — no panel or cover image generation. Reads existing panel and cover URIs from the asset store and re-runs `assemble_comic`.

This is useful when you want to change dialogue, captions, layout, or text overlays without regenerating any images.

**Inputs:** `project_id`, `issue_id`.

**Outputs stored:** New HTML assembly with `built_from` referencing existing panel and cover versions.

### `issue-retry.yaml` — Surgical Issue Retry

Same as `issue-art` but designed for recovering from partial failures. Reads existing storyboard, characters, and style from assets and regenerates only the panels/cover/HTML for one issue.

**Inputs:** `project_id`, `issue_id`.

### `session-to-comic.yaml` — Thin Orchestrator

Becomes a thin wrapper that calls the composable recipes in sequence. Each sub-recipe is self-sufficient. If any sub-recipe fails, you can re-run just that recipe independently.

```
session-to-comic.yaml
  → saga-plan.yaml       (discover, research, storyboard)
  → design-characters.yaml  (character reference sheets)
  → issue-art.yaml          (foreach issue: panels, cover, HTML)
```

## Data Flow

### Asset Store as the Persistence Layer

The `comic://` asset store is the single source of truth between stages. Each recipe reads inputs from the store and writes outputs back to it:

```
                    ┌──────────────────────┐
                    │   comic:// Asset     │
                    │       Store          │
                    │                      │
                    │  research            │
  saga-plan ───────▶│  style guide         │
                    │  storyboard (v=N)    │
                    │  issues              │
                    │                      │
  design-chars ◀───│  storyboard ─────────▶│  characters (v=M)  │
                    │                      │  built_from:       │
                    │                      │    storyboard?v=N  │
                    │                      │    style?v=K       │
                    │                      │
  issue-art ◀──────│  storyboard ─────────▶│  panels (v=P)     │
              ◀────│  characters           │  cover (v=Q)      │
                    │                      │  built_from:       │
                    │                      │    storyboard?v=N  │
                    │                      │    chars?v=M       │
                    │                      │
  issue-compose ◀──│  panels ─────────────▶│  final HTML (v=R) │
               ◀───│  cover                │  built_from:       │
               ◀───│  storyboard           │    panels?v=P     │
                    │                      │    cover?v=Q       │
                    └──────────────────────┘
```

### Version Propagation

When an upstream asset is regenerated (e.g., a character redesign bumps `the-architect` from v=3 to v=4), downstream assets become stale:

```
the-architect v=3 → v=4 (redesigned)
  ↓ stale
panel_01 built_from: the-architect?v=3  ← stale
panel_03 built_from: the-architect?v=3  ← stale
panel_02 built_from: the-implementer?v=5  ← still fresh
  ↓ stale
final HTML built_from: panel_01?v=1  ← stale (transitive)
```

The system detects this by comparing `built_from` URIs against the latest version in the store. It does NOT automatically regenerate — it warns and waits for explicit intent.

## Composable Workflows

### Full Fresh Run

```
session-to-comic with source=comic-strip-bundle style=transformers
  → saga-plan (creates project, research, storyboard, issues)
  → design-characters (creates characters from roster)
  → issue-art foreach (creates panels, covers, HTML per issue)
```

### Redo Characters After Storyboard Edit

```
design-characters with project_id=my-project
  → reads existing storyboard from assets
  → reuses characters that haven't changed
  → only regenerates characters with new roster entries or per_issue variants
```

### Redo Panels for One Issue After Character Redesign

```
issue-art with project_id=my-project issue_id=issue-002
  → reads storyboard for issue-002 from assets
  → reads latest character URIs from project
  → generates fresh panels with new character references
  → regenerates cover + composition
```

### Redo Just Composition Without Regenerating Images

```
issue-compose with project_id=my-project issue_id=issue-001
  → reads existing panels and cover from assets
  → re-runs only the compositor step with updated storyboard text/layout
  → produces new HTML without any image generation
```

### Resume After Partial Failure

```
issue-retry with project_id=my-project issue_id=issue-002
  → reads existing storyboard, characters, style from assets
  → regenerates only the panels/cover/HTML for that one issue
```

## `built_from` Metadata Implementation

The `built_from` metadata is stored in each asset's metadata dict at creation time. The tools that need updating:

| Tool Call | `built_from` Contents |
|-----------|----------------------|
| `comic_create(action='create_character_ref')` | Style version + base character URI (if variant) |
| `comic_create(action='create_panel')` | Storyboard version + character URIs used |
| `comic_create(action='create_cover')` | Storyboard version + character URIs used |
| `comic_create(action='assemble_comic')` | Panel versions + cover version + storyboard version |

The `built_from` metadata is written by the tool automatically — agents don't need to construct it manually. The tool captures the versions of the inputs it receives and records them.

## Error Handling

- **Missing upstream asset:** If a composable recipe cannot find a required input (e.g., `design-characters` with no storyboard), it fails immediately with a clear message: "No storyboard found for project X. Run saga-plan first."
- **Stale upstream asset:** Warning logged but generation proceeds with latest versions. The `built_from` metadata records what was actually used, so staleness is always detectable after the fact.
- **Partial generation failure:** The recipe fails at the step that errored. All previously stored assets remain in the store. The user can re-run just the failed recipe with the same inputs.
- **Character slug mismatch:** If the storyboard roster names a character that doesn't match any stored slug, the system treats it as a new character and generates from scratch.

## Testing Strategy

1. **Sub-recipe calling** — validate that `type: recipe` with relative paths resolves correctly in fresh executions (not just `validate`, but actual runtime).
2. **Character reuse** — run `design-characters` twice on the same project. Second run should produce zero image generation calls if nothing changed.
3. **Staleness detection** — create a panel, then update the storyboard version, then check that the panel's `built_from` is detected as stale.
4. **Composition-only** — run `issue-compose` on an issue with existing panels/cover. Verify no image generation calls are made.
5. **End-to-end orchestration** — run `session-to-comic` and verify it calls each composable recipe in sequence, with proper asset handoff between stages.
6. **Failure recovery** — kill `issue-art` mid-run, then run `issue-retry` for the same issue. Verify it picks up from stored assets.

## Files That Will Change

| File | Change |
|------|--------|
| `recipes/saga-plan.yaml` | **NEW** — Stage 1 as standalone recipe (discover, research, style, storyboard, validate, create issues) |
| `recipes/design-characters.yaml` | **NEW** — Stage 2 as standalone recipe (reads storyboard from assets, reuses existing characters) |
| `recipes/issue-compose.yaml` | **NEW** — composition-only recipe (reads existing panels/cover, re-runs assemble_comic) |
| `recipes/issue-art.yaml` | **MODIFY** — add `built_from` metadata to panel/cover creation |
| `recipes/issue-retry.yaml` | **MODIFY** — ensure it reads from assets correctly |
| `recipes/session-to-comic.yaml` | **MODIFY** — thin orchestrator calling composable sub-recipes |
| `modules/tool-comic-create/.../service.py` | **MODIFY** — add `built_from` metadata to `create_panel`, `create_cover`, `create_character_ref`, `assemble_comic` |
| `modules/tool-comic-create/.../__init__.py` | **MODIFY** — pass `built_from` metadata through to service |
| `agents/character-designer.md` | **MODIFY** — strengthen reuse logic, never recreate existing characters |
| `context/comic-instructions.md` | **MODIFY** — document composable pipeline and `built_from` metadata |
| `docs/diagrams/pipeline-flow.dot` | **MODIFY** — show composable entry points |

## Open Questions

1. **Storyboard revision UX** — should `saga-plan.yaml` detect an existing storyboard and offer to edit/revise it rather than skipping entirely? (e.g., "storyboard v1 exists — do you want to revise it or skip?")

2. **Automatic vs. manual staleness checking** — should `built_from` comparison happen automatically in recipes (a deterministic step that checks versions and warns) or be left to the user to inspect on demand?

3. **Project status recipe** — should there be a `project-status.yaml` recipe that reports the current state of all assets in a project — what exists, what's stale, what's missing — as a diagnostic tool before deciding what to re-run?
