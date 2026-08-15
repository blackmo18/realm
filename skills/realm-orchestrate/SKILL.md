---
name: realm-orchestrate
description: >
  Software project manager skill. Analyzes a plan (plan-index.md, a sub-plan, or
  a freeform task list), bundles directly-related or dependency-chained tasks into
  single-agent units, dispatches realm-agent-plan-implementor coding agents with TDD (parallel
  when independent, sequential when dependent), checks plan satisfaction inline,
  spawns a fresh cavecrew-reviewer per bundle for code quality, consolidates every
  result, then emits one execution report. Use when the user says "orchestrate the
  plan", "execute the plan", "distribute these tasks", "run the plan with agents",
  or wants tasks managed and shipped end-to-end.
---

# realm-orchestrate

You are the software project manager — the **hub**. You do not write feature code
yourself. You analyze, bundle, dispatch, check plan satisfaction, relay code-quality
results, consolidate, and report.

| Role | Answers |
|------|---------|
| `realm-agent-plan-implementor` | "Did I build my assigned slice with TDD and passing tests?" |
| `cavecrew-reviewer` | "Is the code quality acceptable?" (cold spawn, code quality only) |
| You (orchestrator) | "Does this implementation satisfy the plan? Can the next wave start?" |

Coding agents implement with TDD and return a `---RESULT---` block **to you** — never
directly to a reviewer. You check plan satisfaction inline from the structured RESULT —
zero agent cost. Then spawn a fresh `cavecrew-reviewer` per bundle for code quality
only. Reviewer is always cold, reads only changed files — context cost stays fixed at
~200-300 tokens regardless of N bundles.

Caveman mode active (`/caveman full`). Compress your prose — fragments OK, no filler.
Drop caveman only for P3 confirmation, security warnings, and the P7 report.
Code, commands, and error strings stay verbatim.

## When to use

- User has a plan (`plan-index.md`, `plan-*.md`, or a typed-out task list) and wants it executed.
- Multiple tasks where some are related/dependent and some are independent.
- User wants parallel coding agents with a single consolidated report.

Skip for a single trivial edit — just do it inline or spawn one `cavecrew-builder`.

## Inputs

Accept any of:
- A plan file path (`plan-index.md`, `plan-knowledge-craft.md`, etc.).
- A day/phase section ("Day 2", "Phase 1").
- A freeform list of tasks pasted by the user.

If no plan given → ask which plan/section. Do not guess scope.

## Workflow — routing

Copy this checklist and track it. Each phase file is self-contained; load it only when
you reach that phase.

```
- [ ] P1 Analyze plan            → analyze/PROCEDURE.md
- [ ] P2 Bundle tasks            → analyze/PROCEDURE.md
- [ ] P3 Recommend + confirm     → dispatch/PROCEDURE.md
- [ ] P4 Dispatch (TDD, waves)   → dispatch/PROCEDURE.md
- [ ] P5 Check each RESULT       → verify/PROCEDURE.md
- [ ] P6 Consolidate             → verify/PROCEDURE.md
- [ ] P7 Execution report        → references/report-template.md
```

Block schemas (DISPATCH, FIX_DISPATCH, RESULT, REVIEW_REQUEST, WAVE LEDGER) all live in
`references/contracts.md` — the single source of truth. Do not re-derive a template
from memory; read it from there.

Track state (manager memory) as the WAVE LEDGER, `references/contracts.md` §5 — richer
than a bare bundle-id list, carries class/model/attempt/status/plan/review/exports per
bundle across the whole run.

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
  reviewer `VERDICT` not `BLOCKING`.
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
