---
name: realm-concise-query
description: >
  Read-only realm-concise flow. scan (rescan + rescore + regenerate ledger),
  next (peek the queue, no rescan), show (one file's full metrics). All three
  are pure script calls to ../scripts/concise.py — no LLM reasoning, no
  writes beyond the script's own state/ledger files.
---

# realm-concise — query

Triggered by: `/realm-concise`, `/realm-concise scan [project]`, `/realm-concise next [project] [-n N]`, `/realm-concise show <file>`.

Default projects (workspace `CLAUDE.md`): `knowledge-craft`, `backoffice-main`. A bare `/realm-concise` or `/realm-concise scan` with no project arg runs against both.

## `scan`

```bash
python3 "<realmConciseSkillDir>/scripts/concise.py" scan --root <projectDir> --min-loc 450
```

One call crawls, scores, merges into `<projectDir>/.realm/concise-state.json` (preserving existing `status`/`reason`/`adr` per file), and regenerates `<projectDir>/docs/GOD_FILES.md`. Print its stdout verbatim — already caveman-shaped: `score tier loc fanIn test churn path`, top 5 by score.

No agent spawn. No source file reads.

## `next`

```bash
python3 "<realmConciseSkillDir>/scripts/concise.py" next --root <projectDir> -n <N default 3>
```

Pure state read — safe to run repeatedly, never triggers a rescan. Empty queue → say so, suggest `scan`.

## `show <file>`

```bash
python3 "<realmConciseSkillDir>/scripts/concise.py" show --root <projectDir> <file>
```

Full JSON for one tracked file (or its `refactored` history entry if already completed). Used standalone for a quick lookup, and internally by `realm-concise:lifecycle` to check status before gating `approve`/`plan`.

## Output format

```
realm-concise:<project> candidates:<N>

<score> <tier> loc:<loc> fanIn:<n> test:<y/n> churn:<n> <path>
...

-> /realm-concise recommend <top path> | /realm-concise next -n 5
```
