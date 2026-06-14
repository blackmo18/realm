---
name: realm-plan
description: >
  Free-form collaborative ideation canvas. Optional chain syntax (research->design->plan) defines
  initial section generation order — not a hard pipeline. One free-form loop after generation.
  User drives: add, update, skip any section. Save/resume across sessions via categorized vault
  work/ dirs (research/, designs/, plans/, scaffolds/). Finalizes to manifest-draft.md for
  /realm-manifest only on explicit user acceptance.
origin: realm
---

# realm-plan

Think on canvas → collaborate freely → finalize → vault.

## Syntax

```bash
# No chain — blank canvas, user adds sections as needed
/realm-plan "auth refactor"

# Single section starter
/realm-plan plan "auth refactor"
/realm-plan design "API versioning"
/realm-plan investigate "distributed caching bug"
/realm-plan deep-research "event sourcing tradeoffs"
/realm-plan scaffold "PaymentService"

# Chain — generation hint only, not a hard pipeline
/realm-plan deep-research->design->plan "auth refactor"
/realm-plan investigate->plan "caching bug"
/realm-plan scaffold->design->plan "PaymentService"
/realm-plan research->design "new queue architecture"

# Resume saved work (category/slug)
/realm-plan resume plans/auth-refactor
/realm-plan resume designs/api-versioning design   # jump to specific section on open
/realm-plan resume research/event-sourcing

# List in-progress work
/realm-plan list
/realm-plan list plans       # filter by category
/realm-plan list designs

# Flags
/realm-plan design --ui "onboarding flow"       # adds a11y considerations
/realm-plan plan --feature "notifications"       # scope to feature
```

## Core Concept

**Chain syntax = generation hint only.**

`research->design->plan` means: spawn these agents in this order to populate sections with context from prior sections. That is all. After generation, the loop is free-form. There are no gates, no required accepts, no locked sections. The user owns the canvas.

```
/realm-plan deep-research->design->plan "topic"
  │
  ├─ vault pre-load (realm-agent-query, once)
  ├─ deep-research agent → research.md section (standalone vault file)
  ├─ design agent (sees research output) → design.md section
  ├─ plan agent (sees research + design) → plan.md section
  │
  └─ ONE free-form loop opens on full canvas
       user drives — no gates, no sequence enforcement
       any section: update, expand, regenerate, skip, ignore
       save at any point → persists to vault/work/
       resume next session → picks up exactly here
       finalize → promotes sections to proper vault dirs
```

## Section Types

| Keyword | Agent | Generates |
|---------|-------|-----------|
| `plan` | `planner` | Goals, risks, phases, open decisions |
| `investigate` | `cavecrew-investigator` | file:line map, call chains, vault drift — local codebase |
| `deep-research` / `research` | ECC `deep-research` (firecrawl + exa) | Findings, sources, implications — external web/docs |
| `scaffold` | `code-architect` | Boundary, interface, data shapes, file list, build order |
| `design` | `architect` | Options, recommendation, consequences, ADR stub |

`investigate` = local codebase, symbol lookup, bug tracing, read-only.
`deep-research` / `research` = external world: web, docs, papers, competitive analysis.

## Vault Persistence

Working canvas persists in vault under `work/`, categorized by intent:

```
vault/projects/<slug>/
├── decisions/
├── systems/
├── ...existing dirs...
└── work/
    ├── index.md                                ← auto-maintained master list (Obsidian-browsable)
    ├── research/                               ← learning / investigating something
    │   └── <slug>/
    │       ├── _meta.md
    │       └── research.md
    ├── designs/                                ← deciding / architecting something
    │   └── <slug>/
    │       ├── _meta.md
    │       ├── research.md                     # (if chain included research)
    │       └── design.md
    ├── plans/                                  ← planning to build something
    │   └── <slug>/
    │       ├── _meta.md
    │       ├── research.md                     # (if chain included research)
    │       ├── design.md                       # (if chain included design)
    │       └── plan.md
    └── scaffolds/                              ← blueprinting a new module / service
        └── <slug>/
            ├── _meta.md
            ├── design.md                       # (if chain included design)
            └── scaffold.md
```

**Category from terminal mode (last mode in chain):**

| Terminal mode | Category |
|---|---|
| `plan` | `plans/` |
| `design` | `designs/` |
| `scaffold` | `scaffolds/` |
| `research` / `investigate` only | `research/` |
| No chain, no mode | `plans/` (default) |

Examples: `research->design->plan` → `plans/`. `research->design` → `designs/`. `investigate` → `research/`. `scaffold->design` → `designs/`.

Slug = kebab-case from topic, no date prefix. Date lives in `_meta.md` only.

`work/` is vault-resident: visible in Obsidian, queryable by `/realm-recall`, syncs across machines.
Nothing in `work/` is promoted to a real vault node until `finalize`.

### `work/index.md` format (auto-maintained)

```markdown
# Work Index

## plans
| slug | topic | sections | status | updated |
|------|-------|----------|--------|---------|
| [[plans/auth-jwt-refactor/_meta\|auth-jwt-refactor]] | auth JWT refactor | research ✓ design ✓ plan ✓ | in-progress | 2026-06-13 |

## designs
| slug | topic | sections | status | updated |
|------|-------|----------|--------|---------|
| [[designs/api-versioning/_meta\|api-versioning]] | API versioning strategy | design ✓ | draft | 2026-06-12 |

## research
...

## scaffolds
...
```

### `_meta.md` format

```markdown
---
slug: <slug>
topic: "<topic>"
category: plans | designs | research | scaffolds
chain: <deep-research->design->plan | none>
status: draft | in-progress | finalized | abandoned
created: <ISO 8601>
updated: <ISO 8601>
---

## Sections
| Section | Status | Agent used |
|---------|--------|------------|
| research | done | deep-research |
| design | in-progress | architect |
| plan | pending | — |

## Notes
<free-form user notes, added during loop>
```

---

## Procedure

Read `_shared/realm-conventions.md` before executing.

### Step 0 — Guard check

1. Read `.realm/realm-state.json`. If missing: `No realm state. Run /realm-forge first.` STOP.
2. Load: `vaultPath`, `projectSlug`, `projectDir`.
3. Do NOT block on `phase.draftReady`. realm-plan is independent of the phase/manifest pipeline.

### Step 1 — Parse input

**Mode detection:**

- `resume <slug>` → skip to Step 1b (load existing work item)
- `list` → print all `work/` items with status, STOP
- `<chain> "<topic>"` → chain mode: parse `->` separated modes
- `<single-mode> "<topic>"` → single section
- `"<topic>"` only → blank canvas, no sections generated yet

**Chain parsing:**

```
"deep-research->design->plan" → stages = [deep-research, design, plan]
"research->plan"              → stages = [deep-research, plan]   (research = alias)
```

Aliases: `research` = `deep-research`, `investigate` = `investigate`

**Flags:** `--ui` (adds a11y to design/scaffold sections), `--feature <name>` (scope context)

**Slug:** kebab-case from topic. `"refactor auth to JWT"` → `auth-jwt-refactor`

**Category derivation:** inspect terminal (last) mode in chain:
- `plan` → `plans/`
- `design` → `designs/`
- `scaffold` → `scaffolds/`
- `research` / `investigate` only → `research/`
- No chain, no mode → `plans/` (default)

**Work item path:** `<projectDir>/work/<category>/<slug>/`

**Step 1b — Resume:**

Parse `resume <category>/<slug>` or `resume <slug>` (search all categories if no category given).
Load `<projectDir>/work/<category>/<slug>/` from vault.
Read `_meta.md` for section registry and chain.
Print: `realm-plan: resuming "<topic>" [<category>] — <N> sections, status: <status>`
Skip to Step 4 (open loop on loaded canvas).

### Step 2 — Pre-load vault context (one agent spawn)

Spawn `realm-agent-query` recall mode for topic. Collect output.

- Nodes found → use as context for all section generation and pass to loop.
- No nodes → note "no prior vault context", continue.
- Unavailable → note "vault unavailable", continue.

### Step 3 — Initialize work item

Check `<projectDir>/work/<category>/<slug>/` for existing item. If found:
- Print: `Existing work found: work/<category>/<slug>/. Resume? (y/n):`
- `y` → load and skip to Step 4
- `n` → create new with `-2` suffix on slug

Create `<projectDir>/work/<category>/<slug>/`:
- Write `_meta.md` with category, chain, initial section registry
- Create section files listed in chain (or empty canvas if no chain)

Update `work/index.md`: append row to `## <category>` table.

Print: `realm-plan: canvas="<topic>"  category=<category>  chain=<chain | none>`

### Step 3.5 — Generate sections (chain or single)

For each stage in chain order (or single mode):

1. Build prompt with: vault context (Step 2) + all previously generated section content
2. Spawn agent (see prompts below)
3. Write output to `<projectDir>/work/<slug>/<section>.md`
4. Update `_meta.md` section registry: `status: done`
5. Print one-line confirmation: `✓ <section> generated`

No checkpoints, no gates between sections. Generate all, then open loop.

**If `deep-research` mode:** Requires firecrawl MCP (`firecrawl_search`, `firecrawl_scrape`) or exa MCP (`web_search_exa`). If neither available: `deep-research requires firecrawl or exa MCP. Configure in ~/.claude.json.` STOP.

---

#### Section: plan → spawn `planner`

```
Create implementation plan for: "<topic>"

Vault context (existing decisions — do not re-litigate):
<Step 2 output>

Prior sections from this canvas:
<all generated section content so far>

Produce:
## Goals
  What this achieves. What it explicitly does not.

## Risks & Dependencies
  Blockers, unknowns, external dependencies.

## Phases
  Phase breakdown with tasks per phase.

## Open Decisions
  Questions needing an ADR before implementation can proceed.

Return structured markdown only. Write no files.
```

---

#### Section: investigate → spawn `cavecrew-investigator`

Token-efficient: caveman-compressed file:line output. Read-only, no suggestions.

```
Locate and map all code relevant to: "<topic>"
Project root: <projectRoot>

Vault context (existing decisions/ADRs — note any drift):
<Step 2 output>

Return:
1. file:line table — every symbol, function, class, pattern directly involved
2. Call chain — entry → handler → dependency
3. Suspicious locations — potential bug sources, edge cases, unexpected behavior
4. Vault drift — mismatch between vault docs and actual code

Format: path:line — `symbol` — one-line note
Read-only. No fixes. No suggestions.
```

---

#### Section: deep-research → ECC deep-research skill (external web)

```
Investigate externally: "<topic>"

Vault context (existing knowledge — skip already-documented areas):
<Step 2 output>

Prior sections:
<all generated section content so far>

Workflow:
1. Break topic into 3-5 sub-questions. Use vault context to skip known areas.
2. For each sub-question: search with available MCPs (firecrawl_search / web_search_exa).
   Use 2-3 keyword variations per sub-question.
3. Deep-read 3-5 key sources in full (firecrawl_scrape / crawling_exa).
4. Synthesize findings. Every claim needs a source citation.

Output:
## Research Questions
<3-5 sub-questions>

## Vault Context (existing — not re-investigated)
<existing decisions/discoveries | none>

## Findings
### <Sub-question 1>
<findings with inline citations ([Source](url))>
...

## Key Takeaways
<actionable insights>

## Implications for Project
<what this means for decisions, architecture, implementation>

## Sources
1. [Title](url) — one-line summary

## Gaps
<sub-questions where good sources not found>

Quality rules: every claim needs source. Cross-reference single-source claims as unverified.
Prefer sources from last 12 months. Separate fact from inference.
```

---

#### Section: scaffold → spawn `code-architect`

```
Design architecture blueprint for: "<topic>"

Vault context (existing systems/classes — do not duplicate):
<Step 2 output>

Prior sections:
<all generated section content so far>

Produce:
## Boundary
  What this service/module owns. What it does not.

## Interface
  Public methods/API surface with signatures.

## Data Shapes
  Inputs, outputs, key types.

## Dependencies
  What this depends on from existing systems (reference vault context).

## Files
  file path → responsibility (one line each).

## Build Order
  Ordered task list: stub → implement → test.

Return structured markdown only. Write no files.
```

---

#### Section: design → spawn `architect`

```
System design for: "<topic>"

Vault context (existing decisions — do not re-litigate):
<Step 2 output>

Prior sections:
<all generated section content so far>

Produce:
## Problem
  Clear statement of what needs decided and why.

## Options
  2-3 options with trade-offs. No more.

## Recommendation
  Chosen option + full rationale.

## Consequences
  What gets better. What gets harder.

## Architecture Impact
  Changes to architecture.md: new rows, updated service boundaries.

## Decision Record
  Ready-to-vault ADR stub.

Return structured markdown only. Write no files.
```

If `--ui` flag: append — `Also produce: ## Accessibility covering WCAG 2.2 considerations, keyboard navigation, screen-reader constraints.`

---

### Step 4 — Free-form collaboration loop (BLOCKING, no iteration limit)

Present full canvas:

```
realm-plan: canvas open — "<topic>"
work: work/<category>/<slug>/
──────────────────────────────────────────────────────────
## Research
<research.md content | (empty — use "add section: research" to generate)>

## Design
<design.md content | ...>

## Plan
<plan.md content | ...>
──────────────────────────────────────────────────────────
sections: research ✓  design ✓  plan ✓
vault context: <N nodes | none>

Commands: update · add section · skip · dig deeper · alternatives · save · finalize · discard
──────────────────────────────────────────────────────────
```

**Loop commands — wait for user input every turn, never auto-advance:**

| Input | Action |
|-------|--------|
| `update: <section> — <feedback>` | Re-run section agent with feedback + current content. Update section file. |
| `add section: <mode>` | Generate new section using mode agent. Append to canvas. Update `_meta.md`. |
| `skip: <section>` | Mark section as skipped in `_meta.md`. Remove from canvas display. |
| `dig deeper: <section>` | Expand that section inline. Update section file. |
| `alternatives: <section>` | Generate alternative approaches, append to section file. |
| `add: <constraint>` | Incorporate constraint into relevant sections. Update affected files. |
| `re-run: <section>` | Regenerate section from scratch with current vault context + all other sections. |
| `show <section>` | Print that section's current content in full. |
| `show all` | Print full canvas. |
| `show nodes` | List planned vault nodes and target paths. |
| `save` | Write all section files to vault `work/`. Update `_meta.md` status: `in-progress`. Print path. STAY IN LOOP. |
| `finalize` | Exit loop → Step 5. |
| `discard` | Delete `work/<category>/<slug>/`. Update `work/index.md`. Print `Canvas discarded. Vault unchanged.` STOP. |
| Any other text | Free-form feedback: identify affected sections, update accordingly. Summarize changes. |

After every change: update `updated` timestamp in `_meta.md`.
`save` persists to vault but does NOT finalize. User can close session and resume later.
Never write to `manifest-draft.md` during loop.

### Step 5 — Finalize: classify and promote

On `finalize`:

**Classify each section by content signal:**

| Section | Signal | Node type | Vault dir |
|---|---|---|---|
| design | "decided to", "instead of", "because", recommendation + rationale | `decision` | `decisions/` |
| design | new service/integration boundary | `system` | `systems/` |
| scaffold | class/struct with interface | `class` | `classes/` |
| scaffold | function/method spec | `function` | `functions/` |
| research / investigate | finding, perf note, drift, unexpected behavior | `discovery` | `discoveries/` |
| plan | build order, task list | session task block | `sessions/` |
| any | architecture.md rows/boundaries changed | architecture update | `architecture.md` |

**Promotion by category (default mapping when signal is ambiguous):**

| Category | Primary destination |
|---|---|
| `plans/` | `sessions/` (task block) + any `decisions/` extracted |
| `designs/` | `decisions/` (ADR) + `architecture.md` update |
| `research/` | `discoveries/` |
| `scaffolds/` | `classes/` + `systems/` stubs |

**ADR quality check (before classifying):**

For each `design` section being promoted to a `decision` node, verify it contains all 4 subsections:
- `## Context` (or `Context:`)
- `## Decision` (or `Decision:`)
- `## Rejected alternatives` (or `Alternatives:`)
- `## Consequences` (or `Consequences:`)

If any missing → **do not write draft**. Print:
```
ADR quality check failed — <slug>

  missing sections: <list>

  Fix in loop then re-run finalize.
  Commands: update: design — <feedback>  |  dig deeper: design
```
Return user to Step 4 loop. Do NOT close the canvas.

---

Convert section files → `manifest-draft.md` format (per realm-conventions schema).

**For every decision node produced:**

1. Add `source_plan: work/<category>/<slug>` to the ADR frontmatter.
2. Append an `## Origin` section to the ADR body:
   ```markdown
   ## Origin
   Promoted from planning canvas [[work/<category>/<slug>/_meta|<topic>]].
   ```
3. Collect the node path (e.g. `decisions/<adr-slug>.md`) into a `promoted_to` list.

**After all nodes are classified and quality check passes:**

1. Update `<projectDir>/work/<category>/<slug>/_meta.md`:
   - Set `status: finalized`
   - Add/replace `promoted_to:` block:
     ```yaml
     promoted_to:
       - decisions/<adr-slug>.md
       - systems/<system-slug>.md   # if any
     ```

2. Write draft to canvas-local path:
   `<projectDir>/work/<category>/<slug>/manifest-draft.md`
   (NOT `.realm/manifest-draft.md` — draft stays local to this canvas)

3. Push to `realm-state.json` `pendingDrafts`:
   ```json
   {
     "source": "plan",
     "slug": "work/<category>/<slug>",
     "path": "work/<category>/<slug>/manifest-draft.md",
     "created": "<ISO 8601>"
   }
   ```

### Step 6 — Print summary

```
realm-plan finalized

  topic:              "<topic>"
  chain:              <chain | none>
  vault context used: <yes — N nodes | none>
  sections:           <list>

  nodes staged:
    decisions:        <N>  → decisions/<slug>.md  [source_plan linked]
    systems:          <N>  → systems/<slug>.md
    classes:          <N>  → classes/<slug>.md
    functions:        <N>  → functions/<slug>.md
    discoveries:      <N>  → discoveries/<date>-<slug>.md
    architecture:     <updated | unchanged>

  work item:  work/<category>/<slug>/   [status: finalized, promoted_to: <N> nodes]
  staged:     work/<category>/<slug>/manifest-draft.md   ← local to this canvas

  next: /realm-manifest to commit  |  /realm-manifest (no arg) to see all pending
```

---

## realm-plan list output

```
realm-plan: work items

  plans/
    auth-jwt-refactor       "refactor auth to JWT"     research ✓ design ✓ plan ✓   in-progress   2026-06-13
    caching-strategy        "distributed caching"      investigate ✓ plan ✓          finalized     2026-06-08

  designs/
    api-versioning          "API versioning strategy"  design ✓                      draft         2026-06-12

  scaffolds/
    payment-service         "PaymentService"           scaffold ✓                    draft         2026-06-10

  research/
    event-sourcing          "event sourcing tradeoffs" research ✓                    in-progress   2026-06-11

  resume: /realm-plan resume <category>/<slug>
```

---

## Recall integration

Work items are vault-resident and queryable:

```bash
/realm-recall work:plans/auth-jwt-refactor          # full canvas
/realm-recall work:designs/api-versioning design    # just design section
/realm-recall "auth design"                         # searches work/ + decisions/ + systems/
/realm-recall work:research/event-sourcing          # research findings
```

realm-agent-query Step 2 pre-load searches `work/` for matching topic across all categories (status: in-progress or finalized).
