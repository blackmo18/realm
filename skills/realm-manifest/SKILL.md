---
name: realm-manifest
description: >
  Vault-write step in the realm pipeline. Reads pendingDrafts from realm-state.json, lists
  available staged drafts (from realm-plan finalize or realm-convey), lets user select which
  to commit. Spawns realm-agent-write (haiku) per selected draft — validates YAML frontmatter,
  applies caveman compression, writes nodes to vault, updates backlinks, archives draft, removes
  from pendingDrafts. The ONLY realm skill that writes to the vault.
origin: realm
---

# realm-manifest

Commit staged draft(s) to Obsidian. Final step in realm pipeline.

## Syntax

```bash
/realm-manifest                          # list pending drafts, prompt selection
/realm-manifest plans/auth-refactor      # commit specific canvas draft by slug
/realm-manifest all                      # commit all pending drafts
```

## When to Use

| Trigger | Example |
|---|---|
| After realm-plan finalize | "commit this", `/realm-manifest` |
| After realm-convey | "manifest", "write to vault" |
| Multiple pending, commit selectively | `/realm-manifest plans/auth-refactor` |
| Commit everything staged | `/realm-manifest all` |

## When NOT to Use

- `.realm/realm-state.json` missing → `/realm-forge` first
- `pendingDrafts` empty → nothing staged yet; run `/realm-plan finalize` or `/realm-convey`
- Unsatisfied with a draft → edit `<draft-path>` manually first, then re-invoke

---

## Procedure

### Step 0 — Guard check

Read `.realm/realm-state.json`. If missing: `No realm state. Run /realm-forge first.` STOP.

Load `pendingDrafts` array. If empty (or field missing):
```
No pending drafts.
Run /realm-plan finalize or /realm-convey to stage nodes.
```
STOP.

### Step 1 — Resolve target draft(s)

**No arg:**
Print pending list and wait for selection:
```
realm-manifest: pending drafts

  [1] plans/auth-refactor   plan     "auth JWT refactor"   2026-06-14
  [2] convey                convey   conversation capture  2026-06-13

Select: (number | slug | all | cancel):
```
Wait for reply. `cancel` or empty → STOP.

**`/realm-manifest <slug>`:**
Match `slug` against `pendingDrafts[].slug`. If no match:
`Draft not found: <slug>. Run /realm-manifest to see pending list.` STOP.

**`/realm-manifest all`:**
Select all entries from `pendingDrafts`.

### Step 2 — Verify draft files exist

For each selected entry, verify `path` file exists (absolute: `<projectRoot>/<entry.path>` for plan drafts; `<projectRoot>/<entry.path>` for convey).

If missing: `Draft file not found: <path>. Stage again with /realm-plan finalize or /realm-convey.` Skip that entry.

### Step 3 — Spawn write agent (haiku) per selected draft

For each selected entry, spawn `realm-agent-write` with:

```
projectRoot: <absolute path to project root>
draftPath: <absolute path to draft file>
slug: <entry.slug | null>

Validate, compress, and write the staged manifest draft to the vault.
Follow the full procedure in your instructions.
```

Wait for each agent to complete before starting the next. Surface agent summary per draft.

### Step 4 — Remove committed entries from pendingDrafts

After each successful agent run:
```bash
python3 "${HOME}/.claude/plugins/marketplaces/realm/scripts/manifest_write.py" \
  --project-root "<projectRoot>" \
  --remove-draft \
  --draft-path "<entry.path>"
```
If exit code non-zero: warn but continue (vault write already succeeded).

### Step 5 — Print summary

```
realm-manifest complete

  committed: <N> draft(s)
    <slug | convey>  →  decisions: X  functions: Y  classes: Z  discoveries: W

  pending remaining: <M>
  [run /realm-manifest to commit remaining]   ← only if M > 0

  next: /realm-status · /realm-recall <topic>
```
