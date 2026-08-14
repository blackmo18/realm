---
name: realm-facts-recall
description: >
  Query facts by domain, tag, status, or free-text. Reads facts-index.json only — never a live
  scan of the fact tree. LLM ranks/formats results; the script does the filtering.
---

# realm-facts — recall

Triggered by: `/realm-facts recall <query>`, `/realm-facts recall <query> --domain <d>`, `--tag <t>`, `--status <s>`.

## Step 0 — Guard

```bash
python3 "<realmFactsSkillDir>/scripts/facts.py" state --project-root .
```

`FACTS_CONNECTED=false` → `No facts repo connected. Run /realm-facts forge first.` STOP.

## Step 1 — Search

```bash
python3 "<realmFactsSkillDir>/scripts/facts.py" search \
  --facts-root <local-path> --query "<query>" [--domain <d>] [--tag <t>] [--status <s>]
```

This reads `facts-index.json` only. If it looks stale (a fact you know exists doesn't show up),
run `/realm-facts sync` first rather than falling back to a filesystem search.

## Step 2 — Format output

No matches:

```
recall:<query> no facts matched
→ /realm-facts new <domain> <id>  if this should exist
```

Matches — script stdout is already one block per fact (`<id> [<domain>·<status>] #tags` then
the compressed line). Pass it through; add ranking only if the query is ambiguous enough that
result order matters (rank by tag/domain match count, then alphabetical).

```
recall:<query> <N>facts

<script stdout, as-is>

→ /realm-facts ingest <id> --bundle impl  |  /realm-facts link <id> --related <other>
```

## Step 3 — --deps expansion (optional)

If the user wants dependency context beyond what `search` returns, run
`facts.py bundle --facts-root <local-path> --fact <id> --deps` for the matched fact(s) and
append its `deps:` block to the output.
