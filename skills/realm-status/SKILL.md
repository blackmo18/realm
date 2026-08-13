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
| Verify vault health | "what does realm know" |
| Orient at session start | "what does realm know?" |

## When NOT to Use

- Want to investigate code + vault → `/realm-fathom`
- Want to plan architectural changes → `/realm-planning`
- `realm-state.json` missing → will report; run `/realm-forge`

---

## Procedure

Handle all steps inline using Read and Bash. No agent spawn.

### Step 1 — Read state

Read `<projectRoot>/.realm/realm-state.json`.
If missing:
```
No realm state found.
Run /realm-forge to bootstrap.
```
STOP.

Extract: `vaultPath`, `projectSlug`, `projectDir`, `docs`.

### Step 2 — Count nodes by type

If `nodeIndex` present in state: read counts from `state.nodeIndex.counts` (no bash needed).
Fallback (no nodeIndex): `find <projectDir> -name "*.md" | grep -v "_templates" | sort`

Derive node list from `docs` registry (loaded in Step 1):
- Group `docs` keys by leading path segment (`decisions/foo.md` → `decisions/`)
- Strip `.md` suffix for `[[id]]` display
- Use `docs[path].updated` for date display

Tag frequency (run once):
```bash
grep -rh "^  - " <projectDir> --include="*.md" 2>/dev/null | sort | uniq -c | sort -rn | head 20
```

### Step 3 — Identify planned and stale docs

From `docs` registry in realm-state.json:
- `status: "planned"` → planned list
- `status: "stale"` → stale list
- `status: "committed"` → committed count

### Step 4 — Print status (caveman-compressed)

```
realm:<projectSlug>
vault:<vaultPath>  proj:<projectDir>

NODES <total>
decisions/<N>:   [[id]] <date>  [[id2]] <date>
discoveries/<N>: [[id]] <date>
sessions/<N>:    <filename>
planned/<N>:     <path>
stale/<N>:       <path>

TAGS #<tag>:<N>  #<tag>:<N>  #<tag>:<N>  (top 10)

→ pipeline current. Run /realm-fathom to investigate code or /realm-planning to design.
```
