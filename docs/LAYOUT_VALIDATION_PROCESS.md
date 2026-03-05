# Layout Validation: Closed Feedback Loop

Development narrative for the v7.6.0 layout validation system. This document
explains what the problem was, what was built, and how it was verified.

---

## 1. The Problem

The `session-to-comic` pipeline delegates page layout selection to the
storyboard-writer agent. The agent receives a style guide and must assign a
layout ID to each story page. The renderer (`html_renderer.py`) resolves these
IDs against `_GRID_TEMPLATES` -- a dictionary of 47 valid CSS grid definitions.

The storyboard-writer had no way to query which layout IDs actually exist. It
invented plausible-sounding names based on its training data and the style
context:

```
naruto_wide_3
dragon_blast_9
cinematic_splash_left
ghibli_watercolor_triptych
```

None of these exist in `_GRID_TEMPLATES`. The renderer resolved unknown IDs
with `dict.get(layout_id, default_grid)`, silently falling back to a 2x2
default. No error was raised. No warning was logged. The storyboard passed
validation. The approval gate showed the invented names without flagging them.
Image generation proceeded. The final HTML rendered every page with the same
identical 2x2 grid.

The result: comics that cost significant generation time and API spend, where
every page looks the same despite the storyboard specifying distinct layouts.

---

## 2. The SCRATCH.md Lesson

From SCRATCH.md during the debugging investigation:

> Agent instructions are necessary but not sufficient. Without tool validation
> that returns errors and hints, without recipe checkpoints that catch broken
> output, agents silently produce garbage. The system needs a closed feedback
> loop.

The storyboard-writer instructions already said "use valid layout IDs." The
problem was not a missing instruction -- it was the absence of enforcement. The
agent had no way to discover valid options, no tool to check its selections,
and no recipe step to catch mistakes before expensive downstream work began.

Adding more instructions to the agent prompt would not fix this. The system
architecture had to change.

---

## 3. What Was Built

Four phases, each building on the previous.

### Phase 1: Tool enforcement

New functions and actions that give agents and recipes the ability to discover
and validate layout IDs at runtime.

| Component | File | What it does |
|-----------|------|--------------|
| `get_available_layouts()` | `html_renderer.py` | Returns the full list of valid layout IDs from `_GRID_TEMPLATES` |
| `validate_layout_ids()` | `html_renderer.py` | Takes a list of layout IDs, returns pass/fail with per-ID diagnostics and suggestions for invalid IDs |
| `list_layouts` action | `__init__.py` | Tool action exposing `get_available_layouts()` to agents via `comic_create(action='list_layouts')` |
| `validate_storyboard` action | `__init__.py` | Tool action exposing `validate_layout_ids()` to recipe steps via `comic_create(action='validate_storyboard')` |
| `assemble_comic` validation gate | `__init__.py` | Pre-render check inside `assemble_comic` that validates all layout IDs before committing to HTML generation |
| `_grid_css()` warning log | `html_renderer.py` | Logs a warning when a layout ID is not found, as a last-resort diagnostic (defense-in-depth) |

### Phase 2: Recipe checkpoint

A new recipe step and an updated approval gate that catch invalid layouts
before image generation begins.

```yaml
# session-to-comic.yaml (simplified)

- name: storyboard
  agent: storyboard-writer
  # ... produces storyboard JSON with layout IDs

- name: validate-storyboard          # NEW in v7.6.0
  action: comic_create
  params:
    action: validate_storyboard
    storyboard: "{{storyboard.output}}"
  on_failure: abort                   # stops the recipe if any layout ID is invalid

- name: approval-gate
  type: approval
  show:
    - storyboard_summary
    - layout_validation_status        # NEW: reviewer sees validation result
```

The `validate-storyboard` step runs between storyboard generation and the
approval gate. If any layout ID is invalid, the recipe aborts with a diagnostic
message naming the bad IDs and suggesting valid alternatives. The human reviewer
never sees a storyboard with broken layouts.

### Phase 3: Agent update

The storyboard-writer agent prompt and workflow updated to use tool-driven
discovery instead of static knowledge.

| Change | Detail |
|--------|--------|
| `tool-comic-create` added to storyboard-writer | Agent can now call `comic_create` tool actions |
| Mandatory `list_layouts` call | Agent instructions require calling `comic_create(action='list_layouts')` before selecting any layout IDs |
| Static tables removed | Previously hardcoded layout tables in the prompt replaced with instruction to query the tool |
| Aspect ratio guide | Prompt includes guidance on matching layout choice to panel aspect ratios |

The agent now operates on live data from the renderer rather than on stale
prompt text that may drift from the implementation.

### Phase 4: Smoke test

Automated verification that the feedback loop works before running a full
(expensive) end-to-end generation.

| Test | What it checks |
|------|----------------|
| Micro-recipe with valid IDs | `validate_storyboard` passes, recipe continues |
| Micro-recipe with invalid IDs | `validate_storyboard` fails, recipe aborts with suggestions |
| Full e2e with naruto style | Complete pipeline: storyboard-writer calls `list_layouts`, `validate-storyboard` passes, `assemble_comic` passes, HTML renders with 3 distinct grid layouts |

The micro-recipe (`smoke-validate-storyboard.yaml`) uses synthetic storyboard
data with known valid and invalid layout IDs. It runs in seconds without image
generation.

---

## 4. Verification Evidence

### Unit tests

106 total tests, 18 new for layout validation:

| Test file | New tests | Coverage |
|-----------|-----------|----------|
| `test_layout_validation.py` | 9 | `get_available_layouts`, `validate_layout_ids`, `list_layouts` action, `validate_storyboard` action, suggestion matching, edge cases |
| `test_html_renderer.py` | 9 | `_grid_css` fallback warning, valid ID rendering, invalid ID handling, empty layout list, duplicate IDs |
| `test_tool_skeleton.py` | updated | Action list updated to include `list_layouts` and `validate_storyboard` |

### Smoke test

```
smoke-validate-storyboard.yaml: PASSED
  - Valid layout IDs (3p-top-wide, 3p-left-dominant, 3p-cinematic): PASS
  - Invalid layout ID (naruto_wide_3): CAUGHT, suggestion returned (3p-top-wide)
  - Mixed valid/invalid: CAUGHT, per-ID diagnostics correct
```

### Formal reviews

Three independent review passes:

| Reviewer | Result | Focus |
|----------|--------|-------|
| recipe-author | PASS | Recipe structure, step ordering, failure handling, approval gate content |
| result-validator | PASS | Output correctness, HTML structure, grid CSS applied per layout ID |
| foundation-expert | PASS | Tool registration, action schema, error message quality, backward compatibility |

### Full end-to-end

The naruto layout validation e2e test (`naruto-layout-validation-e2e.html`)
confirmed the complete loop:

```
1. storyboard-writer called comic_create(action='list_layouts')
   -> received 47 valid layout IDs

2. storyboard-writer selected: 3p-top-wide, 3p-left-dominant, 3p-cinematic
   -> all three from the valid set

3. validate-storyboard step: PASSED
   -> all 3 layout IDs confirmed valid

4. approval gate: showed layout_validation_status = PASSED
   -> human reviewer saw validation status

5. assemble_comic: PASSED
   -> pre-render validation confirmed layout IDs again

6. HTML output: 3 story pages with 3 DISTINCT grid layouts
   -> visual inspection confirmed different panel arrangements per page
```

---

## 5. Files Changed

7 files, approximately 400 lines added or modified.

| File | Changes |
|------|---------|
| `html_renderer.py` | Added `get_available_layouts()`, `validate_layout_ids()`, `_grid_css()` warning log on fallback |
| `__init__.py` | Added `list_layouts` action, `validate_storyboard` action, `assemble_comic` pre-render validation gate |
| `session-to-comic.yaml` | Added `validate-storyboard` step, updated approval gate to show `layout_validation_status`, v7.6.0 changelog entry |
| `storyboard-writer.md` | Added `tool-comic-create` to tool list, mandatory `list_layouts` call instruction, aspect ratio guide for layout selection |
| `test_layout_validation.py` | 9 new tool-level tests for layout discovery and validation actions |
| `test_html_renderer.py` | 9 new renderer-level tests for grid CSS resolution and fallback behavior |
| `test_tool_skeleton.py` | Updated action list assertions to include new actions |
| `smoke-validate-storyboard.yaml` | New test fixture recipe for automated smoke testing |

---

## 6. The Pattern

Layout validation is one instance of a general problem: an agent selecting from
a fixed set of options that it cannot enumerate from its training data. The same
failure mode applies anywhere a prompt says "choose from these options" but the
options live in code, not in the prompt.

The pattern has three layers:

```
Layer 1: Tool action to discover valid options
  - Agent calls a tool to get the current list at runtime
  - No stale prompt tables, no drift between docs and implementation
  - Agent sees exactly what the system accepts

Layer 2: Recipe step to validate selections
  - Runs after the agent makes its choices, before expensive downstream work
  - Returns per-item diagnostics with suggestions for invalid entries
  - Recipe aborts on failure -- invalid selections never reach generation

Layer 3: Render-time enforcement (defense-in-depth)
  - Final validation at the point of use
  - Logs warnings for any ID that slipped through earlier layers
  - Prevents silent fallback to defaults
```

The key insight: make invalid choices impossible rather than hoping instructions
prevent them. Instructions tell the agent what to do. Tool enforcement ensures
it cannot do otherwise. Recipe checkpoints catch mistakes early. Render-time
validation is the last line of defense.

This pattern is reusable beyond layouts. Any fixed option set in the pipeline --
panel shapes, aspect ratios, style pack names, page templates -- can use the
same three-layer structure: discover, validate, enforce.
