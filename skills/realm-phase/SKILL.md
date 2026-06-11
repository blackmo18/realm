---
name: realm-phase
description: >
  Dry-run repo mapping step in the realm pipeline. Full mode: scans the whole codebase using cavecrew-investigator. Targeted mode (/realm-phase function:X or class:X): scans only the named entity's source file — 10-20x cheaper. Caveman-compresses findings, diffs repo reality against existing vault docs, drafts ADR candidates and doc updates, and writes a staged manifest-draft.md to .realm/. Never writes to the Obsidian vault. Must run after realm-forge and before realm-manifest. Shows a gap map for review before committing.
origin: realm
---

# realm-phase

Scan, compress, stage — without touching vault. Second skill in realm pipeline.

## Modes

| Mode | Trigger | Cost | When |
|------|---------|------|------|
| **Full** | `/realm-phase` | Full investigator scan | After milestones, big changes |
| **Targeted** | `/realm-phase function:validateUser` | Single-entity scan (~10-20x cheaper) | Changed one function/class |
| **Multi-target** | `/realm-phase function:X class:Y` | N-entity scan | Changed handful of entities |

## When to Use

| Trigger | Example |
|---|---|
| Before writing new docs | "phase the project", `/realm-phase` |
| Repo diverged from vault | "map realm", "update realm draft" |
| Changed one function/class | `/realm-phase function:validateUser` |
| Want to review before committing | Generates manifest-draft.md for inspection |

## When NOT to Use

- `.realm/realm-state.json` missing → `/realm-forge` first (hard guard)
- Minor update, no review needed → `/realm-flourish` (auto-commits minor diffs)
- Check state without scanning → `/realm-status`
- Write staged draft to vault → `/realm-manifest`

---

## Procedure

Read `_shared/realm-conventions.md` for schema, taxonomy, compression policy before executing.

**CRITICAL: This skill writes ONLY to `.realm/`. Zero vault writes.**

### Step 0 — Guard check + mode detection

1. Read `.realm/realm-state.json` from project root.
2. If missing: print `No realm state found. Run /realm-forge first.` and STOP.
3. Load: `vaultPath`, `projectSlug`, `projectDir`, existing `docs` registry.
4. Parse args: check for `function:X`, `class:X`, `system:X` patterns in invocation.
   - If found: set **targeted mode**. Collect target list (type + id pairs).
   - If none: set **full mode**.
5. Print: `Mode: <full|targeted>  Targets: <list or "all">`.

### Targeted Mode (when args contain entity specifiers)

Skip Steps 1–2 of full procedure.

**Step T1 — Locate target source files**

For each target:
1. Search repo for source file. Heuristics:
   - `function:validateUser` → grep for `function validateUser`, `def validate_user`, `func validateUser` etc.
   - `class:UserService` → grep for `class UserService`, `struct UserService`, etc.
   - Multiple hits: pick primary definition (not test files).
2. If not found: print `Cannot locate source for <target>. Run full /realm-phase.` and STOP for that target.

**Step T2 — Spawn targeted cavecrew-investigator**

Spawn investigator with narrowed prompt:

```
Analyze ONLY these entities in this repo:
<list of target functions/classes>

For each, extract:
- Full signature (params + return type)
- Responsibility (one-liner)
- Dependencies ([[links]])
- Callers / dependents (if findable)
- Any inline architectural comments ("DO NOT", "invariant", "perf note")
- Performance characteristics if benchmarks/comments present

Output: caveman-compressed, one block per entity.
```

**Step T3 — Diff targeted entities vs vault**

For each target, check if node file exists (`functions/<id>.md`, `classes/<id>.md`).
- Exists: diff investigator output vs node content.
- Missing: plan new node.

**Step T4 — Draft targeted manifest**

Write `.realm/manifest-draft.md` with targeted node diffs only (no architecture/overview update unless diff warrants it). Set `mode: targeted` in Meta block.

**Step T5 — Update realm-state.json and print gap map**

Print:
```
realm-phase complete  [targeted]
  entities:  <list of targets>

GAP MAP
  new docs planned:  <N>
  docs to update:    <N>

  draft staged at: .realm/manifest-draft.md
  cost:            targeted scan (1 investigator call per <N> files)

Review, then run /realm-manifest to write to vault.
(Or run /realm-flourish to auto-commit if changes are minor.)
```

**STOP after Step T5 — do not continue to full mode steps.**

---

### Full Mode

### Step 1 — Inventory existing vault docs

Read `<projectDir>/` recursively. Build list of existing `.md` files relative to `projectDir`. Note:
- `committed` in state registry
- On disk but `status: planned` (previous phase aborted before manifest)
- On disk but NOT in registry (orphaned — add as `committed`)

Cross-check registry: docs marked `committed` but deleted from disk → mark `stale`.

### Step 2 — Spawn cavecrew-investigator to map repo

Spawn `cavecrew-investigator` subagent with prompt:

```
Map this codebase for Obsidian node-graph documentation. Find and compress:

1. SERVICES / CLASSES — each major class/service: name, responsibility, public methods, key deps
2. FUNCTIONS / UTILITIES — critical standalone functions: name, signature, responsibility, who calls it
3. EVENTS / COMMUNICATION — event names, emitters, listeners; API routes; patterns
4. DATA LAYER — DB tables/collections, Redis patterns, schema relationships
5. CONFIGURATION — env vars, config files, safety bounds, named constraints
6. TECH STACK — languages, frameworks, libraries, build/test tools
7. ENTRY POINTS — bootstrap files, CLI entry, init sequences
8. ARCHITECTURAL PATTERNS — decision evidence: "we do X instead of Y because...", naming conventions, guards
9. EXISTING DOCS — list all .md files, README*, IMPLEMENTATION_PLAN*, *.plan.md

Output format: caveman-compressed, grouped by category. For classes/functions, include caveman one-liners that could be node frontmatter:
  - Function: signature + responsibility + typical call frequency/perf
  - Class: responsibility + key deps + typical users
  - Decision signal: code pattern with rationale

No line numbers. File paths where relevant for classes and functions.
```

### Step 3 — Load existing vault doc summaries

For each `committed` doc relevant to scan (overview, architecture, decisions/), read first 50 lines. Only these three needed for gap analysis.

### Step 4 — Diff: repo vs vault

Using investigator output (Step 2) and vault summaries (Step 3), identify gaps:

**architecture.md gaps:** services/events/schema in code not in vault architecture doc.

**overview.md gaps:** milestones done in code but incomplete in vault; new stack deps.

**New node candidates:**

- **Function nodes:** critical standalone functions/methods not in vault. High-call-frequency paths, cross-service utilities, perf-critical code.
- **Class nodes:** major services/modules. Core services, utility libs, domain-specific classes.
- **Decision nodes:** architectural choice signals:
  - Comments: "DO NOT change this because...", "no direct service calls — use event bus"
  - Config bounds (`validation_min`, `validation_max`) encoding rules
  - Anti-pattern avoidance with past-bug refs
  - Files named `*Safeguard*`, `*Guard*`, `*Validator*`, `*Strict*`
- **Discovery nodes:** tech choices, perf characteristics, architectural constraints worth logging.
- **Session log:** always plan one entry (what scanned, candidates found).

### Step 5 — Draft the manifest

Write `.realm/manifest-draft.md` using format from `_shared/realm-conventions.md`:

```
# Realm Manifest Draft — <YYYY-MM-DD>

## Meta
slug: <projectSlug>
phase-run: <ISO timestamp>
gap-summary: <1-line: N new functions, M new classes, K new decisions, L updates>

## Planned Node Documents

### decisions/<id>.md
status: new | update
---
---
id: <id>
type: decision
status: active
tags: [decision, ...]
---

# <Title>

Compressed: <one-liner>

## Full Decision
### Context
[...]
### Decision
[...]
### Consequences
[...]

## Implementation Locations
- [[ClassName]] — implements
- [[functionName]] — enforces

### functions/<id>.md
status: new
---
---
id: <id>
type: function
class: <className>
status: active
tags: [function, ...]
---

# <functionName>()

**Signature**: `<signature>`

Compressed: <one-liner about behavior + frequency + perf>

## Implementation
[...]

## Depends On
- [[OtherClass]]
- [[helper-function]]

## Called By
- [[ClassOrFunction]]

### classes/<id>.md
status: new
---
---
id: <id>
type: class
status: active
tags: [class, service, ...]
---

# <ClassName>

Compressed: <one-liner: responsibility + key deps + users>

## Methods
- `method1()` — [[#method1]]

## Dependencies
- [[OtherClass]]

## Dependents
- [[Consumer1]]

[repeat for each planned node]

## Updated Overview/Architecture (if diverged)
### overview.md
status: update
---
[milestones, tech stack updates only; preserve existing prose]

### architecture.md (if needed)
status: update
---
[new services/events as rows; don't rewrite existing tables]

## Session Log Entry
### sessions/<YYYY-MM-DD>-<topic>.md
status: new
---
<session log with ## Discovered / ## Decided / ## Changed / ## Next sections>
```

**Content rules:**
- Node files: full YAML frontmatter (id, type, status, tags, created, updated); Compressed one-liner; Full section.
- Wikilinks: `[[nodeId]]` for cross-references.
- Overview: only update milestones/stack if diverged; preserve existing.
- Architecture: append new rows; don't rewrite.
- Compression: caveman policy; preserve YAML, code blocks, tables, wikilinks.

### Step 6 — Update realm-state.json

Mutate and write:
- `phase.lastRun`: current ISO timestamp
- `phase.draftReady`: `true`
- `docs`: add planned docs with `status: "planned"`; stale detections → `status: "stale"`; leave `committed` unchanged

### Step 7 — Print gap map

```
realm-phase complete
  scanned:  <N services/modules> | <N events> | <N tables>

GAP MAP
  new docs planned:     <N>  (<list of relative paths>)
  docs to update:       <N>  (<list>)
  new ADR candidates:   <N>  (<list of titles>)
  vault unchanged:      <N> committed docs already current

  draft staged at: .realm/manifest-draft.md

Review the draft, then run /realm-manifest to write to vault.
```

Do NOT write to vault. If about to write to `<vaultPath>/`, stop and abort.
