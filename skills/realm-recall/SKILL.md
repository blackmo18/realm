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

Handle steps 1–5 inline using Read/Glob/Bash. Spawn `realm-agent-query` only as fallback for semantic/NL queries (Step 3d). Never spawn agent for known-node, tag, or filename lookups.

### Step 1 — Parse query and flags

From invocation args:
- `query`: everything before first `--` flag
- `flags`: collect any of `--trace`, `--full`, `--deps`, `--count`, `--expand <id>`

### Step 2 — Read state

Read `<projectRoot>/.realm/realm-state.json`.
If missing: `No realm state. Run /realm-forge first.` STOP.
Extract: `vaultPath`, `projectSlug`, `projectDir`.

Scan `<projectDir>/` for `.md` files across `decisions/`, `functions/`, `classes/`, `systems/`, `discoveries/`.
If none: `No nodes in vault yet. Run /realm-phase then /realm-manifest.` STOP.

### Step 3 — Resolution ladder (first match wins)

Work 3a → 3b → 3c → 3d in order. Stop at first hit.

**3a — Exact node ID match**

Applies when: query has no spaces, no `@`/`#` prefix, no natural-language words (why/how/what/does/is).

```bash
grep -rl "^id: <query>" <projectDir>/
```

If 1+ files found → Read them directly → go to Step 4. No agent spawn.

**3b — Tag cluster**

Applies when: query starts with `@` or `#`, or is a single lowercase word matching a likely tag (e.g. `auth`, `perf`, `security`).

Strip `@`/`#` prefix. Run:

```bash
grep -rl "  - <tag>" <projectDir>/
```

Read all matched files in parallel → go to Step 4. No agent spawn.

**3c — Filename fuzzy match**

Applies when: 3a/3b produced no results, query is 1–2 words.

Glob: `<projectDir>/**/*<query>*.md` (case-insensitive where supported).
If ≤20 matches → Read matched files → go to Step 4. No agent spawn.
If >20 matches → treat as 3d.

**3d — Semantic / NL fallback (agent justified)**

Applies when: query is multi-word phrase, starts with why/how/what, is quoted, or 3a–3c all returned no results.

Spawn `realm-agent-query` with:

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

  Matched nodes: <N>  (decisions: X, functions: Y, classes: Z)
  Deps (--deps): resolve depends_on links for +<est> additional nodes

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
Read YAML frontmatter + `Compressed:` section + link arrays (`depends_on`, `called_by`, `implementations`, `dependents`).

### Step 5 — Format output (caveman-compressed)

Apply caveman rules: drop articles/filler, use fragments, keep technical data exact. Omit empty fields.

**Single node:**
```
<id> [<type>·<status>] #tag1 #tag2
<one-liner from Compressed:>
sig: <signature if function>
deps:[[A]][[B]]  calls:[[C]][[D]]
[Full prose if --full]
```

**Cluster:**
```
recall:<query> <N>nodes

1 <type>:<id> #tags
  <one-liner>
  deps:[[A]]  calls:[[B]]

2 <type>:<id> #tags
  <one-liner>
...
→ <id> --full | <query> --deps | <query> --trace
```

**--trace:**
```
tree:<query>

<type>:<id>
├─impl: <type>:<id>
│  ├─deps:[[A]][[B]]
│  └─calls:[[C]][[D]]
└─impl: <type>:<id>
   └─deps:[[E]]

~<N×20>t compressed. Obsidian graph for visual.
```

### Step 6 — Footer

```
recall done · <N>nodes · ~<estimated>t · mode:<compressed|full|trace>
→ most relevant next: /realm-recall <id> --full | --deps | --trace
```
