---
name: realm-facts:submit
description: >
  Submit a fact for review — validate --mr-ready, move status to review, branch, open a GitLab
  MR, and post a Teams notification. Follows the MCP-first / manual-fallback ladder in
  ../references/mr-flow.md. Never pushes straight to main.
---

# realm-facts — submit

Triggered by: `/realm-facts submit <id>`.

## Step 0 — Guard

```bash
python3 .claude/skills/realm-facts/scripts/facts.py state --project-root .
```

`FACTS_CONNECTED=false` → `No facts repo connected. Run /realm-facts forge first.` STOP.

## Step 1 — Validate mr-ready

```bash
python3 .claude/skills/realm-facts/scripts/facts.py validate --facts-root <local-path> --fact <id> --mr-ready
```

Non-zero exit → surface the `<path>:<field>: <problem>` lines, STOP. Common misses: empty
`evidence`, empty `reviewers` — send the user back to `/realm-facts link` or a manual edit,
then re-run this step. Do not proceed to Step 2 until this passes.

## Step 2 — Move to review status

```bash
python3 .claude/skills/realm-facts/scripts/facts.py set-status --facts-root <local-path> --fact <id> --status review
```

## Step 3 — Branch, MR, notify

Load `../references/mr-flow.md` — it owns the full MCP-first → manual-fallback ladder and the
Teams payload shapes. Follow it exactly: branch `fact/<id>`, labels `realm-facts`/`needs-review`,
MR title `[fact] <title> (<id>)`. **Never push to `main`.**

## Step 4 — Print summary

```
realm-facts:submit complete

  <id>  status: review
  MR: <url>
  Teams: <notified | skipped (REALM_TEAMS_WEBHOOK not set)>

→ /realm-facts review <id>  (reviewer)
```
