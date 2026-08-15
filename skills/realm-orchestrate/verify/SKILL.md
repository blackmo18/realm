---
name: orchestrate-plan-verify
description: >
  P5-P6 of orchestrate-plan. Checks plan satisfaction inline from the RESULT block,
  spawns a fresh cavecrew-reviewer per bundle for code quality, then consolidates
  every result before the P7 report. Loaded by the orchestrate-plan hub — not
  invoked directly.
disable-model-invocation: true
origin: local
---

# verify — P5 Check each RESULT, P6 Consolidate

## P5 — Check each RESULT (two sub-steps, separate messages)

### Step A — Plan satisfaction (inline, zero agent cost)

Read `TASKS_DONE` from the `---RESULT---` block (`../references/contracts.md` §3).
Compare mechanically against the bundle's `PLAN_SLICE`:

```
For each task in PLAN_SLICE:
  Listed in TASKS_DONE as "done"?   → satisfied
  Listed as "missing" or "blocked"? → fix-required
  Not listed at all?                → fix-required
```

If `STATUS` is `BLOCKED` or `PARTIAL` → surface `BLOCKER_NEEDS` to user verbatim. Do
not proceed to Step B. Do not mark that bundle done. Decide: provide missing detail and
re-dispatch (`../dispatch/SKILL.md` Retry / fix-dispatch), or pause.

If plan satisfaction fails → re-dispatch as FIX_DISPATCH in the next P4 wave
(`../references/contracts.md` §2, retry cap in `../dispatch/SKILL.md`). Never amend a
failed run silently.

### Step B — Code quality (fresh cavecrew-reviewer, cold spawn)

Only run Step B after Step A passes, **or** when `RESULT.CONFIDENCE: low` /
`RESULT.DEVIATIONS` is non-empty — those force a review even on an otherwise-clean
MECHANICAL bundle.

Spawn one fresh `cavecrew-reviewer` per bundle — the plugin agent's own model pin
(`model: haiku` in its frontmatter) applies as-is; do not attempt to override it. Use
the REVIEW_REQUEST wrapper (`../references/contracts.md` §4) — pass only changed files
and `KNOWN_ASSUMPTIONS`, no plan context, no other bundle results, no history.

Act on the returned `VERDICT`:
- `BLOCKING` → re-dispatch fix as FIX_DISPATCH before next wave, `REVIEW_FINDINGS` carries the 🔴 lines verbatim
- `SHOULD_FIX` → surface in P6 consolidation, user decides
- `CLEAN` → include 🔵 notes (if any) in P7 report only

**Never resume a reviewer.** Each bundle gets a fresh, cold reviewer — context cost
stays fixed at ~200-300 tokens per bundle regardless of how many bundles have run.

For trivial single-file bundles: same one-shot `cavecrew-reviewer`, same pattern.

## P6 — Consolidate

Collect every `---RESULT---` and `---REVIEW---`, updating the WAVE LEDGER
(`../references/contracts.md` §5) per bundle. Then:

- `BLOCKED` / `PARTIAL` → surface `BLOCKER_NEEDS`. Do not mark done. Re-dispatch or pause.
- Plan satisfaction fail (Step A) → re-dispatch as FIX_DISPATCH. Never amend silently.
- `VERDICT: BLOCKING` (Step B) → re-dispatch fix, run Step B again on the new diff.
- Only bundles with `STATUS: DONE` + plan satisfaction ✓ + `VERDICT` not `BLOCKING` count
  as complete.
- If a `plan-*.md` / `plan-index.md` exists, run the `validate-plan` skill once as a
  final cross-check (complements per-bundle checks, does not replace).

Return to hub → P7 (`../references/report-template.md`).
