---
name: realm-concise
description: >
  God-file concierge. Deterministic crawler (scripts/concise.py, no LLM) finds
  source files over a LOC threshold, scores them by blast radius / test
  safety / churn, and keeps a persistent refactor queue in
  .realm/concise-state.json plus a committed docs/GOD_FILES.md ledger.
  Use to scan for oversized files, inspect the refactor queue, recommend the
  lowest-impact candidate, or hand approved work to realm-planning. Never
  approves, plans, or implements without explicit user confirmation.
---

# realm-concise

Persistent god-file triage. Crawler finds candidates, script remembers the
queue, LLM only reasons about the one file being actively reviewed.

Host invocation: Claude Code and Gemini use `/realm-concise`; Codex uses `$realm-concise`.
Resolve `realmConciseSkillDir` to the directory containing this `SKILL.md`; use
`<realmConciseSkillDir>/scripts/concise.py` for every script call.

## When to Use

| Trigger | Example |
|---|---|
| Periodic tech-debt check | `/realm-concise`, "what's a good file to refactor next" |
| Query the standing queue | `/realm-concise next` |
| Decide if a specific file is worth splitting | `/realm-concise recommend <file>` |
| Ready to act on an approved candidate | `/realm-concise plan <file>` |
| Just landed a refactor | `/realm-concise done <file>` |
| Deliberately leave a file alone | `/realm-concise ignore <file> --reason "..."` |

## When NOT to Use

- Want an ADR for a decision unrelated to file size → `/realm-planning` directly.
- Want live code relationships, not a refactor queue → `graphify query`/`explain`.
- Want past *why* on a completed refactor → `/realm-recall "why split <file>"`.
- No `.realm/realm-state.json` in the project at all → this skill still works (state is independent of the realm ADR pipeline), but `/realm-concise plan` needs realm-planning's vault, so run `/realm-forge` first if the vault was never bootstrapped.

## Ground rules (apply across every subskill)

1. **Script does the counting.** Every LOC count, fan-in resolution, churn lookup, and state mutation goes through `scripts/concise.py`. LOC means physical source lines containing code; blank lines, comments, and documentation comments (including JSDoc) are excluded. Never hand-count lines or hand-edit `.realm/concise-state.json`.
2. **Two active projects, always pass `--root`.** Default targets are `knowledge-craft` and `backoffice-main` (per workspace `CLAUDE.md`). A subcommand naming a file infers the project from the path prefix.
3. **Gate keeping is not optional.** `approve`, `plan`, and `done` all require the user to explicitly name the file and the action in the same turn — enforced in detail by `lifecycle/PROCEDURE.md`.
4. **`plan` never implements.** It hands off to `/realm-planning` and stops once a plan returns. Implementation is a separate, later, separately-approved action.

## Syntax

```bash
/realm-concise                        # scan both projects, print top 3 each
/realm-concise scan [project]         # rescan (default: both)
/realm-concise next [project] [-n N]  # read-only queue peek, no rescan
/realm-concise recommend <file>       # deep single-file analysis (the only LLM read)
/realm-concise approve <file>         # candidate -> approved (explicit only)
/realm-concise plan <file>            # approved -> in-progress, delegates to /realm-planning
/realm-concise done <file> [--adr X]  # mark refactored, offer ADR write-back
/realm-concise ignore <file> --reason "..."  # terminal suppression
```

`project` is `knowledge-craft` or `backoffice-main`; `<file>` is a path relative to that project's root.

## Routing

Each subskill is a self-contained procedure — load only the one the trigger matches, not the others.

- `scan` / `next` / `show` → load `query/PROCEDURE.md`
- `recommend <file>` → load `recommend/PROCEDURE.md`
- `approve` / `plan` / `done` / `ignore` → load `lifecycle/PROCEDURE.md`

---

## Memory model

- `.realm/concise-state.json` — script-owned, gitignored, source of truth for the live queue (status, score, tier, per-file metrics, history of completed refactors).
- `docs/GOD_FILES.md` — script-rendered, committed, human-readable view of the same state. Never hand-edited; every script command that mutates state regenerates it.
- Vault (`decisions/ADR-*.md`) — written only via `/realm-planning`'s `write adr`, only after a `done` completion, only if the user takes the offer. This is where *why* a refactor happened survives for `/realm-recall`.
