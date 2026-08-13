---
name: realm-facts:ingest
description: >
  Produce a FACT_BUNDLE for a coding agent. Pure script call — the bundle shape is fixed
  (see ../references/bundle-format.md); no LLM reasoning beyond picking impl/context/full.
---

# realm-facts — ingest

Triggered by: `/realm-facts ingest <id>`, `/realm-facts ingest <id> --bundle context|full`, `--deps`.

## Step 0 — Guard

```bash
python3 .claude/skills/realm-facts/scripts/facts.py state --project-root .
```

`FACTS_CONNECTED=false` → `No facts repo connected. Run /realm-facts forge first.` STOP.

## Step 1 — Pick bundle mode

Default `impl` (id + compressed + deps + repo_refs + drift_policy — the minimal handoff).
`context` adds title/domain/tags/owners. `full` adds the entire body. See
`../references/bundle-format.md` for the exact shape of each.

## Step 2 — Call the script

```bash
python3 .claude/skills/realm-facts/scripts/facts.py bundle \
  --facts-root <local-path> --fact <id> --bundle <impl|context|full> [--deps]
```

Fact not in the index → script exits non-zero with `bundle: fact not found: <id>`. Suggest
`/realm-facts recall <id>` to confirm the id, or `/realm-facts sync` if the index is stale.

## Step 3 — Hand off

Print the script's `FACT_BUNDLE:` block verbatim — it is meant to be pasted directly into
another agent's prompt or used as session context. Do not wrap it in extra prose.
