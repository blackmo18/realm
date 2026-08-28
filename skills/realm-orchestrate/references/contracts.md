# realm-orchestrate — Canonical Block Contracts

Single source of truth for every block exchanged in this pipeline. Phase files cite
this — do not re-copy filled templates elsewhere. Field meaning only, no duplication.

## 1. DISPATCH — orchestrator → `realm-agent-plan-implementor` (first attempt)

```
You are realm-agent-plan-implementor. Implement only this bundle.

Use TDD:
1. Write or update tests for the requested behavior.
2. Confirm RED before implementation.
3. Implement the smallest correct change.
4. Run tests → GREEN.
5. Return a compact ---RESULT--- block.

Do not read unrelated plan sections.
Do not touch PEER_FILES. If task is ambiguous → BLOCKED.

WAVE: <n>
ATTEMPT: 1 of 2
BUNDLE_ID: <B1|B2|...>
SERVICE: <kc | medusa | bo>
CWD: <dir to run TEST_CMD/TYPECHECK_CMD from>
TASKS:
  - <task id>: <description>   # ordered; implement top to bottom
AFFECTED_FILES: <files this bundle creates/edits>
PEER_FILES: <files owned by other parallel bundles — DO NOT TOUCH>
NON_GOALS: <explicitly out of scope for this bundle>
UPSTREAM_EXPORTS:
  - <symbol> — <path> — <signature/type>    # from prerequisite bundles' RESULT.EXPORTS, or "none"
PLAN_SLICE: <exact plan lines for these tasks only>
TEST_CMD: <how to run tests, e.g. cd knowledge-craft && pnpm test>
TYPECHECK_CMD: <per-service typecheck command>
DONE_MEANS: all tasks implemented + all tests pass
ON_AMBIGUITY: BLOCKED — do not guess
```

`UPSTREAM_EXPORTS` replaces prose `PREVIOUS_OUTPUTS` — it is the prior bundle's
`RESULT.EXPORTS` relayed verbatim, not a summary the implementor must parse.

## 2. FIX_DISPATCH — orchestrator → `realm-agent-plan-implementor` (re-dispatch, attempt 2)

Prepend to the DISPATCH block above (same bundle, `ATTEMPT: 2 of 2`):

```
FIX_FOR: <original bundle id>
PRIOR_STATUS: DONE | PARTIAL | BLOCKED
UNSATISFIED_TASKS:
  - <task id>: <what Step A found missing>
REVIEW_FINDINGS:
  - <path:line: 🔴 ...>          # verbatim blocking lines from ---REVIEW---, or "none"
DO_NOT_REDO: <task ids already satisfied — leave their code alone>
```

Attempt 2 of a MECHANICAL bundle drops the Haiku override (see `../dispatch/PROCEDURE.md`
escalation rule) — inherit chat model instead.

## 3. RESULT — `realm-agent-plan-implementor` → orchestrator

```
---RESULT---
BUNDLE: <id>
STATUS: DONE | PARTIAL | BLOCKED
TASKS_DONE:
  - <task id>: done | missing | blocked — <one line>
FILES_CHANGED:
  - <path>: <what changed>
TESTS:
  - <command>: pass | fail | not-run — <reason if not pass>
TDD_EVIDENCE:
  - tests added/updated: <list>
  - red confirmation: <how RED was confirmed>
  - green confirmation: <how GREEN was confirmed>
EXPORTS:
  - <symbol> — <path> — <signature>     # what downstream bundles can import; "none"
ASSUMPTIONS:
  - <judgment call made where PLAN_SLICE was thin, or "none">
DEVIATIONS:
  - <file touched outside AFFECTED_FILES, or approach differing from PLAN_SLICE, or "none">
CONFIDENCE: high | med | low
BLOCKER_NEEDS: <none or exact ask>
SUMMARY: <human-readable — what shipped, in prose>
---END---
```

`EXPORTS` is the machine channel consumed as next-wave `UPSTREAM_EXPORTS`. `SUMMARY`
stays human prose for the P7 report. Non-empty `DEVIATIONS` or `CONFIDENCE: low` forces
Step B review even on a bundle classified MECHANICAL.

## 4. REVIEW_REQUEST — orchestrator → `cavecrew-reviewer` (spawn prompt, cold)

Wrapper only — `cavecrew-reviewer.md` itself is not modified. This is additive over its
native finding-line format.

```
Review code quality only. Plan satisfaction already verified — do not re-check it.
Do not check test coverage — already verified.

BUNDLE: <id>
DIFF_CMD: <git diff command scoping this bundle's change>
FILES_CHANGED:
  - <path>: <what changed>   # read only these files
KNOWN_ASSUMPTIONS:
  - <assumption from RESULT.ASSUMPTIONS, or "none">   # flag if any looks wrong
SCOPE: correctness, security, error handling, immutability, dead code
OUT_OF_SCOPE: architecture, naming taste, test strategy, formatting nits

Return exactly:
---REVIEW---
BUNDLE: <id>
VERDICT: CLEAN | SHOULD_FIX | BLOCKING
<path:line: <emoji> <severity>: <problem>. <fix>.>
totals: N🔴 N🟡 N🔵
---END---
```

`VERDICT` collapses totals into one field the orchestrator branches on directly —
`BLOCKING` (any 🔴), `SHOULD_FIX` (🟡 only), `CLEAN` (🔵 only or none). No eyeballing
emoji counts.

## 5. WAVE LEDGER — orchestrator state, script-owned and persisted

```
WAVE: <n>
| bundle | class | model | attempt | status | plan | review   | exports |
|--------|-------|-------|---------|--------|------|----------|---------|
| B1     | MECH  | haiku | 1       | DONE   | ✓    | CLEAN    | 2       |
| B2     | COMPLEX | inherit | 2   | DONE   | ✓    | SHOULD_FIX | 0     |
```

Tracks class/model/attempt/status/plan/review/exports per bundle across the whole
run. This table is a view over `<runDir>/run.json` — `scripts/orchestrate.py` is the
only writer (`start`, `wave-start`, `bundle-status`, `wave-done`). The orchestrator
never hand-edits it; every mutation is one script call
(`../dispatch/PROCEDURE.md`, `../verify/PROCEDURE.md`). Full schema:
`run-record.md`.

## 6. RESUME_ANCHOR — `orchestrate.py resume` stdout

```
RESUME_ANCHOR
RUN_ID=<id>
RUN_DIR=<abs path>
PLAN=<path>
STATUS=IN_PROGRESS
FINISHED=B1:DONE,B2:DONE
CURRENT_WAVE=<n>
CURRENT=B3:IN_PROGRESS,B4:DONE
NEXT_WAVE=<n+1>
NEXT=B5,B6
UPDATED=<iso>
```

A bundle in `CURRENT` marked `IN_PROGRESS` never returned a RESULT — treat it as
unverified and re-dispatch from scratch at its stored attempt number. Consumed by
`../resume/PROCEDURE.md`. Full schema: `run-record.md`.
