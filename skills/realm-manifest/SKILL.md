---
name: realm-manifest
description: >
  Vault-write step in the realm pipeline. Reads the staged manifest-draft.md from .realm/, caveman-compresses doc bodies, writes new and updated docs to the Obsidian vault, updates cross-links (ADR index, overview wikilinks), creates a session log entry, marks all planned docs as committed, and archives the draft. The ONLY realm skill that writes to the vault. Must run after realm-phase.
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

Read `_shared/realm-conventions.md` for schema, taxonomy, compression policy, ADR index rules before executing.

**This skill IS allowed to write to `<vaultPath>/`. All previous realm skills are not.**

### Step 0 — Guard checks

1. Read `.realm/realm-state.json`. If missing: print `No realm state. Run /realm-forge then /realm-phase.` and STOP.
2. Check `phase.draftReady == true`. If false: print `No staged draft. Run /realm-phase first.` and STOP.
3. Check `.realm/manifest-draft.md` exists. If missing: print `Draft file missing. Run /realm-phase to regenerate.` and STOP.
4. Load: `vaultPath`, `projectSlug`, `projectDir`, `docs` registry.

### Step 1 — Parse manifest-draft.md

Read `.realm/manifest-draft.md` in full. Parse sections:
- `## Meta` block → extract `slug`, `phase-run`, `gap-summary`
- Each `### <relative path>` block → extract `status` (new|update), `links`, body after `---`
- `## Session Log Entry` → `### sessions/<path>` → body after `---`

Build ordered list of write operations: `[{ path, status, links, body }, ...]`

### Step 2 — Validate and prepare node files

For each planned doc:
1. Verify YAML frontmatter: `id`, `type` (decision|function|class|discovery), `status`, `tags`, `created`, `updated`.
2. Verify structure: `Compressed:` section + `Full` section (or combined prose).
3. Function/class nodes: verify `[[depends_on]]` and `[[called_by]]`/`[[dependents]]` links present.
4. Decision nodes: verify `## Full Decision` has Context/Decision/Consequences.
5. Apply caveman compression (from `_shared/realm-conventions.md`):
   - Do NOT compress: YAML, code blocks, URLs, tables, wikilinks `[[...]]`, tag values
   - Compress: prose bullets, section summaries, filler
   - Decision: preserve causal chain in Context/Decision; compress filler only
6. All `[[wikilinks]]` must use node IDs (not filenames).

### Step 3 — Write node documents to vault

For each write operation:
1. Resolve full path: `<projectDir>/<relative-path>` (create intermediate dirs if needed).
2. `status: new`: write file with full YAML + Compressed + Full sections. If exists, print warning and skip (no clobber).
3. `status: update`: read existing, merge:
   - decisions/functions/classes: append new sections; preserve existing subsections
   - overview.md: only update milestone checkboxes and tech stack; preserve all other prose
   - architecture.md: append new service/event rows; do NOT remove existing rows
4. Per node written: extract `id` and `type` from frontmatter; add to in-memory graph index for backlinks (Step 4).
5. Print each write: `  WROTE   <relative path>  (id: <nodeId>)` or `  MERGED  <relative path>` or `  SKIP    <relative path> (exists)`

### Step 4 — Update node indexes and backlinks

If decision nodes written:
1. Read or create `<projectDir>/decisions/_index.md`.
2. For each new/updated decision, ensure table row: `| [[<id>]] | <Title> | <status> | <updated date> |`
3. Sort rows by date or ID ascending.
4. Write updated index.

For new function/class nodes:
1. New function `<functionName>` with `class: <ClassName>` → if class node exists, append `- [[<functionName>]]` to its `## Methods` or `## Related Functions`.
2. New class `<ClassName>` with `depends_on: [[ClassA]]` → for each dep, append `- [[<ClassName>]]` to their `## Dependents`.
3. Nodes with `[[called_by]]` → ensure caller node (if exists) has entry in `## Dependents` or `## Called By`.
4. Write updated node files if backlinks changed.

### Step 5 — Write session log entry

Write session log from `## Session Log Entry`:
- Full path: `<projectDir>/sessions/<YYYY-MM-DD>-<topic>.md`
- Exists with today's date: append `---` separator + new content.
- Ensure frontmatter: `tags: [session]`, `date:`, `project:`.

### Step 6 — Update realm-state.json

Mutate and write:
- Each successfully written doc: `docs["<path>"].status = "committed"`, `updated = <now ISO>`
- Skipped docs (already existed): leave `committed` unchanged
- `manifest.lastRun`: current ISO timestamp
- `phase.draftReady`: reset to `false`

### Step 7 — Archive the draft

```
mkdir -p <projectRoot>/.realm/archive/
mv .realm/manifest-draft.md .realm/archive/<YYYYMMDD-HHmmss>-draft.md
```

### Step 8 — Print summary

```
realm-manifest complete
  vault:     <projectDir>

  nodes written:
    decisions:    <N> new
    functions:    <N> new
    classes:      <N> new
    discoveries:  <N> new
    updates:      <N> (overview/architecture merged)
    skipped:      <N> (already existed, unchanged)

  backlinks updated: <N> nodes
  decision index:    <N> entries
  session log:       sessions/<YYYY-MM-DD>-<topic>.md
  draft archived:    .realm/archive/<timestamp>-draft.md

Open Obsidian to explore:
  → Graph view: see dependencies and connections
  → Tag filter: #auth, #critical-path, #performance, etc.
  → Backlinks: see what calls/depends on each node

Next: /realm-status to verify  |  /realm-recall <topic> for context  |  /realm-phase after next milestone
```
