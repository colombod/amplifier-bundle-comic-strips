# Performance & Recipe Architecture Design

## Goal

Fix an active CPU-spin incident caused by missing API backoff in the image generation module, and refactor the recipe architecture to move iteration loops from inside agents into the recipe layer — reducing per-agent context size, enabling sequential foreach orchestration, and laying the groundwork for future parallelism and project state management.

## Background

Two independent problems converged into a single design effort. The immediate problem is a CPU-spin incident in production: both image generation backends (`openai_images.py` and `gemini_images.py`) have no retry/backoff logic, so any 429 or 5xx response from the upstream API causes a tight retry loop that pegs the CPU. A fix is needed urgently.

The structural problem is that the recipe architecture places iteration responsibility inside individual agents. The character-designer and panel-artist each manage their own internal loops over a roster or panel list, which means every agent invocation accumulates a growing context as results collect. This makes context size hard to predict, prevents the recipe layer from having visibility into per-item progress, and blocks future parallelism.

## Approach

Two fully independent tracks, shipped in sequence.

**Track A** (Python module fixes) ships first as a single PR to resolve the active incident. It touches only `modules/tool-comic-image-gen/`. No recipe or agent markdown files change.

**Track B** (recipe architecture refactor) follows as a separate PR once Track A is merged. It redesigns the storyboard output, narrows the character-designer and panel-artist to single-item agents, and replaces the monolithic design/generation steps with `foreach` loops in the recipe.

Neither track blocks the other from being designed, but Track A merges first.

---

## Track A — Python Module Fixes

All four changes ship together in a single PR. All files are inside `modules/tool-comic-image-gen/`.

### Components

#### P0 — Exponential Backoff with Jitter

**Files:** `providers/openai_images.py`, `providers/gemini_images.py`

Both `generate()` methods gain a retry loop of up to 3 attempts. Between attempts, the caller sleeps for `2**attempt + random.uniform(0, 1)` seconds (exponential backoff with jitter). Retries trigger on HTTP 429 and 5xx responses only. Non-retryable errors — auth failures (401/403), invalid prompts, malformed inputs — fail immediately on the first attempt without consuming retry budget.

This is the direct fix for the CPU-spin incident.

#### P1 — Non-Blocking File Reads

**Files:** `providers/openai_images.py`, `providers/gemini_images.py`

The `_call_edit()` and `_build_content_config()` methods currently call `Path(p).read_bytes()` synchronously inside async functions, blocking the event loop during disk I/O. These become `await asyncio.to_thread(Path(p).read_bytes)`. On SD card storage (the primary deployment target) this is especially impactful.

#### P1 — Avatar Fetch Retry

**File:** `agents/cover-artist.md`

The `web_fetch` call for the GitHub avatar PNG gains a retry instruction: up to 3 attempts with a brief wait between each. If all attempts fail, the cover step continues without the avatar and emits a visible warning in the cover HTML rather than failing the pipeline. This is a graceful degradation — the cover is non-blocking.

#### P2 — Wire Model Selector into execute()

**File:** `__init__.py`

`ComicImageGenTool.execute()` currently ignores the `requirements` dict passed by callers. It now passes `requirements` to `select_model()`, receives the optimal `model_id`, and forwards it to the backend. The explicit `model` override parameter continues to bypass selection entirely when provided.

---

## Track B — Recipe Architecture Refactor

Three things change: the storyboard-writer's output contract, two agents narrowed to single-item scope, and the recipe itself. Cover-artist and strip-compositor are unchanged.

### Components

#### Storyboard-Writer — Two New Structured Outputs

**File:** `agents/storyboard-writer.md`

The storyboard-writer's core narrative work is unchanged. It gains explicit responsibility for emitting two flat context variables alongside the existing full storyboard JSON:

- **`character_list`** — a JSON array of character objects. Each entry is self-contained and includes: `name`, `role`, `bundle_affiliation`, and `visual_traits`. No cross-references to other entries; each object is everything the character-designer needs for one character.
- **`panel_list`** — a JSON array of panel spec objects. Each entry includes: `index`, `size`, `scene_description`, `characters_present` (list of names), `dialogue`, and `emotional_beat`. Each object is everything the panel-artist needs for one panel.

These two arrays become the foreach inputs in the recipe.

#### Character-Designer — Single-Character Agent

**File:** `agents/character-designer.md`

Redesigned to receive exactly one character object via `{{character_item}}` from the recipe foreach loop. Responsibilities per invocation:

1. Load the image prompt engineering skill.
2. Craft a single reference image prompt from the character object.
3. Call `generate_image` once.
4. Return a single character sheet entry.

No internal loop. No roster accumulation. Context per invocation is bounded to one character object plus the style guide — dropping from the current unbounded accumulation of all prior character results.

#### Panel-Artist — Single-Panel Agent

**File:** `agents/panel-artist.md`

Redesigned to receive exactly one panel spec via `{{panel_item}}` from the recipe foreach loop. Also receives the complete character sheet (already built by the time panels run) and the style guide. Responsibilities per invocation:

1. Generate one panel image.
2. Self-review with up to 3 retries.
3. Return one panel result.

Context stays small and predictable throughout the panel sequence.

#### Recipe — foreach Orchestration

**File:** `recipes/session-to-comic.yaml`

The monolithic character-design step and generate-panels step are replaced with two `foreach` blocks:

1. **Character foreach** — iterates over `character_list`, dispatching the single-character designer for each entry. Collects results into the character sheet.
2. **Panel foreach** — iterates over `panel_list`, dispatching the single-panel artist for each entry with the completed character sheet in scope.

The approval gate, cover-artist, and strip-compositor steps are structurally unchanged.

Every recipe change is authored via `recipes:recipe-author` and validated via `recipes:result-validator` against the original functional spec before any PR is raised. These are mandatory checkpoints.

---

## Data Flow

```
[session-to-comic.yaml]
        │
        ▼
[storyboard-writer]
  → full storyboard JSON
  → character_list[]          ─────────────────────────────────────┐
  → panel_list[]              ──────────────────────────┐          │
        │                                               │          │
        ▼                                               │          │
[foreach: character_list]                               │          │
  → character-designer (×N)                            │          │
      receives: character_item                         │          │
      calls: generate_image (1×)                       │          │
      returns: character sheet entry                   │          │
  → collects: character_sheet[]                        │          │
        │                                              │          │
        ▼                                              ▼          │
[foreach: panel_list] ◄─────── panel_list[] ──────────┘          │
  → panel-artist (×M)                                             │
      receives: panel_item + character_sheet                      │
      calls: generate_image (1× + up to 3 retries)               │
      returns: panel result                                       │
  → collects: panels[]                                           │
        │                                                        │
        ▼                                                        │
[approval gate]                                                  │
        │                                                        │
        ▼                                                        │
[cover-artist] ◄────────────── full storyboard JSON ────────────┘
        │
        ▼
[strip-compositor]
        │
        ▼
  final comic output
```

**Python layer (inside each `generate_image` call):**

```
generate_image call
  → select_model(requirements)        [P2 — model selector]
  → backend.generate()
      → asyncio.to_thread(read_bytes) [P1 — non-blocking I/O]
      → API call
          → 429 / 5xx → sleep(backoff) → retry (max 3) [P0 — backoff]
          → 401 / other → fail immediately
      → return result
```

---

## Error Handling

### Python Layer (Track A)

| Condition | Behaviour |
|---|---|
| HTTP 429 or 5xx | Retry up to 3 attempts with exponential backoff + jitter |
| HTTP 401 / 403 / malformed input | Fail immediately, no retry |
| All retries exhausted | Return `success: False` with final error message |

### Character foreach Failures (Track B)

If a character's reference image cannot be generated after all Python-level retries, the recipe step fails and the pipeline halts. This is intentional — character reference images are upstream inputs to every panel and the cover. Proceeding without a reference would produce an inconsistent comic. The user receives a clear failure at a named character step.

### Panel foreach Failures (Track B)

Each panel step gets up to 3 agent-level self-review retries plus Python-level backoff beneath that. If a panel ultimately fails, the recipe halts at that panel index. All prior panels are already persisted, so resuming from the failed step recovers all prior work. The strip-compositor is never reached until all panels succeed.

### Cover Failures

Unchanged from current behaviour — up to 3 attempts, best result used if all fail, flagged for manual review rather than blocking the pipeline.

### Avatar Fetch Failure (Track A)

Up to 3 retries with brief waits. If all fail, the cover step continues without the avatar image and emits a visible warning in the cover HTML. Not a hard stop.

---

## Testing Strategy

### Track A — Unit Tests

All tests in `modules/tool-comic-image-gen/tests/`.

**Backoff tests:**
- Mock the API client to return 429 twice then succeed. Assert: three total attempts made; `asyncio.sleep` called with increasing durations; final result is success.
- Mock an auth error (401). Assert: fails immediately on first attempt; no retry; sleep not called.

**Async file reads:**
- Patch `asyncio.to_thread` and assert it is called with `Path.read_bytes` as the callable, rather than `Path.read_bytes()` being invoked directly.

**Model selector wiring:**
- Pass a `requirements` dict through `execute()`. Assert the backend receives the `model_id` that `select_model()` would return for that requirements dict.

### Track B — Recipe and Agent Tests

**Agent frontmatter fix:**
- `test_agent_tools_sections.py` currently fails because agent frontmatter is missing `tools:` sections. Both redesigned agents (character-designer, panel-artist) will include explicit frontmatter, resolving the existing failure.

**Storyboard output contract:**
- New test asserting that `character_list` and `panel_list` are present in storyboard-writer output, are valid JSON arrays, and each entry contains the fields expected by the foreach agents (all required keys present, correct types).

**Recipe structure:**
- New test class (following `test_recipe_v4_improvements.py` conventions) asserting: foreach steps exist for both character and panel loops; each foreach references the correct agent; the approval gate step is preserved in its original position.

**Recipe authoring and validation:**
- Every recipe change passes through `recipes:recipe-author` for authoring and `recipes:result-validator` for validation against the original functional spec. These are mandatory pre-PR checkpoints, not optional reviews.

---

## Open Questions

1. **Retry classification completeness** — Which HTTP status codes beyond 401/403 should be treated as non-retryable and skip backoff entirely? (e.g. 400 Bad Request, 422 Unprocessable Entity)

2. **foreach input format** — Should `character_list` and `panel_list` be emitted as JSON strings in recipe context variables, or as structured YAML? Answer depends on the recipe engine's foreach input format and how context variables are interpolated into agent prompts.

3. **Future parallelism** — Parallel foreach design and project state management tooling are explicitly out of scope for this design. The sequential foreach structure is intentional: when state management tooling exists, the foreach steps convert directly to parallel dispatch with no structural redesign required.
