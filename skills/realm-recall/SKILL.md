---
name: realm-recall
description: >
  Natural-language knowledge retrieval from the Obsidian vault. Primary interface for querying
  decisions, rejected alternatives, constraints, and discoveries. Maps a topic, decision keyword,
  or freeform phrase ("why JWT", "what was rejected for auth", "constraint on payments") to vault
  ADR and discovery nodes. When an ADR has source_plan (promoted from realm-plan), intent-maps
  the query to exactly one canvas section (plan/design/research/scaffold) and lazy-loads only
  that file — no full canvas pull. Supports --trace (link structure only), --full (expand prose),
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
/realm-recall <topic> --no-canvas   # Skip canvas expansion even if source_plan present
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

## Canvas Lazy-Load (source_plan)

When an ADR was promoted from a `realm-plan` canvas, its `source_plan` field points to the
canvas dir. realm-recall intent-maps the query to exactly one canvas section and reads only
that file. Cost: ADR compressed (~20t) + one section (~80–150t).

| Query words | Section loaded | Extra tokens |
|---|---|---|
| plan / steps / tasks / phases / build / implement | `plan.md` | ~100t |
| design / architecture / how / approach / structure | `design.md` | ~100t |
| research / why / evidence / tradeoffs / source / learned | `research.md` | ~120t |
| scaffold / blueprint / interface / methods / class / file | `scaffold.md` | ~100t |
| summary / what is / overview / which / what | `_meta.md` section headers only | ~15t |
| rejected / alternatives / why decided / constraint / chose | ADR body (already loaded) | 0t |

```bash
/realm-recall "what is the plan for auth refactor"
→ ADR-auth-refactor (compressed) + work/plans/auth-refactor/plan.md

/realm-recall "what design did we choose for auth"
→ ADR-auth-refactor (compressed) + work/plans/auth-refactor/design.md

/realm-recall "which research drove the auth decision"
→ ADR-auth-refactor (compressed) + work/plans/auth-refactor/research.md

/realm-recall "why did we reject X for auth"
→ ADR-auth-refactor body only — rejected_alternatives already there, 0 extra read

/realm-recall "summarize the auth refactor work"
→ ADR-auth-refactor (compressed) + _meta.md headers only

/realm-recall "auth" --no-canvas
→ ADR only, no canvas expansion (suppress source_plan follow)
```

No canvas follow when: ADR has no `source_plan`,
`--no-canvas` flag passed, `--trace` flag passed, or intent maps to ADR body (rejected/constraints).

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
- No nodes in vault yet → run `/realm-planning` or `/realm-forge` to populate
- Want live code + vault combined → `/realm-fathom`
- Want to plan architectural changes → `/realm-planning`
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
If none: `No nodes in vault yet. Run /realm-forge to bootstrap, or /realm-planning to create plans.` STOP.

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

### Step 4.5 — Canvas expansion (source_plan lazy-load)

Skip entirely if: `--trace` flag, `--no-canvas` flag, or no ADR nodes loaded.

For each ADR node loaded that has a `source_plan` field in frontmatter:

**4.5a — Classify query intent:**

Tokenize query (lowercase, split on spaces). Match first winning rule:

| Rule | Trigger words | Target file |
|---|---|---|
| `plan` | plan, steps, tasks, phases, build, implement, roadmap, milestones | `plan.md` |
| `design` | design, architecture, how, approach, structure, pattern, system | `design.md` |
| `research` | research, why, evidence, tradeoffs, tradeoff, source, learned, studied, found | `research.md` |
| `scaffold` | scaffold, blueprint, interface, methods, class, file, module, boundary | `scaffold.md` |
| `meta` | summary, summarize, overview, which, what, list | `_meta.md` |
| `adr-only` | rejected, alternatives, chose, chose, constraint, consequence, decided | — (no read) |

If no rule matches: default to `meta` (read `_meta.md` headers only).

**4.5b — Resolve canvas path:**

```
canvas_dir = <projectDir>/<source_plan>
section_path = <canvas_dir>/<target_file>
```

If `section_path` does not exist: skip canvas expansion for this node, note in output:
`canvas section not found: <section_path>`

**4.5c — Read section:**

For `_meta.md` target: read headers only (lines starting with `#` or `|`). ~15 tokens.
For all other targets: read full file content. ~80–150 tokens.

Attach section content to the node's output under `## Canvas: <section>`.

**4.5d — Token note:**

Append to Step 6 footer:
`canvas: +<N>t (<section> from <source_plan>)`

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

## Canvas: <section>          ← only if source_plan present and intent matched
<section file content, caveman-compressed>
origin: <source_plan>
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
[canvas: +<Nt> (<section> from <source_plan>)]   ← only if canvas expanded
→ /realm-recall <id> --full | --deps | --no-canvas | /realm-fathom <entity> for live+vault
```
