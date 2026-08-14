---
name: realm-facts-sync
description: >
  Pull the latest approved facts from the central repo, reindex, and stamp lastSync. Pure
  script/git flow — no LLM reasoning.
---

# realm-facts — sync

Triggered by: `/realm-facts sync`, "pull latest facts", after a Teams approval notice.

## Step 0 — Guard

```bash
python3 "<realmFactsSkillDir>/scripts/facts.py" state --project-root .
```

`FACTS_CONNECTED=false` → `No facts repo connected. Run /realm-facts forge first.` STOP.
Otherwise extract `FACTS_LOCAL_PATH` and `FACTS_BRANCH` from the printed lines.

## Step 1 — Pull

```bash
git -C <local-path> pull origin <branch>
```

## Step 2 — Reindex

```bash
python3 "<realmFactsSkillDir>/scripts/facts.py" index --facts-root <local-path>
```

## Step 3 — Stamp lastSync

```bash
python3 "<realmFactsSkillDir>/scripts/facts.py" state --project-root . --stamp-sync
```

## Step 4 — Print summary

```
realm-facts:sync complete

  pulled: <branch> @ <local-path>
  facts:  <N> across <D> domains
  lastSync: <timestamp>

→ /realm-facts recall <topic>
```
