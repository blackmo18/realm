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

- `PLAN_SLICE` per bundle — read verbatim from `bundles[].planSlice`, captured
  once at P2 (`references/run-record.md`). Only re-read the original plan file
  when `planSlice` is empty (a legacy or manually-authored bundles-file that
  predates this field) or too thin to dispatch from.
- `model` per bundle — read verbatim from `bundles[].model`. `bundle-status`
  already applied the MECHANICAL attempt-≥2 escalation when the interrupted
  attempt was recorded, so this field is always the model the re-dispatch must
  use — do not recompute the escalation rule by hand.
- `UPSTREAM_EXPORTS` — from the `exports` field of every bundle already `DONE`
  (relayed verbatim, same as a normal P4 dispatch — `references/contracts.md` §1).

## Step 3 — Re-dispatch `CURRENT`

**Correctness rule:** every bundle listed `IN_PROGRESS` in `CURRENT` never
returned a RESULT — it is unverified, not done. Re-dispatch it from scratch at
its stored `attempt` number (do not bump it — the interruption isn't a failed
attempt). Bundles listed `DONE` are skipped.

`PARTIAL` bundles use the FIX_DISPATCH path (`dispatch/PROCEDURE.md` retry
section) at their next attempt — re-dispatch normally.

`BLOCKED` bundles are **not** re-dispatched on resume. Same hard rule as a
normal run (`dispatch/PROCEDURE.md` retry section): surface `blockerNeeds`
verbatim to the user and wait. Only re-dispatch a `BLOCKED` bundle once the
user supplies the missing detail — never guess it just because the run is
being resumed.

Then continue exactly as a normal run: `wave-start` (if not already
`IN_PROGRESS`) → dispatch → `dispatch/PROCEDURE.md` P4 Step A onward →
`verify/PROCEDURE.md` P5/P6 → `NEXT_WAVE`/`NEXT` become the following wave.

