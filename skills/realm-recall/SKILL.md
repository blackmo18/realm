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

Read `_shared/realm-conventions.md` before executing.

**ZERO vault writes. Read-only.**

### Step 0 — Guard checks

1. Read `.realm/realm-state.json`. If missing: `No realm state. Run /realm-forge first.` STOP.
2. Read `vaultPath`, `projectSlug`, `projectDir`.
3. Scan `<projectDir>/` for nodes across `decisions/`, `functions/`, `classes/`, `systems/`, `discoveries/`.
4. No nodes: `No nodes in vault yet. Run /realm-phase then /realm-manifest.` STOP.

### Step 1 — Parse query + flags

- **topic**: everything before first `--` flag
- **flags**: `--trace`, `--full`, `--deps`, `--count`, `--expand <id>`

### Step 2 — Resolve topic to nodes (NL → vault)

Try in order, first match wins:

**2a — Direct node ID match**
Topic exactly matches a node's `id:` frontmatter field → single node.

**2b — Tag match**
Topic matches tag in any node's `tags: [...]` array.
- Strip `@`/`#` prefix if present.
- Multi-tag `auth,security` → union.
→ tag cluster.

**2c — Title / filename fuzzy match**
Lowercase-compare topic against node filenames and first heading.
- `"session refresh"` → matches `session-refresh.md` or node titled "Session Refresh Strategy".
→ fuzzy cluster.

**2d — Semantic keyword search**
Search `Compressed:` sections for topic keywords.
- `"why JWT"` → scan for "JWT", "token format" → matching decision nodes.
→ keyword cluster.

**2e — No match**
```
No nodes found for: "<topic>"
Available tags: <list top 10>
Available IDs:  <list first 20>
Try: /realm-recall @<tag>  or  /realm-status for full node list
```
STOP.

### Step 3 — Apply --count (if flag present)

Estimate for matched nodes:
- Compressed: ~20 tokens/node
- Full prose: ~120 tokens/node
- Per dep: +20 tokens

Print:
```
/realm-recall <topic> --count

  Matched nodes: <N>  (decisions: X, functions: Y, classes: Z)
  Deps (--deps): +<N> additional nodes

  Cost if compressed (default): ~<N×20> tokens
  Cost if --full:               ~<N×120> tokens
  Cost if --trace:              <10 tokens

Run without --count to pull content.
```
STOP.

### Step 4 — Load node content

**Default (compressed):** for each matched node:
1. Read YAML frontmatter (id, type, status, tags, created, updated).
2. Read `Compressed:` section.
3. Extract link arrays: `depends_on`, `called_by`, `implementations`, `dependents`.

**If --full:** read entire file.

**If --deps:** resolve each `depends_on: [[...]]` link → load those nodes (compressed). Include as "Dependencies" subsection.

### Step 5 — Build output (caveman-compressed)

Apply caveman rules to all output: drop articles/filler, use fragments, keep technical data exact. Omit zero/empty fields silently.

**Single-node result:**
```
<id> [<type>·<status>] #tag1 #tag2
<one-liner from Compressed: section>
sig: <signature if function>
deps:[[A]][[B]]  calls:[[C]][[D]]
[Full prose block if --full]
→ --full | --trace | --deps
```

**Cluster result:**
```
recall:<topic> <N>nodes

1 <type>:<id> #tags
  <one-liner>
  deps:[[A]]  calls:[[B]]

2 <type>:<id> #tags
  <one-liner>
  impl:[[C]][[D]]

[...rest of nodes...]
→ <id> --full | <topic> --deps | <topic> --trace
```

**--trace result:**
```
tree:<topic>

<type>:<id>
├─impl: <type>:<id>
│  ├─deps:[[A]][[B]]
│  └─calls:[[C]][[D]]
└─impl: <type>:<id>
   └─deps:[[E]]

~<N×20>t compressed. Obsidian graph for visual.
```

### Step 6 — Footer (caveman-compressed)

Single line per relevant next step only. Omit steps that don't apply to the query.

```
recall done · <N>nodes · ~<estimated>t · mode:<compressed|full|trace>
→ most relevant next: /realm-recall <id> --full | --deps | --trace
```

---

## Token Efficiency

| Query | Tokens | vs Full Doc |
|-------|--------|-------------|
| Single node (compressed) | ~20 | 85% savings |
| Single node + deps | ~80 | 92% savings |
| Tag cluster @auth, 10 nodes | ~200 | 90% savings |
| Tag cluster --trace | <10 | 99% savings |
| Single node (full prose) | ~120 | baseline |

Strategy: default compressed → explore in Obsidian → expand selectively with `--full` or `--deps`.
