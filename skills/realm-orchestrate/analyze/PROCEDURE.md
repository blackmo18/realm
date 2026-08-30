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

## Persist the run — before P3 confirmation

Assign each bundle a wave number (1-indexed, by its dependency/parallelizability
column). For each bundle, capture `planSlice` now — the exact plan lines for its
tasks, already in hand from P1's extraction — so it is written once and never
re-derived (`references/run-record.md`). Write the bundle table to a scratch
JSON file, one object per bundle:

```json
[
  { "id": "B1", "name": "<short label>", "wave": 1, "class": "MECHANICAL",
    "tasks": ["T1", "T2"], "files": ["a.ts"], "dependsOn": [],
    "planSlice": "<exact plan lines for T1, T2>" },
  { "id": "B2", "wave": 2, "class": "COMPLEX", "tasks": ["T3"], "files": ["b.ts"], "dependsOn": ["B1"],
    "planSlice": "<exact plan lines for T3>" }
]
```

Then create the run record:

```bash
python3 "<realmOrchestrateSkillDir>/scripts/orchestrate.py" start \
  --project-root . --plan <plan path> --plan-slug <kebab-case plan slug> \
  --bundles-file <scratch json path>
```

Run index matches the source plan: `<plan path>`'s leading `NNN-` (e.g.
`execution/007-exct-foo.md`) becomes `ADR-007-task-orchestration`, keeping the
run tied to that same planning/decisions/execution trio. A freeform `--plan`
with no numeric prefix (`plan-index.md`, a typed-out task list) falls back to
the next free index under `orchestration/`.

Exit code `2` means another run is already active (the guard should have caught
this before P1 — treat it as a bug and surface the printed anchor to the user
instead of retrying). Exit `1` with an index-collision message means a prior
orchestration run already used this plan's index — surface it to the user
instead of retrying (resume or abort the prior run first). Exit `0` prints the
new `RUN_ID` and `RUN_DIR` (`references/run-record.md` for the shape written).

**Lock is acquired here, before P3.** The user is never asked to confirm dispatch
for a run that could still fail to start.

Return to hub → P3.
