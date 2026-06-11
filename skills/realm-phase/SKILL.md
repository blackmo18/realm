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

This skill performs a guard check and mode detection, then delegates all scanning and draft generation to `realm-agent-scan`.

### Step 0 — Guard check

Read `<projectRoot>/.realm/realm-state.json`. If missing: print `No realm state found. Run /realm-forge first.` and STOP.

### Step 1 — Detect mode and targets

Parse invocation args for entity specifiers: `function:X`, `class:X`, `system:X`.
- Found → set `mode: targeted`, collect target list.
- None → set `mode: full`.

### Step 2 — Spawn scan agent

Spawn agent `realm-agent-scan` with this prompt:

```
projectRoot: <absolute path to project root>
mode: <full|targeted>
targets: <list of specifiers, e.g. "function:validateUser class:UserService", or empty>

Scan the codebase and generate a staged manifest draft.
Follow the full procedure in your instructions.
```

Wait for completion. Surface the agent's gap map to the user.
