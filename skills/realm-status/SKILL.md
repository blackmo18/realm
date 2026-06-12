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

Handle all steps inline using Read and Bash. No agent spawn.

### Step 1 — Read state

Read `<projectRoot>/.realm/realm-state.json`.
If missing:
```
No realm state found.
Run /realm-forge to bootstrap.
```
STOP.

Extract: `vaultPath`, `projectSlug`, `projectDir`, `phase`, `manifest`, `docs`.

### Step 2 — Count nodes by type

Run:
```bash
find <projectDir> -name "*.md" | grep -v "_templates" | sort
```

Group results by subdirectory: `decisions/`, `functions/`, `classes/`, `systems/`, `discoveries/`, `sessions/`.

For tag frequency, run:
```bash
grep -rh "^  - " <projectDir> --include="*.md" | sort | uniq -c | sort -rn | head 20
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

PIPELINE init✓  phase:<lastRun ts or never>  draft:<yes/no>  manifest:<lastRun ts or never>

NODES <total>
decisions/<N>:   [[id]] <date>  [[id2]] <date>
functions/<N>:   [[id]]→<Class>  [[id2]]→<Class>
classes/<N>:     [[id]] deps:<N>  [[id2]] deps:<N>
discoveries/<N>: [[id]] <date>
sessions/<N>:    <filename>
planned/<N>:     <path>
stale/<N>:       <path>

TAGS #<tag>:<N>  #<tag>:<N>  #<tag>:<N>  (top 10)

→ <single most relevant next step>
```

Next step logic (pick one):
- `phase.draftReady == true` → `→ /realm-manifest  (draft ready)`
- `phase.draftReady == false`, stale docs exist → `→ /realm-phase  (<N> stale docs)`
- `manifest.lastRun == null` → `→ /realm-phase  (never run)`
- otherwise → `→ pipeline current. /realm-phase after next milestone.`
