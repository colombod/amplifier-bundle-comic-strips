# Comic Strip Bundle — Session Handoff

## Current State

**Branch:** `feat/layout-first-pipeline-and-metadata` (off `main` at `a32800b`)
**Commit:** `3a684df` — WIP: Layout-first pipeline and metadata.agent_id support
**Tests:** 263 passing (88 tool-comic-create + 175 tool-comic-assets)
**Main branch:** clean, untouched

---

## What Was Done (14 files changed)

### 1. Character metadata.agent_id (WORKING at storage level)

Characters can now store `metadata.agent_id` (e.g., `"foundation:explorer"`) in the freeform `metadata` dict on `CharacterDesign`. No new schema fields — uses the existing `metadata: dict`.

**Files:**
- `service.py` — `store_character()` now accepts `metadata=` param, passes to `CharacterDesign`
- `service.py` — New `update_issue()` method for patching issue title/description/metadata
- `tool-comic-assets/__init__.py` — `_store` handler passes `metadata` through; new `update_issue` action on `comic_project` tool
- `tool-comic-create/__init__.py` — `_create_character_ref` now forwards `metadata` to `store_character`

**Status:** Code works. The smoke test confirmed character-designer passes metadata to comic_create and it gets stored. The strip-compositor instructions reference `metadata.agent_id` for dialog voice enrichment, but this was never verified in the actual generated output.

### 2. Issue Title Propagation (WORKING at tool level)

The storyboard's narrative title now flows back to `issue.json` via a new recipe step.

**Files:**
- `service.py` — `update_issue()` method (merges metadata, patches title/description)
- `tool-comic-assets/__init__.py` — `update_issue` action wired into `ComicProjectTool`
- `session-to-comic.yaml` — Step 3b (`update-issue-title`) calls `comic_project(action='update_issue')` after storyboard

**Status:** The tool and recipe step exist. The smoke test showed the step ran, but verification that issue.json was actually updated was not done.

### 3. Layout Grid Templates Redesigned (CODE WORKS, AGENTS IGNORE IT)

The `_GRID_TEMPLATES` dict was reorganized with `{count}p-{description}` naming (e.g., `2p-split`, `3p-top-wide`). Legacy names kept as aliases. CSS span modifiers added for all new layouts.

**Files:**
- `html_renderer.py` — Complete overhaul of `_GRID_TEMPLATES` (50+ entries organized by panel count), new CSS span rules for `3p-*`, `4p-*`, `5p-*` layouts
- `test_assemble_comic.py` — One assertion loosened to not depend on specific grid syntax

**Status:** The templates exist and render correctly in unit tests. But the smoke test proved **agents never use them**. The storyboard-writer invented style-specific layout names (e.g., `naruto_wide_3`) instead of using the catalog. The `_grid_css()` function silently falls back to `_DEFAULT_GRID` (2x2) for any unknown ID.

### 4. Layout-First Pipeline Instructions (AGENTS IGNORE THESE)

The storyboard-writer was updated with a layout catalog, `page_layouts` output field, `aspect_ratio` per panel, and `page` field. The panel-artist was updated to use `aspect_ratio`. The strip-compositor was updated to read `page_layouts`.

**Files:**
- `storyboard-writer.md` — New Step 5 with layout catalog, `page_layouts` array in output, `aspect_ratio` per panel, `metadata.agent_id` per character
- `panel-artist.md` — New Size Resolution section, `aspect_ratio` as primary field, `character_uris` (not `character_sheet`)
- `strip-compositor.md` — Step 3 updated for `page_layouts`, new Step 4b with text/speech/SFX styling
- `character-designer.md` — Output simplified to URI-only, metadata forwarding, stale Fields section deleted

**Status:** Agent instructions are updated and internally consistent. But the smoke test proved the storyboard-writer **ignores the catalog** and invents its own layout names. The instructions are necessary but not sufficient — there is no enforcement.

### 5. Text/Speech/SFX Styling (INSTRUCTIONS ONLY, NEVER VERIFIED)

The strip-compositor's new Step 4b has comprehensive balloon-type mapping, tail placement rules, SFX design guidelines. Derived from `source_material_for_new_styles/Comic_Text_and_Speech_Style_Guide.md` and `Comic_Sound_Effects_Style_Guide.md`.

**Status:** Instructions exist. Never verified in actual output.

### 6. Agent Quality Fixes (17 issues fixed)

A foundation-expert review found 3 CRITICAL, 7 SIGNIFICANT, and 7 MINOR issues across all 4 agents. All were fixed:
- CRITICAL: `{{character_sheet}}` stale references in panel-artist, contradictory output formats in character-designer, reuse path returning JSON instead of URI
- SIGNIFICANT: frontmatter description mismatches, duplicate step numbering, variable name inconsistencies, character count ceiling inconsistencies

### 7. Pipeline Flow Diagram (UPDATED)

`docs/diagrams/pipeline-flow.dot` rewritten to v8 showing layout-first annotations, metadata flow, update-issue-title step. PNG rendered.

---

## What Failed in the Smoke Test

### Test Setup
- Shadow environment (`naruto-smoke`) with local bundle snapshot
- Session: `e7fa3a45` (context-intelligence project, 25 turns, 3070 events)
- Style: naruto, 8 pages requested, 7 characters max

### What Actually Happened
- Stage 1 completed (research, style, storyboard, title update, approval gate) — ~25 min
- Stage 2 started (character design, panel art, cover, composition) — ~45 min
- Final HTML: 4.2 MB, 6 pages total, 10 panels

### FAILURE 1: Every page uses default 2x2 grid

**Evidence:**
```
Story page 1: 3 panels, layout=naruto_wide_3,    grid=repeat(2,1fr) repeat(2,1fr)
Story page 2: 2 panels, layout=naruto_standard_2, grid=repeat(2,1fr) repeat(2,1fr)
Story page 3: 2 panels, layout=naruto_dynamic_2,  grid=repeat(2,1fr) repeat(2,1fr)
Story page 4: 1 panel,  layout=naruto_splash,      grid=repeat(2,1fr) repeat(2,1fr)
Story page 5: 2 panels, layout=naruto_dynamic_2,  grid=repeat(2,1fr) repeat(2,1fr)
```

**Root cause:** Storyboard-writer invented layout names (`naruto_wide_3`, etc.) that don't exist in `_GRID_TEMPLATES`. The `_grid_css()` function silently falls back to `_DEFAULT_GRID`. No validation, no error, no feedback to agents.

### FAILURE 2: Cover generation failed 3 times

All 3 attempts failed character consistency review (6-character Naruto group shot). The agent never tried alternatives — fewer characters, different composition, or different model. The pipeline returned `COVER_GENERATION_FAILED` sentinel but didn't handle it meaningfully.

### FAILURE 3: Only 10 panels instead of 24-28

The storyboard was supposed to produce 24-28 panels across 8 pages. Actual output: 10 panels across 5 story pages. Far less than specified.

### FAILURE 4: No storyboard stored as asset

No `storyboard/` directory exists under `issue-002`. The storyboard was parsed via `parse_json: true` but never stored — so there's no record of what the storyboard actually emitted.

### FAILURE 5: Global Amplifier pollution

During troubleshooting, `amplifier bundle add` was run on the host (not just in the shadow), registering `comic-strips` globally. This was cleaned up (`amplifier bundle remove comic-strips`).

---

## Why It Failed — Architectural Root Causes

### 1. Tools accept invalid input silently

`_grid_css()` takes any string and falls back to a default. No error, no warning, no feedback. The agent has no way to know its layout ID was rejected.

**Fix needed:** `_grid_css()` (or the `assemble_comic` action) must validate layout IDs. Unknown IDs should return an error listing valid options so the agent can self-correct. Alternatively, a dedicated `list_layouts` tool action that agents call to discover valid layouts.

### 2. Recipe has no validation checkpoints

The recipe trusts agents completely. If the storyboard produces invalid layout IDs, wrong panel counts, or missing fields — the recipe doesn't catch it. The storyboard flows through to art generation unchecked.

**Fix needed:** Deterministic validation steps in the recipe after the storyboard step. These should check:
- All `page_layouts[].layout` values exist in `_GRID_TEMPLATES`
- Panel count matches the sum across `page_layouts`
- Each panel has `aspect_ratio` set
- Character count is within budget
- `metadata.agent_id` is present on agent-derived characters

Use recipe-author to design these as proper recipe steps with clear pass/fail.

### 3. Agents discover layout options from markdown, not tools

The layout catalog is in the storyboard-writer's markdown instructions. The LLM reads it, decides "Naruto style needs Naruto-specific layouts," and invents names. There's no tool call that constrains the choice.

**Fix needed:** A `comic_create(action='list_layouts')` or `comic_asset(action='list_layouts')` tool that returns the valid layout IDs with their descriptions. The storyboard-writer should call this tool to discover what's available, not rely on instructions it can ignore.

### 4. Cover retry strategy doesn't adapt

Cover-artist bangs its head against the same wall 3 times — 6-character group shot fails character consistency every time. No strategy to reduce complexity on retry.

**Fix needed:** Cover-artist instructions should specify fallback strategies: attempt 1 = full cast, attempt 2 = reduce to 3 featured characters, attempt 3 = dramatic single-character cover. Or the recipe could provide escalating hints.

### 5. No closed-loop feedback

The system is open-loop: agent produces output → tool accepts it → recipe continues. There's no feedback path where a tool says "your layout ID is invalid, here are the valid options" and the agent retries.

**Fix needed:** Tools that return structured errors with correction hints. Agents that check tool responses and self-correct. Recipe validation steps that catch errors before expensive downstream work.

---

## What Needs to Happen Next (Priority Order)

### Phase 1: Tool-Level Enforcement

1. **Add layout validation to `assemble_comic`** — when a `pages[].layout` value isn't in `_GRID_TEMPLATES`, return a structured error with the list of valid IDs and a suggestion based on panel count
2. **Add `list_layouts` action** to `comic_create` or `comic_asset` — returns all valid layout IDs grouped by panel count, with descriptions. Agents call this to discover options.
3. **Add layout validation to `store` actions** — when storyboard data includes `page_layouts`, validate each layout ID against the known set

### Phase 2: Recipe Validation Steps

Use recipe-author to design deterministic validation steps:

1. **Post-storyboard validation step** — a lightweight agent or deterministic check that:
   - Validates all layout IDs exist
   - Validates panel counts match page_layouts
   - Validates aspect_ratio is set on every panel
   - Validates character count is within budget
   - Returns PASS/FAIL with actionable error messages
2. **Post-character-design validation step** — verifies all characters were generated (no silent failures)
3. **Post-panel-generation validation step** — verifies panel count matches storyboard

### Phase 3: Agent Instruction Updates

After tools enforce constraints and recipes validate:

1. **Storyboard-writer**: Must call `list_layouts` tool to discover valid options before selecting. Must not invent layout names.
2. **Cover-artist**: Fallback strategy on retry (reduce characters, change composition)
3. **Strip-compositor**: Must validate layout IDs match the HTML renderer's known set before calling `assemble_comic`

### Phase 4: Smoke Test

Run the same naruto smoke test again after all fixes. This time verify:
- Every page uses a valid layout ID that matches panel count
- Grid templates in HTML match the intended layouts
- Panels fill the page (no wasted grid cells)
- Cover generates successfully (or graceful fallback)
- Panel count matches what was requested

---

## Files and Locations

| Item | Path |
|------|------|
| Bundle repo | `/home/dicolomb/comic-strip-bundle/amplifier-bundle-comic-strips` |
| Feature branch | `feat/layout-first-pipeline-and-metadata` |
| WIP commit | `3a684df` |
| Grid templates | `modules/tool-comic-create/.../html_renderer.py` lines 26-135 |
| `_grid_css()` function | `html_renderer.py` line ~570 |
| `assemble_comic` handler | `modules/tool-comic-create/.../__init__.py` lines ~1094-1176 |
| Storyboard writer agent | `agents/storyboard-writer.md` |
| Panel artist agent | `agents/panel-artist.md` |
| Strip compositor agent | `agents/strip-compositor.md` |
| Character designer agent | `agents/character-designer.md` |
| Recipe | `recipes/session-to-comic.yaml` |
| Smoke test HTML output | `/home/dicolomb/comic-strip-bundle/context-intelligence-naruto-issue-002.html` |
| Shadow environment | `naruto-smoke` (still running, can be destroyed) |
| Shadow log (Stage 1) | `/tmp/smoke-test.log` (inside shadow) |
| Shadow log (Stage 2) | `/tmp/smoke-stage2.log` (inside shadow) |
| Session used for test | `e7fa3a45-782a-4f71-a470-4d1d3bf8c5d7` |
| Source material (text/speech) | `source_material_for_new_styles/Comic_Text_and_Speech_Style_Guide.md` |
| Source material (SFX) | `source_material_for_new_styles/Comic_Sound_Effects_Style_Guide.md` |

---

## Shadow Environment

The shadow `naruto-smoke` is still running. It has:
- Amplifier installed with the local bundle snapshot
- The session file at `/tmp/sessions/context-intel.jsonl`
- Generated assets at `/workspace/.comic-assets/projects/context-intelligence-naruto/`
- Stage 1 and Stage 2 logs at `/tmp/smoke-test.log` and `/tmp/smoke-stage2.log`

To destroy: `amplifier-shadow destroy naruto-smoke`

---

## Key Lesson

Agent instructions are necessary but not sufficient. Without tool-level validation that returns errors and correction hints, without recipe-level checkpoints that catch broken output before expensive downstream work, the agents silently produce garbage. The architecture needs a closed feedback loop: agents propose, tools validate and reject with guidance, agents correct, recipes verify before proceeding.
