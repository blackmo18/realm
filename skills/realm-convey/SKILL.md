---
name: realm-convey
description: >
  Conversation-to-vault ADR bridge. Extracts decisions, rejected alternatives, and discoveries
  from the current conversation, runs a structured interview per decision, then writes a
  manifest draft directly — no codebase scan. One command to capture session knowledge as
  ADR and discovery nodes.
origin: realm
---

# realm-convey

Extract decisions from conversation → structured ADR interview → manifest-draft → vault.

## When to Use

| Trigger | Example |
|---|---|
| Made an architectural decision | "convey this", `/realm-convey` |
| Discussed tradeoffs and chose a direction | "push this decision to realm" |
| End of session with non-obvious choices | "log this session" |
| Finished a `/realm-plan` that produced decisions | "convey the decisions from this plan" |

## When NOT to Use

- No realm state → `/realm-forge` first (hard guard)
- Nothing decided — just wrote code with no tradeoffs → skip
- Want to understand code + prior decisions before touching something → `/realm-fathom`
- Want to query existing decisions → `/realm-recall`

---

## Procedure

Steps 0–2.5 run inline (require main conversation context and user interaction).
Step 3 is an interactive interview — no agents spawned.
Step 4 writes manifest-draft directly. No codebase scan.

### Step 0 — Guard check

1. Read `.realm/realm-state.json`. If missing: `No realm state. Run /realm-forge first.` STOP.
2. Load: `vaultPath`, `projectSlug`, `projectDir`.

### Step 1 — Caveman-compress conversation

Scan current conversation context (all turns). Apply caveman compression:
- Drop: restated code already in source, pleasantries, filler
- Keep: decisions made, options considered, reasons given, constraints stated, unexpected findings, things explicitly rejected

Output: compressed flat list of meaningful items discussed.

### Step 2 — Dissect into topics

Classify each item:

| Type | Signal | Action |
|------|--------|--------|
| `decision` | "decided to", "chose X over Y", "because", "instead of", "DO NOT", "rejected", "went with" | ADR candidate → structured interview (Step 3) |
| `discovery` | perf finding, unexpected behavior, bug post-mortem, tech constraint, "turns out" | discovery node stub |
| `session` | general session summary, what was worked on | session log entry |

**Functions and classes are not captured here.** Code entities are derivable from source — only capture what code cannot express: decisions, rationale, rejected alternatives, constraints.

### Step 2.5 — User selection (BLOCKING)

Present pick-list. **Do not proceed until user replies.**

```
realm-convey: select items to capture

  Decisions
    [1] <decision title> — <one-liner>
    [2] <decision title> — <one-liner>

  Discoveries
    [3] <discovery title> — <one-liner>

  Session log
    [4] this session — <summary one-liner>

Enter numbers (e.g. 1 3), "all", or "none" to cancel:
```

Rules:
- Wait for explicit reply before any draft action
- `all` → select every item
- `none` / empty → `Nothing selected. Vault unchanged.` STOP
- Invalid numbers → re-prompt once, then STOP

### Step 3 — Structured ADR interview (decisions only)

For each selected decision, present this block and wait for user reply before moving to the next:

```
Decision [N/total]: <title>

Answer each — skip any you don't know yet (just press enter):

1. What exactly was decided?
2. What alternatives were considered, and why was each rejected?
3. What constraints or consequences does this impose on future work?
4. What triggered this? (PR, bug, requirement, conversation, spike)
```

Use answers to populate ADR node fields. Skipped fields become `—` placeholders.
After all decisions are interviewed, proceed to Step 4.

### Step 4 — Write manifest-draft

Read `_shared/realm-conventions.md` with `offset=0 limit=50` (frontmatter schema only).

Write `<projectRoot>/.realm/manifest-draft.md` containing:
- One full ADR node per selected decision (interview answers in body)
- One discovery stub per selected discovery
- One session log stub if selected

ADR node body structure:
```markdown
## Context
<what triggered this — from interview answer 4>

## Decision
<what was decided — from interview answer 1>

## Rejected alternatives
<each alternative + reason rejected — from interview answer 2>

## Consequences
<constraints imposed, known tradeoffs — from interview answer 3>
```

Push to `realm-state.json` `pendingDrafts`:
```json
{
  "source": "convey",
  "slug": null,
  "path": ".realm/manifest-draft.md",
  "created": "<ISO 8601>"
}
```

### Step 5 — Print summary

```
realm-convey complete

  decisions captured:  <N>  (ADR nodes staged in manifest-draft.md)
  discoveries:         <N>
  session log:         <yes|no>

  draft: .realm/manifest-draft.md
  next:  /realm-manifest to write to vault
```
