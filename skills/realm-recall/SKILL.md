---
name: realm-recall
description: >
  Natural-language knowledge retrieval from the Obsidian vault. Maps a topic, function name, tag, or freeform phrase to vault nodes and returns compressed context. Replaces realm-pull-obsidian with simpler UX: /realm-recall auth, /realm-recall validateUser, /realm-recall "why JWT". Supports --trace (link structure only), --full (expand prose), and --deps (include dependencies). Zero vault writes. Primary query interface for realm. Maps to /realm:recall intent from sample_usage.md.
origin: realm
---

# realm-recall

Ask vault anything. Get compressed context back.

## Syntax

```bash
/realm-recall <topic>               # NL topic, function name, decision keyword
/realm-recall <topic> --trace       # Link tree only (zero content, <10 tokens)
/realm-recall <topic> --full        # Full prose for matched nodes
/realm-recall <topic> --deps        # Include [[depends_on]] nodes (compressed)
/realm-recall <topic> --count       # Estimate token cost before pulling
/realm-recall <topic> --expand <id> # Expand one node's full prose after compressed view
```

## Examples

```bash
/realm-recall auth
→ All #auth nodes → compressed view (~150 tokens for 10 nodes)

/realm-recall validateUser
→ Direct lookup → function:validateUser compressed + depends_on + called_by (~80 tokens)

/realm-recall "why JWT"
→ Semantic → decision nodes with JWT in title/context → compressed

/realm-recall auth --trace
→ Auth dependency tree, no content (<10 tokens) → explore in Obsidian

/realm-recall auth --deps
→ Auth cluster + all dep nodes, compressed (~200-300 tokens)

/realm-recall validateUser --full
→ Full prose for validateUser (~150 tokens)

/realm-recall #critical-path --count
→ "12 nodes, ~240 tokens compressed, ~1800 tokens full"
```

## When to Use

| Trigger | Example |
|---|---|
| Need context before coding | `/realm-recall auth` |
| Check what calls function | `/realm-recall validateUser --trace` |
| Understand design decision | `/realm-recall "session refresh"` |
| Orient at session start | `/realm-recall overview` |
| Cost estimate before big pull | `/realm-recall @performance --count` |

## When NOT to Use

- `.realm/realm-state.json` missing → `/realm-forge` first
- No nodes in vault → `/realm-phase` then `/realm-manifest` first
- Want to write to vault → `/realm-flourish` or `/realm-manifest`
- Want pipeline health → `/realm-status`

---

## Procedure

This skill parses the query and flags, then delegates all vault reading to `realm-agent-query`.

### Step 1 — Parse query and flags

From invocation args:
- `query`: everything before first `--` flag
- `flags`: collect any of `--trace`, `--full`, `--deps`, `--count`, `--expand <id>`

### Step 2 — Spawn query agent

Spawn agent `realm-agent-query` with this prompt:

```
projectRoot: <absolute path to project root>
mode: recall
query: <parsed query>
flags: <list of flags, e.g. "--full --deps" or empty>

Retrieve vault nodes matching the query and return compressed output.
Follow the full procedure in your instructions.
```

Wait for completion. Surface the agent's output directly to the user.
