---
name: realm-manifest
description: >
  Vault-write step in the realm pipeline. Orchestrates two agents: realm-agent-compress (sonnet) validates and compresses the staged draft, then realm-agent-write (haiku) commits all nodes to the Obsidian vault, updates cross-links, creates session log, and archives the draft. The ONLY realm skill that writes to the vault. Must run after realm-phase.
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

This skill orchestrates two agents sequentially. Do not perform the steps yourself.

### Step 1 — Determine project root

Use the current working directory as `projectRoot`. Verify `.realm/realm-state.json` exists before proceeding. If missing: print `No realm state. Run /realm-forge then /realm-phase.` and STOP.

### Step 2 — Spawn compress agent (sonnet)

Spawn agent `realm-agent-compress` with this prompt:

```
projectRoot: <absolute path to project root>

Validate and compress the staged manifest draft at <projectRoot>/.realm/manifest-draft.md.
Follow the full procedure in your instructions.
```

Wait for completion. If the agent reports an error or guard failure: surface the message to the user and STOP.

### Step 3 — Spawn write agent (haiku)

On compress success, spawn agent `realm-agent-write` with this prompt:

```
projectRoot: <absolute path to project root>

Write the compressed manifest draft to the vault.
Follow the full procedure in your instructions.
```

Wait for completion. Surface the write agent's summary to the user.
