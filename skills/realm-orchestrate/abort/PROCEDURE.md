# abort — drop the active run

Only reached when the routing guard already confirmed `ORCH_ACTIVE=true`. Drop
caveman for this whole flow — this is a confirmation gate, ambiguity here is
costly.

## Step 1 — Warn, plainly, in normal English

```bash
python3 "<realmOrchestrateSkillDir>/scripts/orchestrate.py" status --project-root .
```

Render a warning from that output:

```
⚠ ABORT ORCHESTRATION <RUN_ID>
  plan: <PLAN>   wave <CURRENT_WAVE> of <total waves>   <N> bundles DONE

  Files this run touched will no longer be tracked by orchestration.
  Uncommitted changes stay on disk exactly as they are. Committed work stays
  in history. Nothing is reverted — abort never runs git.

  Type ABORT <RUN_ID> to confirm, or anything else to cancel.
```

## Step 2 — Require the literal confirmation

Wait for the user's next message. Proceed **only** if it is exactly
`ABORT <RUN_ID>` (the run id from Step 1, verbatim). Anything else — including a
plain "yes" — means STOP, do not call `abort`, tell the user the run is still
active.

## Step 3 — Abort

```bash
python3 "<realmOrchestrateSkillDir>/scripts/orchestrate.py" abort --project-root . --confirm <RUN_ID>
```

The script sets the run `ABORTED`, releases the lock, appends it to
`orchestrate-state.json` history with its `runDir` (so it stays traceable), and
prints every `filesChanged` path as "no longer tracked." **Never** follow this
with a git command of any kind — not `status`, not `diff`, nothing. The
working tree is explicitly out of scope for this flow.

Print the script's output verbatim, then resume caveman mode.
