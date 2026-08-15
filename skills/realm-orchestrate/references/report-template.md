# P7 — Execution Report Template

Emit once, at the end of the run. Normal English (not caveman) for readability — this
is the one output the user reads closely.

```
═══ EXECUTION REPORT ═══
Plan: <plan/section>
Bundles: <N> (<P> parallel, <S> sequential)

PER BUNDLE
  B1 <name> — DONE   files: a.ts, b.ts   tests: 12/12   plan: ✓   quality: CLEAN
  B2 <name> — BLOCKED  reason: <one line>  needs: <what user must provide>

TASKS: <done>/<total> complete
TESTS: <pass>/<total> across all bundles
PLAN-CHECK: <validate-plan summary, or n/a>

BLOCKERS (action needed):
  - <bundle>: <what the user must decide/provide>

NEXT: <single recommended next step>
```

`quality:` column takes the reviewer's `VERDICT` field verbatim (`CLEAN` /
`SHOULD_FIX` / `BLOCKING`) — see `references/contracts.md` §4.
