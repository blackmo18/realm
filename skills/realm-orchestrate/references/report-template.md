# P7 — Execution Report Template

Emit once, at the end of the run. Normal English (not caveman) for readability — this
is the one output the user reads closely.

```
═══ EXECUTION REPORT ═══
Run: <RUN_ID>
Record: <RUN_DIR>
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

`Run:` / `Record:` come from the run's `RUN_ID` / `RUN_DIR` (last known from
`orchestrate.py status` or the P2 `start` call).

## Finish the run

Only when every wave is `DONE` and every bundle counts as complete per
`verify/PROCEDURE.md` P6:

```bash
python3 "<realmOrchestrateSkillDir>/scripts/orchestrate.py" finish --project-root .
```

This is what releases the one-active-run lock — the next `/realm-orchestrate <plan>`
cannot start until it runs. If the report surfaces unresolved `BLOCKERS`, do **not**
call `finish` — the run stays active (correctly) until the user resolves them and the
outstanding bundles reach `DONE`, or explicitly asks to abort.
