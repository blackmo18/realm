# resume — continue an interrupted run

Only reached when the routing guard already confirmed `ORCH_ACTIVE=true`. Never
re-runs P1 (analyze) or P2 (bundle) — the bundle plan already exists in `run.json`.
Jumps straight back into P4/P5 territory.

## Step 1 — Load the anchor

```bash
python3 "<realmOrchestrateSkillDir>/scripts/orchestrate.py" resume --project-root .
```

Returns `RESUME_ANCHOR` (shape: `references/run-record.md`). Read `RUN_DIR`,
`STATUS`, `ALL_DONE`, `FINISHED`, `CURRENT_WAVE`, `CURRENT`, `NEXT_WAVE`, `NEXT`.

**`ALL_DONE=true` means every wave already finished but the run was never closed**
(the orchestrator that ran it stopped before P7's `finish` call — a common miss).
Skip straight to P7 (`references/report-template.md`) and `orchestrate.py finish`.
Do not re-dispatch anything — `CURRENT`/`NEXT` will read `none` in this case, which
is correct, not an error.

## Step 2 — Rebuild only what's needed, from `run.json`

Read `<RUN_DIR>/run.json` (one file, not the whole vault). Reconstruct, for the
current wave only:

- `PLAN_SLICE` per bundle — from `bundles[].tasks` + `bundles[].files` already
  stored (do not re-read the original plan file unless a task description is too
  thin to dispatch from).
- `UPSTREAM_EXPORTS` — from the `exports` field of every bundle already `DONE`
  (relayed verbatim, same as a normal P4 dispatch — `references/contracts.md` §1).

## Step 3 — Re-dispatch `CURRENT`

**Correctness rule:** every bundle listed `IN_PROGRESS` in `CURRENT` never
returned a RESULT — it is unverified, not done. Re-dispatch it from scratch at
its stored `attempt` number (do not bump it — the interruption isn't a failed
attempt). Bundles listed `DONE` are skipped. `BLOCKED`/`PARTIAL` bundles use the
FIX_DISPATCH path (`dispatch/PROCEDURE.md` retry section) at their next attempt.

Then continue exactly as a normal run: `wave-start` (if not already
`IN_PROGRESS`) → dispatch → `dispatch/PROCEDURE.md` P4 Step A onward →
`verify/PROCEDURE.md` P5/P6 → `NEXT_WAVE`/`NEXT` become the following wave.

