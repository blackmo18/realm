---
name: realm-facts-link
description: >
  Relate two facts (related / depends_on / supersedes). Pure script call — resolves both ids,
  updates the graph edge, and reindexes. No LLM reasoning beyond picking which relation applies.
---

# realm-facts — link

Triggered by: `/realm-facts link <id> --related <id2>`, `--depends-on <id2>`, `--supersedes <id2>`.

## Step 0 — Guard

```bash
python3 "<realmFactsSkillDir>/scripts/facts.py" state --project-root .
```

`FACTS_CONNECTED=false` → `No facts repo connected. Run /realm-facts forge first.` STOP.

## Step 1 — Pick the relation

- `related` — the two facts are relevant to each other, no directionality implied.
- `depends_on` — this fact's behavior assumes the other fact holds (used by `ingest --deps`).
- `supersedes` — this fact replaces the other (single target, not a list).

If the user just says "link A and B" with no relation named, default to `related`.

## Step 2 — Call the script

```bash
python3 "<realmFactsSkillDir>/scripts/facts.py" link \
  --facts-root <local-path> --fact <id> --related <id2>
# or --depends-on <id2>  /  --supersedes <id2>  (repeatable for --related/--depends-on)
```

Unknown target id → script exits non-zero with `link: related target not found: <id2>`.
Surface it verbatim; suggest `/realm-facts recall <id2>` to check the id is right.

## Step 3 — Print summary

```
realm-facts:link complete

  <id> related+=[<id2>]

→ /realm-facts recall <id> --trace
```
