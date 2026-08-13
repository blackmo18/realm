---
name: realm-planning:phase2
description: >
  Phase 2 of realm-planning. Code-level implementation plan for a coding agent.
  Requires approved Phase 1. Re-enters plan mode for its own read-only work.
  Consumes Phase 1 Anchor Set as authoritative file list — no layer-based
  re-scan. Always defines Affected Files, New Files, and Test Scenarios
  (must-pass) before the step-by-step plan, then writes
  execution/<NNN>-exct-<slug>.md to vault.
---

# realm-planning — Phase 2: Code-Level Plan

Requires approved Phase 1. Phase 2 re-enters plan mode for its own read-only
work (Steps 1-5) — approval to write is a separate `ExitPlanMode` at Step 6,
distinct from Phase 1's.

**Phase 1 Anchor Set is authoritative for the entire phase** — 1-hop column
already populated by Phase 1 (`graphify affected`). No step below re-scans
the codebase or classifies "affected" against layers; every file reference
traces back to that one table.

## Step 0 — Enter Plan Mode

Full boundary + fallback: `../references/plan-mode-contract.md`. `EnterPlanMode` before any other step. Steps 1-5 are read-only. No Write calls until Step 6.

## Step 1 — Contract Gate

`## Contract Delta` in approved Phase 1 plan → resolve slug(s), check
`<projectDir>/contracts/<slug>-api-contracts.md` exists for each (trust Phase
1's determination, don't re-derive it).

- Missing → **STOP** before Step 2: `Contract Delta pending — run "write contract" before Phase 2.`
- Exists → record path(s) for Step 6 execution-file `links:`. Proceed.

No `## Contract Delta` → skip this step, no gate, straight to Step 2.

Enforces: **Phase 1 → contract (if applicable) → Phase 2** — Phase 2 plans
against the frozen shape, not a moving target.

## Step 2 — Rule + Skill Selection

Read approved Phase 1. Layer → rule/skill mapping table: `../references/layer-rules.md`. Layers classify **rules only** — scope stays the Anchor Set.

Document selected rules + skills before Step 3.

## Step 3 — Codebase Validation

Spawn `code-architect` with: Phase 1 plan, active rules/skills, **Phase 1 Anchor Set table verbatim** — pass as-is, do not re-derive.

Gap-fill escape: an anchor's 1-hop cell is empty (fallback investigator path didn't collect it) → `code-architect` has Bash, may run `graphify affected "<file>" --depth 1` to fill it. Cap **3** graphify calls. Never grep.

Greenfield exception: no file list exists → pass Phase 1 conventions summary instead.

**Failure mode**: code-architect returns an empty or unusable file list on a non-greenfield run → surface the gap, ask user whether to re-run Phase 1 anchor resolution or narrow scope. Never fabricate a file list to keep moving.

Returns: conflicts with existing code, existing vs new files, patterns to follow, logging plan (requirements: `../references/logging-plan.md`).

## Step 4 — Scope & Test Definition (mandatory, always)

Before any step-by-step plan exists, populate `references/plan-template.md`'s
`### Scope Summary` section in full. **Always required** — not gated on
`tdd-workflow` selection (unlike Step 5's per-task Test field, which stays
conditional on task type).

- **Affected Files** — every existing file Step 3 marked modified, one line each: path + what changes.
- **New Files** — every file Step 3 marked created, one line each: path + purpose.
- **Test Scenarios (must pass)** — checklist of concrete scenarios (condition → expected outcome) that gate this plan as done. Derive from Phase 1 acceptance criteria + Step 3 conflicts/edge cases. Empty Affected/New Files or zero Test Scenarios → plan is incomplete, do not proceed to Step 5.

This section is a gate: Step 5's task list must trace back to entries here — every task's **File** appears in Affected or New Files, every task's **Test** maps to a Test Scenario.

## Step 5 — Step-by-Step Plan

Use `../references/plan-template.md` (Phase 2 section) — Scope Summary (Step 4) first, then Tasks.

Each task:
- What: build/change what
- Where: file + function/component (must appear in Step 4 Affected/New Files)
- How: impl notes (follow pattern X, use Y)
- Logging: trace + non-PII inputs/outputs + branch-point logs (`../references/logging-plan.md`)
- Test: unit / integration / E2E (must map to a Step 4 Test Scenario)

Order by execution dependency.

Testing detail, when `tdd-workflow` selected in Step 2, expand Step 4's scenarios into:
- Unit: functions to cover
- Integration: API routes / DB ops (when `backend`/`data` active)
- E2E: critical user flows (when `frontend` + user-facing)
- Coverage: 80% minimum on new code

Skip test types with no coverage surface. Step 4's Test Scenarios checklist stays mandatory regardless.

## Step 6 — Exit Plan Mode + Write Execution File

Present full Phase 2 plan to user (Scope Summary + Tasks). `ExitPlanMode` —
approval to write, separate from Phase 1's. No Write calls before this.

Naming, ADR number reservation, frontmatter, `links:` omit rules: `../references/vault-conventions.md` (`write adr` reuses the same number).

Write `<projectDir>/execution/<NNN>-exct-<slug>.md` directly with Write tool (create `execution/` if missing). No manifest pipeline. No agent spawn. Body = full Phase 2 output verbatim, including Scope Summary.

Print: `execution file written: execution/<NNN>-exct-<slug>.md`

Say `write adr` to commit the decision and planning file to vault.
