---
name: realm-flourish
description: >
  Lightweight update skill for the realm pipeline. Uses git diff since the last manifest run to identify changed files, runs a targeted realm-phase on those files only, and auto-commits the changes via realm-manifest if the diff is minor (no new structural decisions). Falls back to staged-for-review mode when major changes are detected. 10-20x cheaper than a full realm-phase + realm-manifest cycle for incremental work. Maps to the /realm:florish intent from sample_usage.md.
origin: realm
---

# realm-flourish

Incremental update: git diff → targeted scan → auto-commit minor changes. One command instead of two.

## When to Use

| Trigger | Example |
|---|---|
| Changed 1-3 functions or classes | "flourish", `/realm-flourish` |
| Quick sync after coding sprint | "update realm", "sync realm" |
| Short session end | "log this session to realm" |

## When NOT to Use

- First-time setup → `/realm-forge` first
- Vault not initialized → `/realm-phase` then `/realm-manifest` first
- Major architecture change (new service, new decision) → `/realm-phase` full for review boundary
- Want to review draft before committing → `/realm-phase` + `/realm-manifest` separately
- `.realm/realm-state.json` missing → `/realm-forge` first

---

## Procedure

Read `_shared/realm-conventions.md` before executing.

**Auto-commit boundary**: flourish auto-commits ONLY when all changes are `type: function | class | discovery`. Any new `type: decision` or architecture change → staged mode.

### Step 0 — Guard checks

1. Read `.realm/realm-state.json`. If missing: `No realm state. Run /realm-forge first.` STOP.
2. Check `phase.draftReady == true`. If true: `Staged draft exists. Run /realm-manifest to commit it first, or delete .realm/manifest-draft.md to discard.` STOP.
3. Load: `vaultPath`, `projectSlug`, `projectDir`, `manifest.lastRun`.

### Step 1 — Identify changed files via git diff

Run `git diff --name-only` from project root:
- `manifest.lastRun` set: `git diff --name-only HEAD@{<last-manifest-datetime>}..HEAD`
- `manifest.lastRun` null: use all tracked files (first flourish = full scan, warn user)
- Filter: source files only (exclude `.realm/`, test files, lock files, assets)
- No changed source files: `No source changes since last manifest. Vault is current.` STOP.

Print: `Changed source files (<N>): <list>`

### Step 2 — Map changed files to entity targets

For each changed file:
- Grep for top-level function/class definitions
- Check if vault node exists: `functions/<id>.md` or `classes/<id>.md`
- Separate: **Known** (node exists → update) | **Unknown** (no node → create)

Print: `Targets: <N> known (update), <M> new (create)`

### Step 3 — Spawn targeted cavecrew-investigator

Spawn with entity list from Step 2 (same targeted prompt as `realm-phase` targeted mode). Collect output.

### Step 4 — Diff and classify changes

For each entity, compare investigator output vs vault node. Classify:
- `minor` — function body changed, perf note added, dep link changed
- `structural` — new service boundary, new data flow, new pattern decision in comments
- `new-decision` — found `"DO NOT"`, invariant, or architecture rationale not in vault

Build:
- `auto_commit`: all `minor`
- `review_required`: any `structural` or `new-decision`

### Step 5 — Route by classification

**If `review_required` is empty:**

→ Auto-commit:
1. Draft manifest (`mode: targeted`)
2. Write node updates directly (skip staged-draft)
3. Update `realm-state.json`: `manifest.lastRun = <now>`, mark docs `committed`
4. Write session log (Step 6)
5. Print summary (Step 7)

**If `review_required` non-empty:**

→ Staged mode:
1. Draft manifest for ALL changes (minor + structural)
2. Write `.realm/manifest-draft.md`
3. Update `realm-state.json`: `phase.draftReady = true`
4. Print:
```
realm-flourish → staged (review required)

  Structural changes detected — auto-commit disabled:
    <list of structural/new-decision entities>

  Minor changes included in draft:
    <list>

  Review: .realm/manifest-draft.md
  Commit: /realm-manifest

  (To force auto-commit: edit draft to remove structural sections, then run /realm-manifest)
```
5. STOP.

### Step 6 — Write session log (auto-commit path only)

Write `<projectDir>/sessions/<YYYY-MM-DD>-flourish.md`:

```markdown
---
tags: [session, flourish]
date: <YYYY-MM-DD>
project: <slug>
---

# <YYYY-MM-DD> — flourish sync

## Changed

<list of updated nodes with one-liner of what changed>

## Next

- Review stale nodes: /realm-status
```

Append to existing same-day session file if present.

### Step 7 — Print summary (auto-commit path)

```
realm-flourish complete  [auto-committed]

  source files scanned: <N>
  entities updated:     <N>  (functions: X, classes: Y, discoveries: Z)
  entities created:     <N>
  session log:          sessions/<YYYY-MM-DD>-flourish.md

  vault current as of <timestamp>

Next: /realm-status to verify  |  /realm-phase (full) after next milestone
```
