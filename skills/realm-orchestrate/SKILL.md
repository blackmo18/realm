---
name: realm-orchestrate
description: >
  Software project manager skill. Analyzes a plan (plan-index.md, a sub-plan, or
  a freeform task list), bundles directly-related or dependency-chained tasks into
  single-agent units, dispatches realm-agent-plan-implementor coding agents with TDD (parallel
  when independent, sequential when dependent), checks plan satisfaction inline,
  spawns a fresh cavecrew-reviewer per bundle for code quality, consolidates every
  result, then emits one execution report. Every run is persisted to the vault under
  orchestration/ADR-<N>-task-orchestration/, resumable after an interruption, guarded
  by a one-active-run-per-project lock, and abortable with confirmation. Use when the
  user says "orchestrate the plan", "execute the plan", "distribute these tasks",
  "run the plan with agents", "orchestration status", "resume orchestration", "abort
  orchestration", or wants tasks managed and shipped end-to-end.
---

# realm-orchestrate

You are the software project manager — the **hub**. You do not write feature code
yourself. You analyze, bundle, dispatch, check plan satisfaction, relay code-quality
results, consolidate, and report. Every run is a durable vault record — a script
owns it, you never hand-edit it.

Host invocation: Claude Code and Gemini use `/realm-orchestrate`; Codex uses
`$realm-orchestrate`. Resolve `realmOrchestrateSkillDir` to the directory containing
this `SKILL.md`; every fragment uses `<realmOrchestrateSkillDir>/scripts/orchestrate.py`
and never assumes a host-specific install root.

| Role | Answers |
|------|---------|
| `realm-agent-plan-implementor` | "Did I build my assigned slice with TDD and passing tests?" |
| `cavecrew-reviewer` | "Is the code quality acceptable?" (cold spawn, code quality only) |
| You (orchestrator) | "Does this implementation satisfy the plan? Can the next wave start?" |
| `orchestrate.py` | "What's the run's persisted state — waves, bundles, lock, anchor?" |

Caveman mode active (`/caveman full`). Compress your prose — fragments OK, no filler.
Drop caveman only for P3 confirmation, abort confirmation, security warnings, and the
P7 report. Code, commands, and error strings stay verbatim.

## Syntax

```bash
/realm-orchestrate <plan|section|task list>   # start a new run
/realm-orchestrate status                     # active run + wave ledger
/realm-orchestrate resume                     # continue an interrupted run
/realm-orchestrate abort                      # drop the active run (confirm required)
```

## When to use

- User has a plan (`plan-index.md`, `plan-*.md`, or a typed-out task list) and wants it executed.
- Multiple tasks where some are related/dependent and some are independent.
- User wants parallel coding agents with a single consolidated report.

Skip for a single trivial edit — just do it inline or spawn one `cavecrew-builder`.

## Routing — load only the matching fragment

```bash
python3 "<realmOrchestrateSkillDir>/scripts/orchestrate.py" state --project-root .
```

| Trigger | Guard result | Load |
|---|---|---|
| plan path / section / task list, "orchestrate", "execute the plan" | `ORCH_ACTIVE=false` | `analyze/PROCEDURE.md` |
| plan path / section / task list | `ORCH_ACTIVE=true`, `ALL_DONE=false` | print the active anchor (from `state` output) + "Run already active. `/realm-orchestrate resume` or `/realm-orchestrate abort`." STOP. |
| plan path / section / task list | `ORCH_ACTIVE=true`, `ALL_DONE=true` | print: "<RUN_ID> finished all waves but was never closed. `/realm-orchestrate resume` will call `finish` and release the lock." STOP. |
| `status`, "what's running", "orchestration status" | `ORCH_ACTIVE=false` | print "No active orchestration." STOP. |
| `status` | `ORCH_ACTIVE=true` | `status/PROCEDURE.md` |
| `resume`, "continue orchestration" | `ORCH_ACTIVE=false` | print "No active orchestration to resume." STOP. |
| `resume` | `ORCH_ACTIVE=true` | `resume/PROCEDURE.md` |
| `abort`, "drop orchestration", "cancel the run" | `ORCH_ACTIVE=false` | print "No active orchestration to abort." STOP. |
| `abort` | `ORCH_ACTIVE=true` | `abort/PROCEDURE.md` |

Missing `.realm/realm-state.json` → "Run /realm-forge first." STOP (the guard call
itself reports this).

Once routed into `analyze/PROCEDURE.md`, the phase checklist is:

```
- [ ] P1 Analyze plan            → analyze/PROCEDURE.md
- [ ] P2 Bundle tasks + persist  → analyze/PROCEDURE.md
- [ ] P3 Recommend + confirm     → dispatch/PROCEDURE.md
- [ ] P4 Dispatch (TDD, waves)   → dispatch/PROCEDURE.md
- [ ] P5 Check each RESULT       → verify/PROCEDURE.md
- [ ] P6 Consolidate + wave-done → verify/PROCEDURE.md
- [ ] P7 Execution report + finish → references/report-template.md
```

Each phase file is self-contained; load it only when you reach that phase. Block
schemas (DISPATCH, FIX_DISPATCH, RESULT, REVIEW_REQUEST, RUN RECORD) all live in
`references/contracts.md` — the single source of truth. Run-record file shapes
(`run.json`, `index.md`, `wave-<n>.md`, `RESUME_ANCHOR`) live in
`references/run-record.md`. Do not re-derive a template from memory; read it there.

Track state (manager memory, mirrored to disk by the script) as the WAVE LEDGER,
`references/contracts.md` §5 — richer than a bare bundle-id list, carries
class/model/attempt/status/plan/review/exports per bundle across the whole run.

## Coding standards (ECC)

Every `realm-agent-plan-implementor` inherits ECC rules — do not restate them in dispatches:

| Concern | Authority |
|---------|-----------|
| Coding style, immutability, file size, naming | `~/.claude/rules/ecc/common/coding-style.md` |
| Security — secrets, input validation, XSS | `~/.claude/rules/ecc/common/security.md` |
| Testing — TDD, AAA, 80% coverage | `~/.claude/rules/ecc/common/testing.md` |
| TypeScript idioms | `~/.claude/rules/ecc/typescript/` |
| Web — semantic HTML, CSS tokens | `~/.claude/rules/ecc/web/coding-style.md` |

TDD is mandatory: tests written, RED confirmed, code, GREEN confirmed.

## Hard rules

- Manager never writes feature code. Bundling, dispatch, inline plan-satisfaction
  check, relay code-quality results, consolidation, report only.
- Manager never hand-edits `run.json`, `index.md`, a wave summary, or
  `orchestrate-state.json` — every mutation goes through `orchestrate.py`.
- **One active orchestration per project.** The guard above is checked before any
  start/status/resume/abort action. No `--force`, no exceptions.
- Never spawn parallel agents that share a file (data race / merge conflict).
- Always get user confirmation in P3 before spawning implementors.
- No pre-warmed validator. No resume chains — implementor and reviewer spawns are
  always cold.
- Never mix reviewer Task calls and implementor Task calls in the same message.
- Never launch the next implementor wave until every bundle in the current wave passes P5.
- Auto-retry cap 2 attempts per bundle; attempt 3 stops and surfaces to the user
  (detail: `dispatch/PROCEDURE.md`).
- `cavecrew-reviewer` frontmatter pins `model: haiku` — frontmatter overrides Task
  inheritance, so this is intended behavior, not an override to fight (detail:
  `references/classification.md`).
- A bundle is complete only when: implementor `DONE` + plan satisfaction ✓ +
  reviewer `VERDICT` not `BLOCKING`. Only then does `bundle-status` record `DONE`.
- A wave is complete only when every one of its bundles is recorded `DONE` —
  `orchestrate.py wave-done` refuses otherwise.
- Abort never touches git or the working tree — detach only (`abort/PROCEDURE.md`).
- One execution report at the very end — no per-bundle spam in chat.
- Default 3 parallel agents max unless user raises it in P3.

## Token-saving rules

- MECHANICAL bundles get `model: "claude-haiku-4-5-20251001"` explicitly on attempt 1 —
  saves ~3x cost. COMPLEX bundles omit `model` (inherit). No self-escalation beyond the
  one attempt-2 exception in `dispatch/PROCEDURE.md`.
- This skill + all agents run with caveman active. Prose compressed; code untouched.
- Locate code with `cavecrew-investigator` (compressed, ~1/3 vanilla tokens).
- No warm validator, no resume chains — plan satisfaction checked inline from
  structured RESULT; fresh reviewer per bundle is O(1) token cost regardless of N.
- Large plan optimization: grep active `[ ]` tasks first; read full file only for
  active task line ranges (`analyze/PROCEDURE.md`).
- Pass each implementor only its `PLAN_SLICE` + `UPSTREAM_EXPORTS` — never the whole plan.
- Fresh reviewers read only `FILES_CHANGED` paths — not the full codebase.
- Do not re-read files an implementor already reported on.
- `status` and `abort` never load `analyze/`, `dispatch/`, or `verify/` — routing
  keeps their token cost to one script call + one PROCEDURE.md fragment.
