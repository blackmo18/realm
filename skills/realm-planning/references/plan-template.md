# Plan Template

Used by the `realm-planning` skill. Phase 1 produces the ADR section. Phase 2 appends the implementation section.

---

## Phase 1 Output — High-Level ADR

```markdown
# [TOPIC] Plan
**Date**: YYYY-MM-DD HH:MM

**Status**: Draft | Approved | Superseded

## Description
[One paragraph: what this plan covers and why it's needed]

## Context
[What triggered this — existing problem, new feature request, constraint]

## Mode & Anchor Set
**Mode**: enhancement | anchored-new | greenfield
**Graph**: fresh | stale | absent

| Kind | Path:Line | Why | 1-hop (relation → path) | Source |
|------|-----------|-----|--------------------------|--------|
| file | `src/path/to/file.ts:L1` | [why this anchors the change — e.g. feature home, integration point, exemplar] | `imports → src/other.ts` | graphify:explain |
| route | `src/app/.../page.tsx:L1` | [...] | [...] | convention |

`Source` ∈ `graphify:query` \| `graphify:explain` \| `graphify:affected` \| `graphify:path` \| `vault` \| `investigator` \| `convention`.

<!-- Handoff artifact: Phase 2 passes this table verbatim, including the 1-hop column, to realm-agent-code-architect — no re-derivation. -->
<!-- greenfield: no anchors — replace table with one-paragraph conventions summary (stack, structure, patterns found in shallow pass). -->

## High-Level Direction
[The chosen approach in plain language. Not steps — the strategic direction.]

## Architecture Diagram
[ASCII or Mermaid block]

## Pros
- [Benefit 1]
- [Benefit 2]

## Cons
- [Tradeoff 1]
- [Tradeoff 2]

## Rejected Alternatives

| Option | Reason Rejected |
|--------|----------------|
| [Alt A] | [Why not] |
| [Alt B] | [Why not] |

## Open Questions
- [ ] [Question that needs answering before or during implementation]

## Related ADRs
- [ADR-XXX title] — [how it relates]
```

---

## Phase 2 Append — Implementation Plan

```markdown
## Implementation Plan
**Validated by**: realm-agent-code-architect (against Phase 1 Anchor Set + 1-hop imports — no layer re-scan)
**Active Layers**: [frontend | backend | data | auth | payments | infra — rule selection only, not scope]
**ECC Rules Loaded**: [only rules selected in Phase 2 Step 2 — not the full ECC set]
**Skills Loaded**: [only skills selected in Phase 2 Step 2]

### Scope Summary
<!-- MANDATORY — always populated, regardless of tdd-workflow selection. Defined before Tasks below. -->

#### Affected Files (existing, modified)
- `src/path/to/file.ts` — [what changes]

#### New Files (created)
- `src/path/to/new-file.ts` — [purpose]

#### Test Scenarios (must pass)
- [ ] [Scenario] — [given/when/then or condition → expected outcome]

### Prerequisites
- [Existing service/module this builds on]
- [Migration or config change needed first]

### Tasks

#### Task 1 — [Name]
- **File**: `src/path/to/file.ts`
- **Target**: `functionName` / `ComponentName`
- **Action**: [create | modify | delete]
- **Notes**: [follow pattern X, use utility Y, respect constraint Z]
- **Logging**: [trace entry/exit; non-PII inputs: e.g. `orderId`, `policyId`; non-PII outputs: e.g. `status`, `routeCount`; branch points: e.g. `policy matched → route A`]
- **Test**: [what to assert — unit / integration / E2E]

#### Task 2 — [Name]
- **File**: `src/path/to/file.ts`
- **Target**: `functionName`
- **Action**: [create | modify]
- **Notes**: [...]
- **Logging**: [...]
- **Test**: [...]

<!-- repeat per task, ordered by execution dependency -->

### Testing & Validation

#### Unit Tests
- [ ] [Function] — [what behavior to cover]

#### Integration Tests
- [ ] [Route or operation] — [what to assert]

#### E2E (if applicable)
- [ ] [User flow] — [expected outcome]

#### Coverage Target
Minimum 80% on all new code. Run `pnpm test:coverage` to verify.

### Logging & Observability
Requirements: `logging-plan.md` (same file, same rules — each task's **Logging** field above is this table applied per-task).

### Coding Agent Notes
- Assume nothing about existing code — read target files before editing
- Follow existing patterns in the file rather than inventing new ones
- Implement logging per task **Logging** field before marking task done
- Run tests after each task before moving to the next
- Do not refactor unrelated code
```
