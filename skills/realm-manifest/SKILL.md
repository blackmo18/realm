---
name: realm-manifest
description: >
  Vault-write step in the realm pipeline. Spawns realm-agent-write (haiku) which validates YAML frontmatter, applies caveman compression inline, commits all nodes to the Obsidian vault, updates cross-links, creates session log, and archives the draft. Single-agent pipeline — no separate compress step. The ONLY realm skill that writes to the vault. Must run after realm-phase.
origin: realm
---

# realm-manifest

Commit staged draft to Obsidian. Third skill in realm pipeline.

## When to Use

| Trigger | Example |
|---|---|
| After reviewing realm-phase output | "commit realm", `/realm-manifest`, "manifest" |
| Draft reviewed, ready to write | No changes needed to staged content |
| Applying manually edited draft | Edited `.realm/manifest-draft.md` before committing |

## When NOT to Use

- `.realm/realm-state.json` missing → `/realm-forge` first
- `phase.draftReady != true` → `/realm-phase` first (hard guard)
- `.realm/manifest-draft.md` missing → `/realm-phase` to regenerate
- Unsatisfied with draft → edit `.realm/manifest-draft.md` manually, then re-invoke

---

## Procedure

This skill spawns one agent. Do not perform the steps yourself.

### Step 1 — Determine project root

Use the current working directory as `projectRoot`. Verify `.realm/realm-state.json` exists before proceeding. If missing: print `No realm state. Run /realm-forge then /realm-phase.` and STOP.

### Step 2 — Spawn write agent (haiku)

Spawn agent `realm-agent-write` with this prompt:

```
projectRoot: <absolute path to project root>

Validate, compress, and write the staged manifest draft to the vault.
Follow the full procedure in your instructions.
```

Wait for completion. Surface the agent's summary to the user.
