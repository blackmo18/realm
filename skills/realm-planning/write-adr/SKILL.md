---
name: realm-planning:write-adr
description: >
  Commit an approved Phase 1 decision (and Phase 2 execution plan, if run) to
  the vault as an ADR + planning file, update the ADR index. Triggered by
  "write adr" / "write the adr" / "commit adr" after Phase 1 approval or
  Phase 2 completion.
---

# realm-planning — write adr

Trigger: user says `write adr`, `write the adr`, or `commit adr` — after Phase 1 approval or Phase 2 completion.

**All writes are direct to vault using the Write tool. No manifest pipeline. No manifest_write.py. No agent spawn.**

Plan-mode write boundary: `../references/plan-mode-contract.md` — if plan mode still active when triggered, `ExitPlanMode` first with pending writes as the plan.

## Step 1 — Load state

Read `.realm/realm-state.json`. If missing: `No realm state. Run /realm-forge first.` STOP.
Extract: `projectDir`.

## Step 2 — Get next ADR number

Reservation logic (reuse Phase 2's number if it already ran, else index+1): `../references/vault-conventions.md`.

## Step 3 — Extract decision from Phase 1

| Phase 1 section | ADR field |
|---|---|
| `## Context` | `### Context` |
| `## High-Level Direction` | `### Decision` |
| `## Rejected Alternatives` table | `### Rejected Alternatives` |
| `## Cons` + `## Open Questions` | `### Consequences` |
| `## Description` one-liner | `## Compressed` (caveman-compress it) |

Derive kebab slug from topic (e.g. `"auth JWT refactor"` → `auth-jwt-refactor`).
Derive tags from domain words in topic (e.g. `[decision, auth, jwt]`).

**Quality check before writing:** all 4 subsections must have content. Missing any → surface gap, ask user to fill. Do NOT write partial ADR.

## Step 4 — Write planning file to vault

Naming + frontmatter template (planning): `../references/vault-conventions.md`.

Write Phase 1 output to `<projectDir>/planning/<NNN>-plan-<slug>.md` (create `planning/` if missing). Body = full Phase 1 output verbatim, no compression, including `## Contract Delta` if present.

## Step 5 — Write ADR to vault

Check whether `<projectDir>/execution/<NNN>-exct-<slug>.md` exists (Phase 2 was run) — controls the `links:` omit rule (`../references/vault-conventions.md`).

Write `<projectDir>/decisions/ADR-<NNN>-<slug>.md` — frontmatter template + `links:` omit rules: `../references/vault-conventions.md`.

Body:

```markdown
## Compressed
<one tight caveman sentence — causal chain, ≤2 sentences>

## Full Decision

### Context
<Phase 1 ## Context — caveman compressed>

### Decision
<Phase 1 ## High-Level Direction — caveman compressed>

### Rejected Alternatives
<Phase 1 ## Rejected Alternatives — list format, caveman compressed>

### Consequences
<Phase 1 ## Cons + ## Open Questions — caveman compressed>

## Source Plan
[[planning/<NNN>-plan-<slug>]]
[[execution/<NNN>-exct-<slug>]]   ← omit if Phase 2 not run
```

Apply caveman compression to all prose in ADR body. Never compress YAML frontmatter, code blocks, URLs, or wikilinks.

## Step 6 — Update ADR index

Read `<projectDir>/decisions/ADR-000-index.md`. Append row to decisions table:

```
| [[ADR-<NNN>-<slug>]] | <topic> | active | <YYYY-MM-DD> |
```

Write updated file back.

## Step 7 — Summary

```
write adr complete

  adr:       decisions/ADR-<NNN>-<slug>.md
  planning:  planning/<NNN>-plan-<slug>.md
  execution: execution/<NNN>-exct-<slug>.md   ← only if Phase 2 was run
  index:     ADR-000-index.md updated
  tags:      [decision, <topic-tags>]

  recall: /realm-recall "why <topic>" | /realm-recall decisions
```
