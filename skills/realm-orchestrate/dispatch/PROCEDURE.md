# dispatch — P3 Recommend + confirm, P4 Dispatch (TDD, wave by wave)

## P3 — Recommend agent count + confirm

State: number of bundles, which run parallel vs sequential, rough token cost (more
parallel = more tokens but faster). Recommend agent count. Default cap **3 parallel
agents**; user can override.

Include the model routing table from `../references/classification.md` — one row per
bundle (or group bundles that share the same model):

```
┌──────────────┬─────────────────────┬────────────────────────────────────────────┐
│    Bundle    │        Model        │                   Reason                   │
├──────────────┼─────────────────────┼────────────────────────────────────────────┤
│ B2           │ Sonnet (inherit —   │ Complex: integration into existing route,  │
│              │ no override)        │ atomic transaction, test suite             │
├──────────────┼─────────────────────┼────────────────────────────────────────────┤
│ B1, B3, B4,  │ Haiku (explicit     │ Mechanical: additive/new files, fully      │
│ B5, B6       │ override)           │ specified in plan                          │
└──────────────┴─────────────────────┴────────────────────────────────────────────┘
```

User can override any row before confirming.

Drop caveman here — ask plainly and wait for confirmation before spawning anything.

**After user confirms → go directly to P4.** No validator prime. No pre-warmed agents.

## P4 — Dispatch realm-agent-plan-implementor agents (TDD)

**Wave model — implement then check, never mix in one spawn batch.**

Each cycle is three steps in **separate messages**:

```
Step A — implement (P4):  spawn realm-agent-plan-implementor agent(s) for this wave only
Step B — check (P5):      plan satisfaction + code review for each returned bundle
                          (sequential — one bundle at a time)
Step C — next wave:       only after Step B clears every bundle in this wave
```

**Before spawning, mark the wave started:**

```bash
python3 "<realmOrchestrateSkillDir>/scripts/orchestrate.py" wave-start --project-root . --wave <n>
```

For each bundle about to be spawned, record it `IN_PROGRESS` first — this is what
makes resume correct if the run is interrupted mid-wave:

```bash
python3 "<realmOrchestrateSkillDir>/scripts/orchestrate.py" bundle-status --project-root . \
  --bundle <id> --status IN_PROGRESS --attempt <n>
```

For each bundle, spawn a `realm-agent-plan-implementor` agent via the Task tool using the DISPATCH
block from `../references/contracts.md` §1 (fill every field, including
`UPSTREAM_EXPORTS` from prerequisite bundles' `RESULT.EXPORTS`). Run independent
bundles **in parallel** (multiple Task calls in one message — implementors only). Run
dependent bundles **after** their prerequisite returns DONE.

**Hard cap:** max **3 parallel implementors** per wave.

**Model routing** — mechanical → Haiku, complex → inherit. Agent frontmatter `model:`
overrides Task inheritance — `realm-agent-plan-implementor.md` must **not** set `model:`. Table:
`../references/classification.md`. User override from P3 takes precedence.

The slice is the spec; the agent executes it. Expected output: RESULT block,
`../references/contracts.md` §3.

For a trivial single-file bundle, use `cavecrew-builder` directly (cheaper). Use
`realm-agent-plan-implementor` whenever tests must run.

## Retry / fix-dispatch (used from P5, entry point lives here)

- **Auto-retry cap: 2 attempts per bundle.** Attempt 3 → stop, surface to user instead
  of re-dispatching.
- **Escalation exception:** attempt 2 of a bundle classified MECHANICAL drops the Haiku
  override and inherits the chat model. This is the *only* sanctioned deviation from
  P3's classification — no other self-escalation.
- Re-dispatch uses the FIX_DISPATCH block (`../references/contracts.md` §2) — carries
  `UNSATISFIED_TASKS`, `REVIEW_FINDINGS` (verbatim 🔴 lines), and `DO_NOT_REDO` so the
  implementor never blindly redoes tasks that already passed. Record the retry before
  spawning: `bundle-status --bundle <id> --status IN_PROGRESS --attempt 2`.
- `STATUS: BLOCKED` → surface `BLOCKER_NEEDS` verbatim, wait for user. **Never**
  re-dispatch a BLOCKED bundle with a guessed answer — only re-dispatch once the user
  supplies the missing detail. Record it: `bundle-status --bundle <id> --status BLOCKED
  --attempt <n> --blocker "<BLOCKER_NEEDS verbatim>"`.

Never mix reviewer Task calls and implementor Task calls in the same message. Never
launch the next implementor wave until every bundle in the current wave passes P5.

Return to hub → P5 (`../verify/PROCEDURE.md`).
