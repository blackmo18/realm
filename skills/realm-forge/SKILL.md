---
name: realm-forge
description: >
  Bootstrap a project's Obsidian knowledge base and local realm state. Creates the vault directory structure (overview, architecture, decisions/, sessions/, templates), writes a .claude/CLAUDE.md project anchor, seeds .realm/realm-state.json, and adds .realm/ to .gitignore. Idempotent — safe to re-run; never overwrites existing vault docs. First step in the realm pipeline before realm-phase and realm-manifest.
origin: realm
---

# realm-forge

Bootstrap Obsidian knowledge base for current project. First skill in realm pipeline.

## When to Use

| Trigger | Example |
|---|---|
| First-time setup | "init realm", `/realm-forge` |
| Vault path not configured | "set up project knowledge base" |
| `.realm/realm-state.json` missing | Starting pipeline from scratch |
| Adding realm to project with existing Obsidian docs | Idempotent — detects existing docs |

## When NOT to Use

- Valid `realm-state.json` exists, want to re-scan → `/realm-phase`
- Want to write docs → `/realm-manifest` (after phase)
- Project initialized, state current → `/realm-status` to check

---

## Procedure

Read `_shared/realm-conventions.md` before executing. All taxonomy, schema, guard rules defined there.

### Step 1 — Resolve vault path and project slug

1. Check args. If vault path provided, use it.
2. No arg: check if `.realm/realm-state.json` exists → reuse its `vaultPath`.
3. Still not found: ask user for Obsidian vault root. Example: `/Users/username/Documents/obsidian/universe`.
4. Derive `projectSlug`: read `package.json` `.name`; if absent, use repo root dir name. Normalize to kebab-case.
5. Print `Vault: <path>  Slug: <slug>` and proceed.

### Step 2 — Read project metadata

Read (skip if missing):
- `package.json` → `name`, `description`, `dependencies`
- `README.md` → first 30 lines (title, description, tech stack)
- `IMPLEMENTATION_PLAN.md` or `*.plan.md` → milestone list

Extract: project name, one-line description, tech stack, milestones. Used to seed `overview.md`.

### Step 3 — Scaffold vault directories

Create only if not present:
```
<vaultPath>/projects/<slug>/
<vaultPath>/projects/<slug>/decisions/
<vaultPath>/projects/<slug>/functions/
<vaultPath>/projects/<slug>/classes/
<vaultPath>/projects/<slug>/systems/
<vaultPath>/projects/<slug>/discoveries/
<vaultPath>/projects/<slug>/sessions/
<vaultPath>/_templates/
```
Print created vs already-existed for each.

### Step 4 — Seed vault templates (if missing)

Write only if file does not exist:

**Decision-Node.md:**
```markdown
---
id: {{id}}
type: decision
status: active
tags: [decision]
created: {{date:YYYY-MM-DD}}
updated: {{date:YYYY-MM-DD}}
---

# {{title}}

Compressed: {{one-line summary}}

## Full Decision

### Context
What forced this decision.

### Decision
What was chosen and why.

### Consequences
Trade-offs and downstream effects.

## Implementation Locations

- [[ClassName]] — implements this
- [[functionName]] — enforces this

## Related Decisions

- [[other-decision]] — related context

## ECC Override
If overriding an ECC rule — which rule and why.
```

**Function-Node.md:**
```markdown
---
id: {{functionName}}
type: function
class: {{ClassName}}
status: active
tags: [function]
created: {{date:YYYY-MM-DD}}
updated: {{date:YYYY-MM-DD}}
---

# {{functionName}}()

**Signature**: `{{signature}}`

Compressed: {{one-line behavior summary}}. {{call frequency}}. {{performance}}

## Implementation

[Full implementation details, edge cases, performance notes]

## Depends On

- [[OtherClass]] — dependency
- [[helper-function]] — used in implementation

## Called By

- [[ClassOrFunction]] — uses this
- [[middleware-name]] — guards/validates
```

**Class-Node.md:**
```markdown
---
id: {{ClassName}}
type: class
status: active
tags: [class, service]
created: {{date:YYYY-MM-DD}}
updated: {{date:YYYY-MM-DD}}
---

# {{ClassName}}

Compressed: {{one-line responsibility}}. Uses [[Dependency1]], [[Dependency2]]. Used by [[Consumer1]], [[Consumer2]].

## Methods

- `method1()` — [[#method1]]
- `method2()` — [[#method2]]

## Dependencies

- [[OtherClass]] — persistence, caching, or utility

## Dependents

- [[Consumer1]]
- [[Consumer2]]
```

**Discovery-Note.md:**
```markdown
---
tags: [discovery]
date: {{date:YYYY-MM-DD}}
topic:
---

# {{title}}

## What

{{summary of finding}}

## Why It Matters

{{impact or relevance}}

## Related Decisions

- [[decision-title]] — connected context

## Related Functions/Classes

- [[functionName]] — affected or relevant
- [[ClassName]] — affected or relevant
```

**Session-Log.md:**
```markdown
---
tags: [session]
date: {{date:YYYY-MM-DD}}
project:
---

# {{date:YYYY-MM-DD}} — {{project}}

## Discovered

- {{finding}} — [[related-node]]

## Decided

- {{decision}} affects [[related-node]]

## Changed

- [[function-or-class]] — {{what changed}}

## Next Session

- {{open question}}
```

### Step 5 — Write overview.md stub (if missing)

Write `<projectDir>/overview.md` only if not present:

```markdown
---
tags: [project]
status: active
repo: <absolute project path>
---

# <project name>

<one-line description from README or package.json>

## Stack
<tech stack from package.json deps or README>

## Milestones
<list from plan file if found, else:>
- [ ] M1 —
- [ ] M2 —

## Knowledge
- [[architecture]] — service map, data flow
- [[decisions/ADR-000-index]] — all architecture decisions

## Key Source Files
- README.md
```

### Step 6 — Write ADR index stub (if missing)

Write `<projectDir>/decisions/ADR-000-index.md` only if not present:

```markdown
---
tags: [adr, index]
updated: <today YYYY-MM-DD>
---

# ADR Index — <slug>

| # | Title | Status | Date |
|---|---|---|---|
```

### Step 7 — Write project .claude/CLAUDE.md anchor (if missing)

Write `<projectRoot>/.claude/CLAUDE.md` only if not present:

```markdown
# <project name>

<one-line description>

## Knowledge Base (Obsidian)
`<vaultPath>/projects/<slug>/`
- `overview.md` — project status, milestone tracker
- `architecture.md` — service map, event shapes
- `decisions/` — Architecture Decision Records
- `sessions/` — per-session discovery logs

## When Making Architecture Changes
1. Check existing ADRs in `decisions/` before deciding
2. Write new ADR for decisions not already captured
3. After milestones: update `overview.md` milestone status
4. After each session: add entry in `sessions/YYYY-MM-DD-topic.md`
```

### Step 8 — Update .gitignore

Append `.realm/` to `<projectRoot>/.gitignore` if not present. Grep first; skip if line exists.

### Step 9 — Detect existing vault docs

Scan `<projectDir>/` for all `.md` files (including subdirs). Build initial `docs` registry:
- Each found file: `{ "status": "committed", "updated": "<today>" }`
- Files just created in Steps 5-6: same.

### Step 10 — Write realm-state.json

Create `<projectRoot>/.realm/`. Write `realm-state.json`:
```json
{
  "vaultPath": "<resolved vault path>",
  "projectSlug": "<slug>",
  "projectDir": "<vaultPath>/projects/<slug>",
  "phase": { "lastRun": null, "draftReady": false },
  "manifest": { "lastRun": null },
  "docs": { <registry from Step 9> }
}
```

### Step 11 — Print summary

```
realm-forge complete
  vault:    <vaultPath>
  project:  <slug>
  state:    <projectRoot>/.realm/realm-state.json

  vault docs registered: <N>
  templates:  <created|already existed>
  .gitignore: <updated|already had .realm/>

Next step: /realm-phase  (scan repo → stage doc plan)
```
