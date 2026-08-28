# Run Record — Schema Reference

Canonical shape of every file `scripts/orchestrate.py` owns. Nothing outside the
script writes these — read them, never hand-edit them.

## `.realm/orchestrate-state.json` — the lock

Gitignored, one per project. `activeRun` is the lock; `null` means no run is in
progress.

```json
{
  "version": 1,
  "activeRun": { "runId": "ADR-003-task-orchestration", "runDir": "<abs path>", "planPath": "plan-index.md", "startedAt": "<iso>" },
  "history": [
    { "runId": "ADR-002-task-orchestration", "runDir": "<abs path>", "status": "COMPLETE", "endedAt": "<iso>" }
  ]
}
```

Every history entry carries `runDir` — the execution folder it was spawned from —
so a past run is always traceable back to its vault record even after the lock
releases.

## `<runDir>/run.json` — single source of truth

Lives in the vault under
`<projectDir>/orchestration/ADR-<NNN>-task-orchestration/run.json`. Survives a
`.realm/` wipe or fresh clone; `orchestrate-state.json` is only a pointer to it.

```json
{
  "runId": "ADR-003-task-orchestration",
  "index": 3,
  "planPath": "plan-index.md",
  "planSlug": "plan-index",
  "projectSlug": "demo",
  "status": "IN_PROGRESS",
  "startedAt": "<iso>", "updatedAt": "<iso>", "endedAt": null,
  "currentWave": 2,
  "waves": [
    { "wave": 1, "status": "DONE", "bundles": ["B1", "B2"], "summaryFile": "wave-1.md", "endedAt": "<iso>" },
    { "wave": 2, "status": "IN_PROGRESS", "bundles": ["B3"], "summaryFile": null, "endedAt": null }
  ],
  "bundles": [
    {
      "id": "B1", "name": "", "wave": 1, "class": "MECHANICAL", "model": "haiku",
      "tasks": ["T1", "T2"], "files": ["a.ts"], "dependsOn": [],
      "attempt": 1, "status": "DONE", "planCheck": "pass", "review": "CLEAN",
      "filesChanged": ["a.ts"], "exports": ["fn — a.ts — (x:number)=>string"],
      "blockerNeeds": null, "updatedAt": "<iso>"
    }
  ]
}
```

- Run `status`: `IN_PROGRESS | COMPLETE | ABORTED`.
- Wave `status`: `PENDING | IN_PROGRESS | DONE`.
- Bundle `status`: `PENDING | IN_PROGRESS | DONE | PARTIAL | BLOCKED | ABORTED`.
- `exports` is `RESULT.EXPORTS` relayed verbatim (contracts.md §3) — the next
  wave's `UPSTREAM_EXPORTS` comes straight from here, no re-derivation.

## `<runDir>/index.md` — human/Obsidian view

Rendered by `orchestrate.py` on every mutating command (`start`, `wave-start`,
`bundle-status`, `wave-done`, `finish`, `abort`, `render`). Never hand-edited.
Contains: run header, waves table, bundles table, a Blockers section (only
bundles with `BLOCKED` + non-empty `blockerNeeds`), and an Aborted banner when
`status: ABORTED`.

## `<runDir>/wave-<n>.md` — per-wave summary

Written once by `wave-done`, after every bundle in that wave reaches `DONE` —
`wave-done` refuses otherwise. Auto-rendered table (bundle, class, attempt,
status, plan check, review, files changed, exports) plus an optional `--note`
passed through as free prose. This is the durable "wave summary" record.

## `RESUME_ANCHOR` — `orchestrate.py resume` stdout, not a file

```
RESUME_ANCHOR
RUN_ID=ADR-003-task-orchestration
RUN_DIR=<abs path>
PLAN=plan-index.md
STATUS=IN_PROGRESS
ALL_DONE=false
FINISHED=B1:DONE,B2:DONE
CURRENT_WAVE=2
CURRENT=B3:IN_PROGRESS,B4:DONE
NEXT_WAVE=3
NEXT=B5,B6
UPDATED=<iso>
```

**Resume correctness rule:** a bundle shown `IN_PROGRESS` in `CURRENT` never
returned a RESULT before the interruption — it is unverified, not done. Resume
always re-dispatches it at the same attempt number; never assume it finished.

**`ALL_DONE=true`** means every wave already reached `DONE` but `finish` was never
called — `run.status` is still `IN_PROGRESS` and the lock is still held (the
orchestrator that ran it stopped before P7). `CURRENT`/`NEXT` will both read `none`
in this state; that's correct, not a bug. `orchestrate.py start` refuses a second
run in this state exactly like any other active run, but names it explicitly in the
block message so it doesn't read as a stuck lock. `orchestrate.py resume` also
surfaces `ALL_DONE=true` — the fix is `orchestrate.py finish`, not re-dispatch.
