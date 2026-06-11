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

### Step 1 — Read state

Read `.realm/realm-state.json` from project root. If missing:
```
No realm state found for this project.
Run /realm-forge to bootstrap.
```
STOP.

### Step 2 — Print status (caveman-compressed)

Apply caveman rules: drop articles/filler, use fragments, keep technical data exact. Omit zero-count categories silently.

```
realm:<projectSlug>
vault:<vaultPath>  proj:<projectDir>

PIPELINE init✓  phase:<ts|never> draft:<yes/no>  manifest:<ts|never>

NODES <total>
decisions/<N>: [[id]]<date> [[id2]]<date>
functions/<N>: [[id]]→<Class> [[id2]]→<Class>
classes/<N>:   [[id]]deps:<N> [[id2]]deps:<N>
discoveries/<N>: [[id]]<date>
planned/<N>: <path>
stale/<N>: <path>

TAGS #auth:<N> #critical-path:<N> #perf:<N> #<tag>:<N>

→ <single most relevant next step based on state>
```

`NEXT STEP` logic (pick one line):
- `phase.draftReady == true` and manifest not run since phase → `→ /realm-manifest  (draft ready)`
- `phase.draftReady == false`, no stale docs → `→ pipeline current. /realm-phase after next milestone.`
- Any docs `stale` → `→ /realm-phase  (<N> stale docs)`
- `manifest.lastRun == null` → `→ /realm-phase  (never run)`
