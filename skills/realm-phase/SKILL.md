---
name: realm-phase
description: >
  Dry-run repo mapping step in the realm pipeline. Default (auto) mode: infers targets from git diff since last manifest — 10-20x cheaper than full scan for typical sessions. Full mode (--full flag): scans whole codebase with cavecrew-investigator swarm. Manual targeted mode (/realm-phase function:X): scans named entities only. All modes caveman-compress findings, diff vs vault, draft ADR candidates and doc updates, write staged manifest-draft.md to .realm/. Never writes to vault. Warns on stale docs in targeted/auto modes. Must run after realm-forge and before realm-manifest.
origin: realm
---

# realm-phase

Scan, compress, stage — without touching vault. Second skill in realm pipeline.

## Modes

| Mode | Trigger | Cost | When |
|------|---------|------|------|
| **Auto** | `/realm-phase` (default) | Git diff → targeted scan | Most sessions — 1-3 changed entities |
| **Manual targeted** | `/realm-phase function:validateUser` | Single-entity scan | Know exactly what changed |
| **Multi-target** | `/realm-phase function:X class:Y` | N-entity scan | Changed handful of entities |
| **Full** | `/realm-phase --full` | Full investigator scan | Milestones, big refactors, stale doc reconciliation |

## When to Use

| Trigger | Example |
|---|---|
| After coding session (default) | `/realm-phase` — auto-infers from git diff |
| Know exact entity changed | `/realm-phase function:validateUser` |
| After major milestone or refactor | `/realm-phase --full` |
| Stale docs need reconciliation | `/realm-phase --full` |
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

Load: `vaultPath`, `projectSlug`, `projectDir`, `manifest.lastRun`, `docs` registry.

### Step 1 — Detect mode

Parse invocation args:
- `--full` present → set `mode: full`. Skip to Step 4.
- Entity specifiers present (`function:X`, `class:X`, `system:X`) → set `mode: targeted`, collect target list. Skip to Step 3.
- File path present (bare path like `src/foo.tsx` or `@`-expanded file) → grep the file for top-level entity definitions (same patterns as Step 2), set `mode: targeted`, mark the file as `already-read`. Do NOT read it again. Skip to Step 3.
- Neither → set `mode: auto`. Proceed to Step 2.

### Step 2 — Auto mode: infer targets from git diff

Run:
```bash
git -C <projectRoot> diff --name-only HEAD@{<manifest.lastRun>}..HEAD 2>/dev/null
```
If `manifest.lastRun` is null (never run): use `git -C <projectRoot> diff --name-only HEAD~1..HEAD`.

Filter to source files only — exclude: `.realm/`, `node_modules/`, `dist/`, `build/`, `__pycache__/`, test files (`*.test.*`, `*.spec.*`, `*_test.*`), lock files (`*.lock`, `package-lock.json`), assets.

**No changed source files found:**
```
No source changes since last manifest. Vault may be current.
Run /realm-phase --full to force full scan.
```
STOP.

For each changed source file, grep for top-level entity definitions:
- Functions: `^(export )?(async )?function `, `^(export default )?function `, `^def `, `^func `, `^fn `
- Classes: `^(export )?(abstract )?class `, `^(pub )?(struct|impl|enum) `, `^type [A-Z]`
- Services/modules: files named `*Service.*`, `*Manager.*`, `*Controller.*`, `*Handler.*`

**No entities found from diff:**
```
Changed files detected but no named entities found.
Run /realm-phase --full for complete scan.
```
STOP.

Print: `Auto-targeted <N> entities from git diff: <list>`

Set `mode: targeted`, targets = inferred entity list. Proceed to Step 3.

### Step 3 — Stale doc check (targeted and auto modes)

Scan `docs` registry in realm-state.json. Count entries with `status: "stale"`.

If stale docs exist:
```
WARN: <N> stale doc(s) detected — not covered by targeted scan.
      Run /realm-phase --full to reconcile all stale nodes.
```

Proceed to Step 4 (spawn scan agent with targeted mode).

### Step 4 — Spawn scan agent

Spawn agent `realm-agent-scan` with this prompt:

```
projectRoot: <absolute path to project root>
vaultPath: <vaultPath from Step 0>
projectSlug: <projectSlug from Step 0>
projectDir: <projectDir from Step 0>
mode: <full|targeted>
targets: <list of specifiers, e.g. "function:validateUser class:UserService", or empty if full>
already-read: <comma-separated list of file paths already in context, or "none">

State already loaded — do NOT re-read realm-state.json.
Files listed under already-read: do NOT re-read; treat their content as authoritative from main thread context.

Scan the codebase and generate a staged manifest draft.
Follow the full procedure in your instructions.
```

Wait for completion. Surface the agent's gap map to the user.
