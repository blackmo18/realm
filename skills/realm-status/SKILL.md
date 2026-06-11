---
name: realm-status
description: >
  Read-only status check for the realm pipeline. Reads .realm/realm-state.json and prints the vault path, project slug, pipeline state (draftReady, last run timestamps), and the full doc registry (committed/planned/stale). No writes. Use to quickly assess what the vault knows vs what's pending.
origin: realm
---

# realm-status

Inspect realm pipeline state without scanning or writing.

## When to Use

| Trigger | Example |
|---|---|
| Check vault vs staged | "realm status", `/realm-status` |
| Verify init completed | After `/realm-forge` |
| See if draft pending | Before deciding to run `/realm-manifest` |
| Orient at session start | "what does realm know?" |

## When NOT to Use

- Want to scan repo → `/realm-phase`
- Want to write to vault → `/realm-manifest`
- `realm-state.json` missing → will report; run `/realm-forge`

---

## Procedure

This skill delegates entirely to `realm-agent-query` in status mode.

### Step 1 — Spawn query agent

Spawn agent `realm-agent-query` with this prompt:

```
projectRoot: <absolute path to project root>
mode: status

Print the full realm pipeline status report.
Follow the full procedure in your instructions.
```

Wait for completion. Surface the agent's output directly to the user.
