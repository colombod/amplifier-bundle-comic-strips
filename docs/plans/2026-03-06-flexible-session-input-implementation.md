# Flexible Session Input — Implementation Plan

> **Execution:** Use the subagent-driven-development workflow to implement this plan.

**Goal:** Replace the rigid `session_file` input with a flexible `source` input that accepts project names, session IDs, file paths, or descriptive phrases — letting the story-researcher agent discover session data using its native tools.

**Architecture:** A new `discover-sessions` step (Step 0a) slots between `init-project` and `research`. It receives the user's `source` string, resolves it to concrete session data via git/gh/grep/delegation, stores consolidated data as a comic asset, and passes the URI to the research step. The existing `session_file` variable remains as a deprecated backward-compatible alias.

**Tech Stack:** Recipe YAML, GraphViz dot, Markdown documentation. No Python code changes.

**Design document:** `docs/plans/2026-03-06-flexible-session-input-design.md`

---

## Scope

**IN v1 (this plan):** Recipe context variables, new discover-sessions step, research step prompt update, init-project metadata update, version bump + changelog, pipeline dot file, comic-instructions.md data flow section, examples/README.md invocation examples, recipe validation.

**DEFERRED:** Full e2e smoke test (recipe validation is sufficient for YAML/prompt/doc changes). Updating `smoke-validate-storyboard.yaml` test fixture (it doesn't use `session_file`).

---

### Task 1: Update recipe context variables

**Files:**
- Modify: `recipes/session-to-comic.yaml` (lines 238–243)

**Step 1: Update the usage comments and context block**

Open `recipes/session-to-comic.yaml`. Find the usage comments (lines 238–240) and context block (lines 242–243).

Replace this exact block:

```yaml
# Usage:
#   amplifier run "execute session-to-comic with session_file=~/.amplifier/sessions/2026-02-27/events.jsonl style=superhero"
#   amplifier run "execute session-to-comic with session_file=./my-session.jsonl style=manga output_name=my-comic"

context:
  session_file: ""        # Required: path to events.jsonl session file or session ID
```

With:

```yaml
# Usage:
#   amplifier run "execute session-to-comic with source=comic-strip-bundle style=superhero"
#   amplifier run "execute session-to-comic with source=./my-session.jsonl style=manga output_name=my-comic"
#   amplifier run "execute session-to-comic with session_file=./events.jsonl style=naruto"  # (deprecated, still works)

context:
  source: ""              # Required: project name, session ID(s), file path(s), or descriptive phrase
  session_file: ""        # Deprecated: backward-compatible alias for source (single file path)
```

**Step 2: Verify the edit**

Run: `head -n 256 recipes/session-to-comic.yaml | tail -n 20`

Expected: You see `source: ""` on the line after `context:`, followed by `session_file: ""` with its deprecated comment. The usage comments show the new `source=` syntax with a deprecated `session_file=` example.

**Step 3: Commit**

```bash
cd amplifier-bundle-comic-strips
git add recipes/session-to-comic.yaml
git commit -m "feat: add source context variable, deprecate session_file"
```

---

### Task 2: Add the discover-sessions step to the recipe

**Files:**
- Modify: `recipes/session-to-comic.yaml` (insert between lines 282 and 284)

**Step 1: Insert the new step between init-project and research**

Find the end of the `init-project` step (line 282: `timeout: 120  # init-project: ...`) and the beginning of the research step comment block (line 284: `# ============================================` / line 285: `# STEP 1: RESEARCH`).

Insert the following new step block **between** those two sections — after line 282 and before line 284:

```yaml

      # ============================================
      # STEP 0a: DISCOVER SESSIONS - Source Resolution
      # Translates the user's flexible {{source}} input
      # (project name, session IDs, file paths, or
      # descriptive phrase) into consolidated session data.
      # The researcher discovers data using its native tools
      # — not hardcoded paths.
      # ============================================
      - id: "discover-sessions"
        agent: "stories:story-researcher"
        prompt: |
          You are given a source describing what to research: {{source}}
          Legacy session file (if provided): {{session_file}}

          If source is provided, use it. If source is empty but session_file is provided, use session_file instead.
          If BOTH are empty, STOP and return an error: {"error": "No source or session_file provided. One is required."}

          The source could be any of these — inspect the string and figure out which:
          - A project name (e.g. "comic-strip-bundle")
          - A directory path to a project
          - A single session file path (e.g. path/to/events.jsonl)
          - A session ID or comma-separated list of session IDs
          - A descriptive phrase (e.g. "the context-intelligence project")

          YOUR JOB: Discover and gather the relevant Amplifier session data — agent activity,
          tool usage, key moments, outcomes, and metrics. Use your tools freely: bash (git log,
          gh CLI, find, ls), grep, read_file, and delegation to foundation:explorer for deep
          exploration. Synthesize across multiple sessions if the source spans more than one.

          DO NOT extract comic-specific structures (characters, panel moments, narrative arcs).
          That is the research step's job. You are purely "find the data and consolidate it."

          Store the consolidated research material using:
          comic_asset(action='store', project='{{project_init.project_id}}', issue='{{project_init.issue_id}}', type='research', name='session-discovery', content=<your consolidated session data>)

          Return ONLY the URI string from the store response. Your entire output should be just the URI, e.g.:
          comic://my-project/issues/issue-001/research/session-discovery?v=1
        output: "session_data"
        timeout: 600  # discover-sessions: exploration + consolidation (~5-8 min)
```

**Step 2: Verify the edit**

Run: `grep -n 'id: "discover-sessions"\|id: "init-project"\|id: "research"' recipes/session-to-comic.yaml`

Expected: Three lines showing `init-project`, then `discover-sessions`, then `research` in order.

**Step 3: Commit**

```bash
cd amplifier-bundle-comic-strips
git add recipes/session-to-comic.yaml
git commit -m "feat: add discover-sessions step (step 0a) for flexible source resolution"
```

---

### Task 3: Update the research step prompt

**Files:**
- Modify: `recipes/session-to-comic.yaml` (the research step prompt, currently starting at line 289)

**Step 1: Replace the research step prompt opening**

Find the research step prompt. It currently starts with:

```yaml
        prompt: |
          Analyze the Amplifier session at: {{session_file}}

          Extract structured data for comic strip creation:
```

Replace those first three lines of the prompt (keeping the `prompt: |` line) with:

```yaml
        prompt: |
          Analyze the session data at: {{session_data}}

          Load the consolidated session data:
          comic_asset(action='get', uri='{{session_data}}', include='full')

          Extract structured data for comic strip creation:
```

This means the research step now loads pre-gathered data from the discover step's asset instead of reading a raw file path. It no longer references `session_file` or `source` directly.

**Step 2: Verify the edit**

Run: `grep -A 5 'id: "research"' recipes/session-to-comic.yaml | head -8`

Expected: You see `id: "research"`, then `agent: "stories:story-researcher"`, then `prompt: |`, then `Analyze the session data at: {{session_data}}`, then the `comic_asset(action='get'...)` line.

**Step 3: Commit**

```bash
cd amplifier-bundle-comic-strips
git add recipes/session-to-comic.yaml
git commit -m "change: research step consumes session_data URI from discover step"
```

---

### Task 4: Update init-project step metadata

**Files:**
- Modify: `recipes/session-to-comic.yaml` (the init-project step prompt, line 274)

**Step 1: Add source to the metadata dict**

Find this line in the init-project step prompt (line 274):

```
          comic_project(action='create_issue', project='{{project_name}}', title='{{issue_title}}', metadata={"session_file": "{{session_file}}", "style": "{{style}}", "created_by": "session-to-comic recipe v7.4.0", "saga_issue": "{{saga_issue}}", "previous_issue_id": "{{previous_issue_id}}"})
```

Replace it with:

```
          comic_project(action='create_issue', project='{{project_name}}', title='{{issue_title}}', metadata={"source": "{{source}}", "session_file": "{{session_file}}", "style": "{{style}}", "created_by": "session-to-comic recipe v7.7.0", "saga_issue": "{{saga_issue}}", "previous_issue_id": "{{previous_issue_id}}"})
```

Two changes: (1) added `"source": "{{source}}"` at the start of the metadata dict, (2) bumped the `created_by` version from `v7.4.0` to `v7.7.0`.

**Step 2: Verify the edit**

Run: `grep 'create_issue' recipes/session-to-comic.yaml`

Expected: The metadata dict starts with `"source": "{{source}}", "session_file": "{{session_file}}"` and the `created_by` shows `v7.7.0`.

**Step 3: Commit**

```bash
cd amplifier-bundle-comic-strips
git add recipes/session-to-comic.yaml
git commit -m "change: init-project metadata includes source alongside session_file"
```

---

### Task 5: Recipe changelog and version bump

**Files:**
- Modify: `recipes/session-to-comic.yaml` (lines 3 and 10–11)

**Step 1: Bump the version**

Find line 3:

```yaml
version: "7.6.0"
```

Replace with:

```yaml
version: "7.7.0"
```

**Step 2: Add changelog entry**

Find lines 10–11:

```
#
# v7.6.0 (2026-03-05):
```

Insert the new changelog entry **before** the existing v7.6.0 entry. Replace those two lines with:

```
#
# v7.7.0 (2026-03-06):
#   - FEAT: Add flexible source input. New context variable `source` accepts
#     project names, session IDs, file paths, descriptive phrases, or any
#     combination. The stories:story-researcher agent discovers and consolidates
#     session data using its native tools (git/gh CLI, grep, delegation).
#   - FEAT: Add discover-sessions step (Step 0a) between init-project and
#     research. Resolves {{source}} to consolidated session data stored as a
#     comic asset. Returns a comic:// URI consumed by the research step.
#   - CHANGE: research step now consumes {{session_data}} URI from the discover
#     step instead of reading {{session_file}} directly. Research loads
#     pre-gathered data via comic_asset(action='get').
#   - CHANGE: session_file context variable deprecated. Still accepted as a
#     backward-compatible alias — if source is empty and session_file is
#     provided, the discover step uses session_file instead.
#   - CHANGE: init-project metadata now includes source alongside session_file.
#
# v7.6.0 (2026-03-05):
```

**Step 3: Verify the edit**

Run: `head -30 recipes/session-to-comic.yaml`

Expected: `version: "7.7.0"` on line 3. Changelog starts with `v7.7.0 (2026-03-06)` entry with FEAT and CHANGE items, followed by the existing `v7.6.0` entry.

**Step 4: Commit**

```bash
cd amplifier-bundle-comic-strips
git add recipes/session-to-comic.yaml
git commit -m "chore: bump recipe to v7.7.0, add changelog for flexible source input"
```

---

### Task 6: Update pipeline-flow.dot

**Files:**
- Modify: `docs/diagrams/pipeline-flow.dot` (lines 16, 20–27, 44–53, 100)

**Step 1: Update the title version**

Find line 16:

```
  label=<<B><FONT POINT-SIZE="16">Comic Generation Pipeline v7.6.0</FONT></B>>;
```

Replace with:

```
  label=<<B><FONT POINT-SIZE="16">Comic Generation Pipeline v7.7.0</FONT></B>>;
```

**Step 2: Update the input node**

Find the input node (lines 20–27):

```dot
  input [
    label=<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0">
      <TR><TD><B>events.jsonl</B></TD></TR>
      <TR><TD><FONT POINT-SIZE="9" COLOR="#666666">Amplifier session log</FONT></TD></TR>
    </TABLE>>,
    shape=note, style="filled", fillcolor="#E8F4FD", color="#90CAF9",
    width=2.0
  ];
```

Replace with:

```dot
  input [
    label=<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0">
      <TR><TD><B>{{source}}</B></TD></TR>
      <TR><TD><FONT POINT-SIZE="9" COLOR="#666666">project name, session ID(s),</FONT></TD></TR>
      <TR><TD><FONT POINT-SIZE="9" COLOR="#666666">file path(s), or description</FONT></TD></TR>
    </TABLE>>,
    shape=note, style="filled", fillcolor="#E8F4FD", color="#90CAF9",
    width=2.2
  ];
```

**Step 3: Add the discover_sessions node**

Find the end of the `init` node (line 43: `];`) and the beginning of the `research` node (line 45: `research [`).

Insert the following node **between** them — after line 43 and before line 45:

```dot

    discover_sessions [
      label=<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="2">
        <TR><TD><B>0a. Discover Sessions</B></TD></TR>
        <TR><TD><FONT POINT-SIZE="9" COLOR="#1565C0">stories:story-researcher</FONT></TD></TR>
        <TR><TD><FONT POINT-SIZE="8" COLOR="#666666">resolves {{source}} to session data</FONT></TD></TR>
      </TABLE>>,
      shape=box, style="rounded,filled", fillcolor="#E3F2FD", color="#90CAF9",
      width=2.4
    ];

```

**Step 4: Update the edge chain**

Find line 100:

```dot
    init -> research -> style_curation -> storyboard -> validate_storyboard -> update_title [color="#90CAF9"];
```

Replace with:

```dot
    init -> discover_sessions -> research -> style_curation -> storyboard -> validate_storyboard -> update_title [color="#90CAF9"];
```

**Step 5: Add a data flow annotation for the discover step**

Find the existing `storyboard_data` annotation node (line 104, starts with `storyboard_data [`). Insert the following **before** it (before line 103):

```dot
  // Data flow annotation (discover step)
  discover_data [
    label=<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="2">
      <TR><TD><FONT POINT-SIZE="8" COLOR="#2E7D32"><B>Session discovery:</B></FONT></TD></TR>
      <TR><TD><FONT POINT-SIZE="8" COLOR="#2E7D32">{{source}} → discover-sessions → {{session_data}} URI</FONT></TD></TR>
    </TABLE>>,
    shape=none, margin=0
  ];

```

**Step 6: Verify the edit**

Run: `grep -n 'discover_sessions\|v7.7.0\|source' docs/diagrams/pipeline-flow.dot`

Expected: You see the version label with `v7.7.0`, the `discover_sessions` node, the `{{source}}` in the input node, and the updated edge chain with `discover_sessions` between `init` and `research`.

**Step 7: Commit**

```bash
cd amplifier-bundle-comic-strips
git add docs/diagrams/pipeline-flow.dot
git commit -m "docs: add discover_sessions node to pipeline-flow.dot, bump to v7.7.0"
```

---

### Task 7: Update comic-instructions.md Cross-Agent Data Flow

**Files:**
- Modify: `context/comic-instructions.md` (lines 158–163)

**Step 1: Update the section intro and add stage 0**

Find lines 158–162:

```markdown
## Cross-Agent Data Flow

The comic creation pipeline passes data between agents in six stages:

1. **Research JSON** - The story-researcher agent outputs structured research JSON containing session events, metrics, and narrative arcs extracted from source material.
```

Replace with:

```markdown
## Cross-Agent Data Flow

The comic creation pipeline passes data between agents in seven stages:

0. **Session Discovery** *(new in v7.7.0)* - The `discover-sessions` step receives a flexible `{{source}}` input — a project name, session ID(s), file path(s), or descriptive phrase. The `stories:story-researcher` agent discovers and consolidates the relevant Amplifier session data using its native tools (git/gh CLI, grep, `read_file`, delegation to `foundation:explorer`). It stores the consolidated material as a comic asset and returns a `comic://` URI (`{{session_data}}`). This decouples the pipeline from Amplifier's internal storage layout — the researcher explores creatively rather than following hardcoded paths.
1. **Research JSON** - The story-researcher agent loads the consolidated session data via `comic_asset(action='get', uri='{{session_data}}')` and extracts structured research JSON containing session events, metrics, and narrative arcs for comic creation.
```

**Step 2: Verify the edit**

Run: `grep -n 'Session Discovery\|seven stages\|session_data' context/comic-instructions.md`

Expected: You see "seven stages", the new "Session Discovery" stage 0, and the updated stage 1 referencing `{{session_data}}`.

**Step 3: Commit**

```bash
cd amplifier-bundle-comic-strips
git add context/comic-instructions.md
git commit -m "docs: add session discovery stage to Cross-Agent Data Flow in comic-instructions"
```

---

### Task 8: Update examples/README.md invocation examples

**Files:**
- Modify: `examples/README.md` (lines 26–36, 151–156, 293–308, 441–446)

**Step 1: Update the sin-city invocation examples (lines 26–36)**

Find the sin-city CLI invocation block (lines 26–29):

```
amplifier tool invoke recipes \
  operation=execute \
  recipe_path=amplifier-bundle-comic-strips/recipes/session-to-comic.yaml \
  context='{"session_file": "combined-sessions.jsonl", "style": "sin-city", "output_name": "sin-city-comic", "project_name": "sin-city-e2e"}'
```

Replace with:

```
amplifier tool invoke recipes \
  operation=execute \
  recipe_path=amplifier-bundle-comic-strips/recipes/session-to-comic.yaml \
  context='{"source": "comic-strip-bundle", "style": "sin-city", "output_name": "sin-city-comic", "project_name": "sin-city-e2e"}'
```

Then find the conversational invocation (lines 35–36):

```
execute session-to-comic with session_file=combined-sessions.jsonl style=sin-city output_name=sin-city-comic project_name=sin-city-e2e
```

Replace with:

```
execute session-to-comic with source=comic-strip-bundle style=sin-city output_name=sin-city-comic project_name=sin-city-e2e
```

**Step 2: Update the JJK invocation example (line 155)**

Find:

```
execute session-to-comic with session_file=combined-sessions.jsonl style=jujutsu-kaisen output_name=comic-strips-bundle-creation-jjk project_name=jjk-e2e
```

Replace with:

```
execute session-to-comic with source=comic-strip-bundle style=jujutsu-kaisen output_name=comic-strips-bundle-creation-jjk project_name=jjk-e2e
```

**Step 3: Update the Ghibli invocation example (lines 297–308)**

Find the multi-line invocation starting with:

```
execute session-to-comic with \
  session_file=~/.amplifier/projects/-home-dicolomb-context-intelligence-second-pass/sessions/59cb8e3f-48a2-422a-867d-f78a98b2a75b/events.jsonl \
```

Replace the first two lines of that invocation with:

```
execute session-to-comic with \
  source="the context-intelligence-second-pass project" \
```

Leave all the remaining parameters (`style=ghibli \`, `output_name=...`, etc.) unchanged.

**Step 4: Update the Naruto invocation example (lines 441–446)**

Find the naruto CLI invocation:

```
amplifier tool invoke recipes \
  operation=execute \
  recipe_path=@comic-strips:recipes/session-to-comic.yaml \
  context='{"session_file": "/workspace/test-session.jsonl", "style": "naruto", "output_name": "e2e-layout-test", "project_name": "e2e-layout-validation", "max_pages": "3", "max_characters": "4"}'
```

Replace with:

```
amplifier tool invoke recipes \
  operation=execute \
  recipe_path=@comic-strips:recipes/session-to-comic.yaml \
  context='{"source": "/workspace/test-session.jsonl", "style": "naruto", "output_name": "e2e-layout-test", "project_name": "e2e-layout-validation", "max_pages": "3", "max_characters": "4"}'
```

**Step 5: Verify the edits**

Run: `grep -n 'session_file\|source=' examples/README.md | head -20`

Expected: All invocation examples now use `source=` instead of `session_file=`. There should be zero occurrences of `session_file=` in invocation commands. (The word "session_file" may still appear in the step descriptions from "How it was created" sections — that's fine, those describe historical runs.)

**Step 6: Commit**

```bash
cd amplifier-bundle-comic-strips
git add examples/README.md
git commit -m "docs: update example invocations from session_file to source"
```

---

### Task 9: Validate the recipe

**Files:**
- Read-only: `recipes/session-to-comic.yaml`

**Step 1: Run recipe validation**

```bash
amplifier tool invoke recipes operation=validate recipe_path=amplifier-bundle-comic-strips/recipes/session-to-comic.yaml
```

Or if running from inside the bundle directory:

```bash
cd amplifier-bundle-comic-strips
amplifier tool invoke recipes operation=validate recipe_path=recipes/session-to-comic.yaml
```

Expected: Validation passes with no errors. The recipe engine confirms the YAML structure is valid, all step IDs are unique, all output variables are referenced correctly, and the staged structure is well-formed.

**Step 2: Quick sanity check on the full recipe**

```bash
grep -c 'session_file' recipes/session-to-comic.yaml
```

Expected: A small number (3–5 occurrences). These should be:
1. The `session_file: ""` context variable (deprecated alias)
2. The `{{session_file}}` reference in the discover-sessions prompt (backward compat)
3. The `"session_file": "{{session_file}}"` in the init-project metadata dict

There should be **zero** occurrences of `session_file` in the research step prompt. Verify:

```bash
grep -A 3 'id: "research"' recipes/session-to-comic.yaml
```

Expected: The research step prompt references `{{session_data}}`, not `{{session_file}}`.

**Step 3: Final commit (if any fixes were needed)**

If validation revealed issues and you fixed them:

```bash
cd amplifier-bundle-comic-strips
git add recipes/session-to-comic.yaml
git commit -m "fix: address recipe validation feedback"
```

If validation passed cleanly, no commit needed — you're done!
