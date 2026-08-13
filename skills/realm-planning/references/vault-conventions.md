# Vault Conventions — Naming, Numbering, Frontmatter, Links

Single source of truth for every vault write in realm-planning (Phase 2 Step 6, `write contract`, `write adr`). Loaded whenever any of those writes a file.

## Naming

| Type | Filename |
|---|---|
| planning (Phase 1) | `<NNN>-plan-<slug>.md` |
| execution (Phase 2) | `<NNN>-exct-<slug>.md` |
| ADR | `ADR-<NNN>-<slug>.md` |
| contract | `<slug>-api-contracts.md` (no `<NNN>` — contracts aren't ADR-numbered) |

`<slug>` = kebab-case of topic, consistent across all four types for one decision.

## ADR Number Reservation

1. `<projectDir>/execution/<NNN>-exct-<slug>.md` already exists → reuse that `<NNN>` (Phase 2 already reserved it).
2. Else read `<projectDir>/decisions/ADR-000-index.md`, find highest `ADR-NNN`, next = N+1, zero-padded to 3 digits.
3. No numbered ADRs found → start at `001`.

Whichever of Phase 2 or `write adr` runs first reserves the number; the other reuses it.

## Frontmatter Templates

**planning** (`write adr` Step 4):
```markdown
---
id: <NNN>-plan-<slug>
title: "<topic>"
type: planning
created: <YYYY-MM-DD>
links:
  - "[[ADR-<NNN>-<slug>]]"
  - "[[<slug>-api-contracts]]"
---
```

**execution** (Phase 2 Step 6):
```markdown
---
id: <NNN>-exct-<slug>
title: "<topic>"
type: execution
created: <YYYY-MM-DD>
links:
  - "[[planning/<NNN>-plan-<slug>]]"
  - "[[<slug>-api-contracts]]"
---
```

**ADR** (`write adr` Step 5):
```markdown
---
id: ADR-<NNN>-<slug>
title: "<topic>"
type: decision
status: active
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
tags: [decision, <topic-tags>]
links:
  - "[[ADR-000-index]]"
  - "[[overview]]"
  - "[[planning/<NNN>-plan-<slug>]]"
  - "[[execution/<NNN>-exct-<slug>]]"
  - "[[<slug>-api-contracts]]"
---
```

## `links:` Omit Rules

Every `links:` entry above is conditional — never write a wikilink to a file that doesn't exist yet:

| Entry | Omit when |
|---|---|
| `- "[[<slug>-api-contracts]]"` | no `## Contract Delta` in Phase 1 plan, or `write contract` never run for this topic |
| `- "[[execution/<NNN>-exct-<slug>]]"` | Phase 2 was not run |
| `- "[[planning/<NNN>-plan-<slug>]]"` (in ADR) | never omit — `write adr` always writes the planning file first, in the same run |

Backlink direction: whichever file writes *later* adds the reverse link itself and checks for an existing entry first — never duplicate an edit in either direction.
