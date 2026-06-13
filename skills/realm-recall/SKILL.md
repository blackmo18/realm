---
name: realm-recall
description: >
  Natural-language knowledge retrieval from the Obsidian vault. Primary interface for querying
  decisions, rejected alternatives, constraints, and discoveries. Maps a topic, decision keyword,
  or freeform phrase ("why JWT", "what was rejected for auth", "constraint on payments") to vault
  ADR and discovery nodes. Supports --trace (link structure only), --full (expand prose),
  --deps (include dependencies). Zero vault writes.
origin: realm
---

# realm-recall

Ask vault anything. Get compressed context back. Optimized for ADR queries.

## Syntax

```bash
/realm-recall <topic>               # NL topic, decision keyword, tag
/realm-recall <topic> --trace       # Link tree only (zero content, <10 tokens)
/realm-recall <topic> --full        # Full prose for matched nodes
/realm-recall <topic> --deps        # Include [[depends_on]] nodes (compressed)
/realm-recall <topic> --count       # Estimate token cost before pulling
/realm-recall <topic> --expand <id> # Expand one node's full prose after compressed view
```

## ADR Query Patterns

The primary reason to use realm-recall — answering questions code can't answer:

```bash
/realm-recall "why JWT"
→ decision nodes where JWT appears in title/context/rationale (~20 tokens)

/realm-recall "what was rejected for auth"
→ ADR nodes with non-empty rejected_alternatives field, #auth tag (~30 tokens)

/realm-recall "constraint on payments"
→ decision nodes with consequences field mentioning payments (~25 tokens)

/realm-recall "has anyone tried websockets"
→ searches rejected_alternatives across all ADRs for websocket mentions

/realm-recall decisions
→ all ADR nodes, compressed (~20 tokens each)

/realm-recall decisions --full
→ full prose for all ADRs including context, rejected, consequences
```

## General Query Examples

```bash
/realm-recall auth
→ All #auth nodes → compressed view

/realm-recall "session refresh"
→ Semantic → decision/discovery nodes matching phrase

/realm-recall auth --trace
→ Auth dependency tree, no content (<10 tokens) → explore in Obsidian

/realm-recall #critical-path --count
→ "12 nodes, ~240 tokens compressed, ~1800 tokens full"
```

## When to Use

| Trigger | Example |
|---|---|
| "Why did we choose X?" | `/realm-recall "why X"` |
| "What did we reject for Y?" | `/realm-recall "rejected for Y"` |
| "Any constraint on Z?" | `/realm-recall "constraint Z"` |
| "Has anyone tried W before?" | `/realm-recall "tried W"` |
| Orient before touching unfamiliar area | `/realm-recall auth` |
| Cost estimate before big pull | `/realm-recall decisions --count` |

## When NOT to Use

- `.realm/realm-state.json` missing → `/realm-forge` first
- No nodes in vault yet → run `/realm-convey` after a session to populate
- Want live code + vault combined → `/realm-fathom`
- Want to write to vault → `/realm-manifest`
- Want pipeline health → `/realm-status`

---

## Procedure

Handle steps 1–5 inline using Read/Glob/Bash. Spawn `realm-agent-query` only as fallback for semantic/NL queries (Step 3d). Never spawn agent for known-node, tag, or filename lookups.

### Step 1 — Parse query and flags

From invocation args:
- `query`: everything before first `--` flag
- `flags`: collect any of `--trace`, `--full`, `--deps`, `--count`, `--expand <id>`

### Step 2 — Read state

Read `<projectRoot>/.realm/realm-state.json`.
If missing: `No realm state. Run /realm-forge first.` STOP.
Extract: `vaultPath`, `projectSlug`, `projectDir`.

Scan `<projectDir>/` for `.md` files across `decisions/`, `discoveries/`, `sessions/`, `work/`.
If none: `No nodes in vault yet. Run /realm-convey to capture decisions, then /realm-manifest.` STOP.

### Step 3 — Resolution ladder (first match wins)

Work 3a → 3b → 3c → 3d in order. Stop at first hit.

**3a — Exact node ID match**

Applies when: query has no spaces, no `@`/`#` prefix, no natural-language words (why/how/what/does/is/rejected/constraint/tried).

```bash
grep -rl "^id: <query>" <projectDir>/
```

If 1+ files found → Read them directly → go to Step 4. No agent spawn.

**3b — Tag cluster**

Applies when: query starts with `@` or `#`, or is a single lowercase word matching a likely tag (e.g. `auth`, `perf`, `security`, `decisions`).

Strip `@`/`#` prefix. For `decisions` keyword: glob `<projectDir>/decisions/*.md` directly.

Otherwise run:
```bash
grep -rl "  - <tag>" <projectDir>/
```

Read all matched files in parallel → go to Step 4. No agent spawn.

**3c — Filename fuzzy match**

Applies when: 3a/3b produced no results, query is 1–2 words with no NL indicators.

Glob: `<projectDir>/**/*<query>*.md` (case-insensitive where supported).
If ≤20 matches → Read matched files → go to Step 4. No agent spawn.
If >20 matches → treat as 3d.

**3d — Semantic / NL fallback (agent justified)**

Applies when: query is multi-word phrase; starts with why/how/what/rejected/constraint/tried/has; is quoted; or 3a–3c returned no results.

For ADR-specific queries (why/rejected/constraint/tried), also grep `decisions/` body text:
```bash
grep -rl "<keyword>" <projectDir>/decisions/
```
If hits found → Read matched files → go to Step 4. No agent spawn.

Otherwise spawn `realm-agent-query`:
```
projectRoot: <absolute path to project root>
mode: recall
query: <parsed query>
flags: <list of flags, e.g. "--full --deps" or empty>
```
Surface agent output directly. STOP.

### Step 4 — Apply flags to loaded nodes

**--count (if flag present):**
Count matched files. Print estimate, then STOP:
```
/realm-recall <query> --count

  Matched nodes: <N>  (decisions: X, discoveries: Y, sessions: Z)

  Cost if compressed (default): ~<N×20> tokens
  Cost if --full:               ~<N×120> tokens
  Cost if --trace:              <10 tokens

Run without --count to pull content.
```

**--deps (if flag present):**
For each loaded node, read its `depends_on: [[...]]` frontmatter links.
Resolve each link to a file path in `<projectDir>/` and Read it.
Append resolved nodes as a "Dependencies" subsection.

**--full:**
Read entire file content (not just frontmatter + Compressed: section).

**Default (no --full):**
Read YAML frontmatter + `Compressed:` section + link arrays.

For ADR nodes, also surface: `decision`, `rejected_alternatives`, `consequences` fields in compressed form.

### Step 5 — Format output (caveman-compressed)

Apply caveman rules: drop articles/filler, use fragments, keep technical data exact. Omit empty fields.

**ADR node (single):**
```
<id> [decision·<status>] #tag1 #tag2
<one-liner from Compressed:>
decided: <decision field>
rejected: <rejected_alternatives field, compressed>
consequences: <consequences field, compressed>
[Full prose if --full]
```

**Cluster:**
```
recall:<query> <N>nodes

1 decision:<id> #tags
  <one-liner>
  decided: <...>
  rejected: <...>

2 discovery:<id> #tags
  <one-liner>
...
→ <id> --full | <query> --deps | <query> --trace
```

**--trace:**
```
tree:<query>

<type>:<id>
├─related:[[A]][[B]]
└─related:[[C]]

~<N×20>t compressed. Obsidian graph for visual.
```

### Step 6 — Footer

```
recall done · <N>nodes · ~<estimated>t · mode:<compressed|full|trace>
→ /realm-recall <id> --full | --deps | /realm-fathom <entity> for live+vault
```
