---
name: orchestrate-plan-analyze
description: >
  P1-P2 of orchestrate-plan. Reads the plan, extracts tasks, bundles them into
  agent-sized units, classifies each bundle MECHANICAL/COMPLEX. Loaded by the
  orchestrate-plan hub — not invoked directly.
disable-model-invocation: true
origin: local
---

# analyze — P1 Analyze plan, P2 Bundle tasks

## P1 — Analyze plan

**Large plans (>200 lines):** grep active tasks first, then read context only around those lines:

```bash
grep -n "^- \[ \]" plan-index.md   # active tasks only
```

Read ±10 lines of surrounding context per active task match — not the full file.

**Small plans (<200 lines):** read in full.

For each task extract: `id`, `description`, `affected_files` (best-effort from task text),
`depends_on` (prerequisite task ids), `service` (kc / medusa / bo if applicable). Skip tasks
already `[x]` done unless user says re-run.

Compress extracted tasks into a **PLAN_SUMMARY** (≤150 lines) — store in manager memory.
Used in P5 plan-satisfaction checks and implementor `PLAN_SLICE` generation.

Use `cavecrew-investigator` (not vanilla Explore) when you must locate affected files —
compressed output saves main context.

## P2 — Bundle tasks

Group tasks into **bundles**. One bundle = one coding agent. Apply rules in order:

1. **Dependency chain → same bundle.** If B `depends_on` A, put A and B in one bundle, ordered A→B. Agent implements them in sequence.
2. **Shared files/module → same bundle.** Tasks touching the same file go together.
3. **Same feature slice → same bundle.** Tasks that only make sense shipped together (e.g. schema + migration + the API that reads it).
4. **Independent + disjoint files → separate bundles.** These can run in parallel.

**Hard constraint — no file shared across parallel bundles.** Record each bundle's file
set to pass `PEER_FILES` per agent and detect conflicts.

Output bundle plan as table: `bundle | tasks | files | depends_on_bundle | parallelizable`.

### Bundle classification

After the table, classify each bundle MECHANICAL or COMPLEX and assign its `SERVICE`
(kc / medusa / bo) + `CWD` + `TEST_CMD` / `TYPECHECK_CMD` for that service. Full signal
table and model routing: `../references/classification.md`.

Store classification + service info in the WAVE LEDGER (`../references/contracts.md` §5)
— this feeds P3 confirmation and every P4 dispatch.

Return to hub → P3.
