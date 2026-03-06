# v8.0.0 Saga System Design

## Goal

Transform the `session-to-comic` recipe from a single-issue-per-run pipeline into a multi-issue saga system where one run discovers all material, plans a multi-issue narrative arc, gets a single approval, then loops through each issue — producing separate HTML files per issue with narrative continuity, shared characters, and per-issue visual evolution.

## Background

The current recipe produces one comic issue per execution. For larger source material — such as an entire project's development history — the content naturally spans multiple issues. Today, producing a multi-issue series requires manually running the recipe multiple times, with no shared character continuity, no narrative arc across issues, and no way to plan the full story upfront.

The saga system solves this by making multi-issue output a first-class capability: one run discovers all material, an LLM plans the full arc, characters are designed once and evolved across issues, and each issue is generated with narrative hooks (recaps, cliffhangers) that tie the series together.

## Approach

**Hybrid: saga planning step + foreach over issue sub-recipe (Approach C).**

The main recipe handles all shared work — discovery, research, saga planning, style curation, and character design. A lightweight sub-recipe (`issue-art.yaml`) handles per-issue work — panel art, cover art, and HTML composition. The recipe engine's `foreach` + `type: recipe` pattern connects them.

This keeps the main recipe focused on narrative and character decisions while the sub-recipe is a pure art-generation loop with no discovery or approval logic.

## Architecture

The recipe is restructured into three stages with a clear separation of concerns:

```
Stage 1: Saga Planning (text-only, cheap)
  ├── Init Project
  ├── Discover Sessions (flexible source= input)
  ├── Research
  ├── Style Curation
  ├── Saga Storyboard (full arc + character roster)
  ├── Validate Storyboard (layout IDs across ALL issues)
  ├── Create Issues (foreach: issue-001, issue-002, ...)
  └── Approval Gate (full saga summary)

Stage 2: Character Design (image gen, shared across saga)
  └── foreach character in roster → character-designer
        ├── Cross-project discovery (search action)
        ├── Reuse / redesign / new decision
        └── Per-issue variant creation (v1, v2, v3...)

Stage 3: Per-Issue Art Generation (image gen, per issue)
  └── foreach issue → issue-art.yaml sub-recipe
        ├── Panel art (foreach panel)
        ├── Cover art
        ├── Composition (recap + cliffhanger)
        └── Store final HTML
```

## Components

### Stage 1: Saga Planning

All text-based, no image generation. This is the cheapest stage and produces the full narrative plan.

**Step 0 — Init Project:** Creates the project structure but NOT individual issues. Issues are created later in Step 3b after the saga plan determines how many are needed.

**Step 0a — Discover Sessions:** Uses the v7.7.0 flexible `source=` input to find and load session data. Also returns a `suggested_project_name` derived from the source material when the user hasn't provided an explicit `project_name`.

**Step 1 — Research:** Comic-specific extraction from the discovered session data. Identifies narrative beats, key moments, character candidates.

**Step 2 — Style Curation:** Loads the style pack for the chosen visual style.

**Step 3 — Saga Storyboard:** The storyboard-writer produces the full saga plan as a single JSON output. This includes: how many issues, the narrative arc across all of them, per-issue beat breakdown, cliffhangers between issues, and the full character roster across the saga. See [Saga Storyboard Structure](#saga-storyboard-structure) for the schema.

**Step 3a — Validate Storyboard:** Validates layout IDs across ALL issues in the saga plan. Ensures every referenced layout exists and every panel slot is accounted for.

**Step 3b — Create Issues:** A `foreach` over the `saga_plan.issues[]` array that calls `create_issue` for each one, producing `issue-001`, `issue-002`, etc.

**Approval Gate:** Shows the full saga arc, all issue summaries, all characters, and layout validation status. This is the single approval point for the entire saga — no per-issue approvals.

### Stage 2: Character Design

Runs a `foreach` over the unique character roster from the saga storyboard. The character-designer runs once per character (not once per issue), producing all needed variants upfront.

For each character, the designer:

1. **Checks `existing_uri`** — if a cross-project match was found during saga planning and it's reusable for issue 1, keeps it as-is.
2. **Looks at `per_issue`** — for each issue that has `needs_new_variant: true`, creates a new variant linked to the base character (`v2`, `v3`, etc.). Each variant's metadata includes the evolution description and the issue number.
3. **Creates fresh** if no existing character fits — but stores cross-project links in metadata for future discovery.

Characters are designed at the project level and reusable across all issues in the saga.

### Stage 3: Per-Issue Art Generation

A single `foreach` step with `type: recipe` that invokes `issue-art.yaml` for each issue. See [Sub-Recipe: issue-art.yaml](#sub-recipe-issue-artyaml) for details.

### Smart Project Naming

The discover-sessions step proposes a meaningful project name derived from the source material:

- If the user provides `project_name` explicitly → use it (override).
- If `project_name` is empty → the discover step proposes one based on the narrative content it found. For `source="comic-strip-bundle project - all iterations"`, it might suggest `comic-engine-chronicles` or `forging-the-comic-engine`.
- `init-project` uses `{{session_data.suggested_project_name}}` as a fallback when `project_name` is empty.

The storyboard-writer also assigns a **saga title** (e.g., "Forging the Comic Engine") and **per-issue titles** that appear on covers. The project name is the technical identifier; the saga title is the narrative title.

## Saga Storyboard Structure

The storyboard JSON has two separate scopes:

**Saga-level (shared):**
- `saga_plan` — arc summary, total issues, overall theme
- `character_roster[]` — ALL characters across the saga, with metadata for discovery/reuse

**Per-issue (scoped):**
- Each entry in `saga_plan.issues[]` has its OWN `character_list[]` containing only the characters that appear in THAT issue. These reference the roster entries by slug but are scoped to what the panel-artist and cover-artist actually need for that specific issue.

```json
{
  "title": "Forging the Comic Engine",
  "saga_plan": {
    "total_issues": 3,
    "arc_summary": "From first prototype to production pipeline...",
    "issues": [
      {
        "issue_number": 1,
        "title": "The Blueprint",
        "character_list": ["the_architect", "the_explorer"],
        "panel_list": ["..."],
        "page_layouts": ["..."],
        "cliffhanger": "The shadow test reveals..."
      },
      {
        "issue_number": 2,
        "title": "The Validation Wars",
        "character_list": ["the_architect", "the_explorer", "the_validator"],
        "recap": "Previously: ...",
        "cliffhanger": "Agents silently produce garbage...",
        "panel_list": ["..."],
        "page_layouts": ["..."]
      },
      {
        "issue_number": 3,
        "title": "The Production Run",
        "character_list": ["the_architect", "the_explorer", "the_validator", "the_researcher"],
        "recap": "Previously: ...",
        "cliffhanger": null,
        "panel_list": ["..."],
        "page_layouts": ["..."]
      }
    ]
  },
  "character_roster": [
    {
      "name": "The Architect",
      "char_slug": "the_architect",
      "role": "protagonist",
      "first_appearance": 1,
      "existing_uri": null,
      "visual_traits": "...",
      "metadata": { "agent_id": "foundation:zen-architect", "bundle": "foundation" }
    },
    {
      "name": "The Explorer",
      "char_slug": "the_explorer",
      "role": "specialist",
      "first_appearance": 1,
      "existing_uri": "comic://other-project/characters/the_explorer?v=1",
      "needs_redesign": false,
      "visual_traits": "...",
      "metadata": { "agent_id": "foundation:explorer", "bundle": "foundation" }
    }
  ]
}
```

## Character Evolution Across Issues

Each character in the roster gets a `per_issue` map that specifies visual overrides or evolution notes for specific issues. The character-designer uses these to decide whether to create a new variant.

```json
{
  "name": "The Explorer",
  "char_slug": "the_explorer",
  "base_visual_traits": "hooded figure, brown cloak, carries a lantern",
  "existing_uri": "comic://other-project/characters/the_explorer?v=1",
  "needs_redesign": false,
  "per_issue": {
    "1": null,
    "2": {
      "evolution": "cloak is torn, lantern cracked, carries a map",
      "needs_new_variant": true
    },
    "3": {
      "evolution": "fully armored, lantern replaced with energy sword",
      "needs_new_variant": true
    }
  }
}
```

The `foreach` over the roster in Stage 2 produces one design task per unique variant needed, not one per character. When `issue-art.yaml` runs for a specific issue, its `character_list` resolves to the correct variant URIs for that issue — The Explorer in issue 2 gets `v2`, issue 3 gets `v3`.

## Cross-Project Character Discovery

A new `search` action on the `comic_character` tool enables discovering characters across all projects:

```
comic_character(action='search', style='transformers', metadata_filter={"agent_id": "foundation:explorer"})
```

This searches across ALL projects in `.comic-assets/projects/` for characters that have a variant in the requested style. Returns matches with URIs, visual traits, metadata, and originating project/issue.

**How it's used:** The storyboard-writer calls this during saga planning. When it identifies that a character in the story maps to an existing agent, it searches for cross-project matches. If found, it sets `existing_uri` on the roster entry. The character-designer then decides: reuse as-is, create a new variant using the existing one as a reference base, or create fresh.

**What this does NOT change:**
- Characters are still stored at the project level (`comic://project/characters/slug`)
- The search is read-only discovery — it doesn't move or copy characters between projects
- The character-designer's existing 3-case logic (reuse / redesign / new) stays the same — it just gets a broader input scope

**Implementation:** The `search` action in `tool-comic-assets` walks all `projects/*/characters/` directories, reads each character's metadata, and filters by style and optional metadata fields.

## Sub-Recipe: issue-art.yaml

Lightweight per-issue recipe invoked by Stage 3's `foreach`. Pure art generation and composition — no discovery, research, or style curation.

### Inputs (from parent foreach)

| Variable | Source | Example |
|----------|--------|---------|
| `project_id` | Parent context | `comic-engine-chronicles` |
| `issue_id` | Created in Stage 1 step 3b | `issue-002` |
| `issue_number` | From `saga_plan.issues[]` | `2` |
| `issue_storyboard` | That issue's slice from the saga storyboard | `{panel_list, page_layouts, recap, cliffhanger, ...}` |
| `character_uris` | Resolved in Stage 2 — map of char_slug to variant URI per this issue | `{"the_explorer": "comic://proj/characters/the_explorer?v=2"}` |
| `style_uri` | From parent style curation | `comic://proj/styles/transformers` |
| `output_name` | Parent context + issue number | `transformers-comic-issue-002` |
| `saga_context` | Previous issue's cliffhanger + recap text | For narrative continuity |

### Steps

1. **Panel art** — `foreach` over `issue_storyboard.panel_list`, panel-artist generates each panel using the issue-specific character variant URIs.
2. **Cover art** — Cover-artist generates the cover for this issue, featuring only the characters in this issue's `character_list`.
3. **Composition** — Strip-compositor assembles the HTML using the issue's `page_layouts`, panels, and cover. Adds recap text at the start (issues 2+) and a "To Be Continued" cliffhanger tease at the end (all except the final issue).
4. **Store final** — `assemble_comic` writes the self-contained HTML to `issues/{issue_id}/final/`.

**What the sub-recipe does NOT do:**
- No discovery, research, or style curation (already done in parent Stage 1)
- No character design (already done in parent Stage 2)
- No approval gate (already approved at saga level in Stage 1)

## Data Flow

```
User Input (source, style, project_name?)
  │
  ▼
Stage 1: Saga Planning
  │
  ├─ discover-sessions ──► session_data + suggested_project_name
  ├─ research ──► narrative beats, key moments
  ├─ style-curation ──► style_uri
  ├─ storyboard-writer ──► saga_storyboard JSON
  │    ├─ saga_plan.issues[] (per-issue panels, layouts, characters)
  │    └─ character_roster[] (full cast with per_issue evolution)
  ├─ validate-storyboard ──► layout validation across all issues
  ├─ create-issues ──► issue-001, issue-002, ...
  └─ APPROVAL GATE
  │
  ▼
Stage 2: Character Design
  │
  ├─ foreach character in roster:
  │    ├─ cross-project search (comic_character action=search)
  │    ├─ reuse / redesign / create decision
  │    └─ per-issue variant creation (v1, v2, v3...)
  └─► character_variant_map: {char_slug: {issue_num: variant_uri}}
  │
  ▼
Stage 3: Per-Issue Art (foreach issue → issue-art.yaml)
  │
  ├─ issue-art.yaml receives: storyboard slice, variant URIs, saga_context
  │    ├─ foreach panel → panel-artist
  │    ├─ cover-artist
  │    ├─ strip-compositor (recap + cliffhanger)
  │    └─ assemble_comic → issues/{issue_id}/final/*.html
  │
  └─► Separate self-contained HTML per issue
```

## Error Handling

- **Storyboard validation failure:** Blocks at Stage 1 before the approval gate. The saga plan must have valid layouts across all issues before proceeding.
- **Character search failure:** Non-fatal. If cross-project discovery fails or finds nothing, the character-designer falls back to creating fresh — the existing 3-case logic handles this gracefully.
- **Sub-recipe failure:** Currently, a failed issue will halt the Stage 3 foreach. Whether to adopt `on_error: continue` is an open question (see below).
- **Cache staleness:** The dual-cache problem (runtime creates a second clone at an older commit) is addressed by the cache invalidation procedure before testing.

## Testing Strategy

### Cache Invalidation (pre-test)

```bash
amplifier reset --remove cache -y
amplifier bundle add git+https://github.com/colombod/amplifier-bundle-comic-strips@main --app
```

Forces a fresh single clone from published main — no stale second copy.

### Test Levels

1. **Unit tests** — New tests for `comic_character(action='search')` cross-project discovery, and for the `per_issue` variant resolution logic in the character model.
2. **Recipe validation** — `recipes validate` on both `session-to-comic.yaml` and the new `issue-art.yaml` sub-recipe.
3. **Micro-recipe smoke test** — Synthetic saga with 2 issues, validating: issue creation loop produces `issue-001` + `issue-002`, character reuse skips generation, layout validation passes across both issues.
4. **Full e2e** — Run the transformers comic with `source=comic-strip-bundle`, let the saga planner decide how many issues. Verify: separate HTML per issue, characters shared across issues, narrative continuity (recap pages, cliffhangers), correct layouts per issue.

### Version Bump

**v8.0.0** — Major feature: multi-issue saga with architectural changes to the recipe, character model, and new sub-recipe.

## Files Changed

| File | Change |
|------|--------|
| `recipes/session-to-comic.yaml` | 3-stage restructure, saga storyboard step, issue creation foreach, character design foreach |
| `recipes/issue-art.yaml` | **NEW** — per-issue sub-recipe (panels, cover, composition) |
| `agents/storyboard-writer.md` | Saga planning instructions, character roster vs per-issue character_list, per_issue evolution |
| `agents/character-designer.md` | Cross-project discovery, per-issue variant creation, evolution notes |
| `modules/tool-comic-assets/.../service.py` | `search` action for cross-project character discovery |
| `modules/tool-comic-assets/.../__init__.py` | Wire up `search` action |
| `context/comic-instructions.md` | Updated data flow for 3-stage saga pipeline |
| `docs/diagrams/pipeline-flow.dot` | Redrawn for 3-stage saga architecture |
| `examples/README.md` | Updated invocation examples with saga parameters |

## Open Questions

1. **Max issues cap** — Should there be a `max_issues` context variable to cap how many issues the saga planner can create? This prevents runaway 20-issue sagas from an overly ambitious storyboard-writer.
2. **Error policy for sub-recipe** — Should `issue-art.yaml` have an `on_error: continue` policy so one failed issue doesn't block the rest of the saga?
3. **Character search caching** — Should character search results be cached per recipe run to avoid re-scanning `.comic-assets/` for every character in the roster?
