---
name: realm-convey
description: >
  Conversation-to-realm bridge. Caveman-compresses the current conversation context, dissects it into typed topics (entities, decisions, discoveries), then routes code entities to realm-phase targeted mode. Lets you push conversation knowledge into the vault without manually identifying what changed.
origin: realm
---

# realm-convey

Compress conversation → dissect topics → feed realm-phase. One command to capture session knowledge.

## When to Use

| Trigger | Example |
|---|---|
| End of coding session | "convey this", `/realm-convey` |
| Discussed new decision/entity | "push this to realm" |
| Want to capture conversation findings | "log this session" |

## When NOT to Use

- No realm state → `/realm-forge` first (hard guard)
- Nothing technical discussed → skip
- Already used `/realm-flourish` → vault current

---

## Procedure

Read `_shared/realm-conventions.md` before executing.

Steps 0–2.5 run inline (require main conversation context and user interaction). Step 3 delegates to `realm-agent-scan`. Steps 4–5 run inline.

### Step 0 — Guard check

1. Read `.realm/realm-state.json`. If missing: `No realm state. Run /realm-forge first.` STOP.
2. Load: `vaultPath`, `projectSlug`, `projectDir`.

### Step 1 — Caveman-compress conversation

Scan current conversation context (all turns). Apply caveman compression policy from `_shared/realm-conventions.md`:
- Drop filler, articles, pleasantries
- Keep: function/class names, file paths, decisions, error messages, architectural rationale
- Preserve wikilink candidates: any named service, class, function mentioned ≥ 2x

Output: compressed flat list of all meaningful items discussed.

### Step 2 — Dissect into topics

Classify each item:

| Type | Signal | Realm destination |
|------|--------|-------------------|
| `function` | "wrote X()", "fixed X()", "X does Y" | `realm-agent-scan targeted function:X` |
| `class` | "class X", "service X", "module X" | `realm-agent-scan targeted class:X` |
| `decision` | "decided to", "because", "instead of", "DO NOT" | new ADR candidate |
| `discovery` | perf finding, bug post-mortem, unexpected behavior | `discoveries/` |
| `session` | everything else | session log entry |

### Step 2.5 — User selection (BLOCKING)

Present numbered pick-list. **Do not proceed until user replies.**

```
realm-convey: select items to process

  Functions
    [1] <functionName> — <one-liner>
    [2] <functionName> — <one-liner>

  Classes
    [3] <ClassName> — <one-liner>

  Decisions
    [4] <decision title> — <one-liner>

  Discoveries
    [5] <discovery title> — <one-liner>

Enter numbers (e.g. 1 3 5), "all", or "none" to cancel:
```

Rules:
- Wait for explicit reply before any vault or draft action
- `all` → select every item
- `none` / empty → `Nothing selected. Vault unchanged.` STOP
- Invalid numbers → re-prompt once, then STOP if still invalid
- Selected set is the only input for Steps 3–4; discard unselected

### Step 3 — Spawn scan agent for entities

If selected items include functions or classes:

Spawn agent `realm-agent-scan` with this prompt:

```
projectRoot: <absolute path to project root>
mode: targeted
targets: <list of function:X and class:X specifiers from selected items>

Scan the codebase for these entities and generate a staged manifest draft.
Follow the full procedure in your instructions.
```

Wait for completion.

If zero entities but decisions/discoveries present: skip to Step 4.
If nothing selected: `Nothing to convey. Vault unchanged.` STOP.

### Step 4 — Append decision/discovery candidates to draft

If Step 3 produced a draft (`<projectRoot>/.realm/manifest-draft.md`):
- Append ADR candidate stubs for each selected decision item
- Append discovery note stubs for each selected discovery item

If Step 3 was skipped (no entities), write `<projectRoot>/.realm/manifest-draft.md` with only the stubs.

Update `realm-state.json`: `phase.draftReady = true`.

### Step 5 — Print summary

```
realm-convey complete

  topics extracted:   <N>
  realm-agent-scan:   targeted (<entity list> | skipped)
  ADR candidates:     <N>  (staged in manifest-draft.md)
  discoveries:        <N>  (staged)

  draft: .realm/manifest-draft.md
  next:  /realm-manifest to write to vault
```
