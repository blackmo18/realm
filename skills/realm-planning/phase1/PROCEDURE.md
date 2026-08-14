---
name: realm-planning-phase1
description: >
  Phase 1 of realm-planning. High-level plan + ADR direction for a topic.
  Enters native plan mode, detects run mode (enhancement / anchored-new /
  greenfield), resolves typed anchors, runs scoped investigation and architect
  analysis, and produces a plan approved via ExitPlanMode.
---

# realm-planning — Phase 1: High-Level Plan

## Step 0 — Enter Plan Mode

Full boundary + fallback: `../references/plan-mode-contract.md`. Call `EnterPlanMode` before any context gathering.

## Step 1 — Graph Precondition (main thread, one Bash call)

Command reference, cost table, guardrails for every `graphify` call below: `../references/graphify-contract.md`.

`test -f graphify-out/graph.json`:
- **Present** → graphify path active for Step 2 / Step 3. Then `graphify check-update .` — pending re-extraction → **Graph: stale** (graphify output becomes hints, investigator trigger threshold drops); otherwise **Graph: fresh**.
- **Absent** → **Graph: absent**. Legacy path: Step 2 keeps `grep -ril`, Step 3 keeps full investigator budgets. Skip all graphify sub-steps below. Skill must work in a repo with no graph.

Record `Graph: fresh | stale | absent` — carried into the Step 7 plan header.

## Step 2 — Mode Detection (main thread, zero agents, zero file Reads)

Resolve topic against cheap indexes:
1. CLAUDE.md key-files map
2. Repository-specific reuse guidance from `AGENTS.md`, `CLAUDE.md`, or host rules
3. Vault node paths (`classes/`, `functions/`, execution nodes)
4. Graph present → `graphify query "<topic>" --budget 500`. Graph absent → one `grep -ril "<topic keywords>" src/`.

Graph path reads the `Traversal:` header, not the NODE body:

| graphify evidence | Mode |
|----------|------|
| `Start:` seeds contain topic-specific labels, matching `src=` paths cluster in 1-2 communities | **enhancement** |
| `Start:` seeds hit only neighbor systems (auth, repo, route, API client), no topic-named node | **anchored-new** |
| No meaningful seed match after one vocab retry | **greenfield** |

**Drift guard:** seeding is label string match — a topic whose words aren't node labels drifts silently (top-ranked NODE lines can be wholly unrelated files). Seeds semantically unrelated to the topic = drift, NOT greenfield. Before concluding greenfield, retry once with graphify's installed vocab-expansion guidance when available (dump node-label vocab, pick ≤12 real vocab tokens, re-query with those). Only conclude greenfield after that retry still misses.

Legacy (grep) evidence table:

| Evidence | Mode |
|----------|------|
| Direct hits — feature exists in code | **enhancement** |
| No direct hits, neighbor systems hit (auth, checkout, repos, routes) | **anchored-new** |
| Nothing hits | **greenfield** |

Print detected mode + evidence before Step 3.

Misdetection mid-run (e.g. investigator finds feature exists during anchored-new run) → surface, switch mode, never continue silently.

## Step 3 — Context (per mode)

### Common — all modes, parallel

- `realm-recall "<topic>"` — ADRs, constraints, node file paths
- `realm-recall "ADR index"` — what decisions exist

Existing solution found → surface, ask: extend or plan fresh.

Conflict rule: code wins location/behavior, vault wins intent/constraint. Flag drift, never blend.

### enhancement — ADR first, typed anchors, tight scope

1. Vault first: ADR `source_plan` execution nodes list files touched last time = precomputed anchor set. Often ends anchor search.
2. Fill gaps via typed resolution — anchor-kind → command table: `../references/anchor-resolution.md`.
3. **Investigator is a fallback**, not a default spawn — trigger conditions + budgets: `../references/investigator-rules.md`.

### anchored-new — integration points + exemplar

Seeds = attach points (route dir, repository layer, API client) + one existing sibling feature as shape exemplar. Graph present: resolve attach points via `graphify explain`/`affected` same as enhancement (`../references/anchor-resolution.md`); the "nearest shape" sibling still benefits from a quick `graphify query "<sibling feature>" --budget 500` before falling back to investigator.

Investigator (fallback only, see `../references/investigator-rules.md`) answers two questions: "where does this attach" and "which existing feature is nearest shape".

### greenfield — research-heavy, code-light

No deep code search. Single shallow pass: top-level structure, key configs, conventions files. Graph present: one `graphify query "<topic>" --budget 500` first, in case the drift guard was wrong. Investigator fallback only (`../references/investigator-rules.md`). Weight shifts to Step 4 research.

## Step 4 — Research (greenfield or unknown patterns only)

Skip when topic already in codebase. Otherwise:
- `research-ops` — current-state evidence
- `deep-research` — deep synthesis when needed

## Step 5 — Architect Analysis

`architect` agent has no Bash — it cannot run graphify itself. Spawn `architect` with: topic + requirements, vault context, research findings, and the resolved discovery table (graphify anchor table + `affected` output when graph present, investigator `file:line` table when it ran as fallback or graph absent) fed in by the main thread.

Returns: approach, alternatives, constraints, risks.

## Step 6 — Decision Gate

2+ credible approaches, no clear winner → `council` skill.

## Step 7 — Plan Output

Use `../references/plan-template.md` (Phase 1 section — sections list lives there, not duplicated here). Handoff artifact: Mode + Anchor Set table is authoritative — Phase 2 trusts it verbatim, never re-derives.

### Contract Delta (conditional)

Anchor touched ≠ trigger — gate logic, affecting/not-affecting table, ambiguous default: `../references/contract-delta-gate.md`. Single source of truth for the whole contract pipeline (this embed, `write contract`, Phase 2's Contract Gate step) — decide once here, everything downstream trusts it without re-deriving.

## Step 8 — Approval Gate = ExitPlanMode

Present Phase 1 plan via `ExitPlanMode`. Approval exits plan mode = Phase 1 approved.

- Approved → Phase 2 runs (re-enters its own plan mode per `../references/plan-mode-contract.md`)
- Rejected → iterate, stay in plan mode

**No Phase 2 until approval.**
