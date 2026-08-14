---
name: realm-planning-lite
description: >
  Lite mode for realm-planning. Scope & Test Definition only — Affected Files,
  New Files, Test Scenarios — no architecture, no ADR, no full task plan, no
  execution file write. For token-budget-constrained direction when the user
  will hand-code the implementation themselves.
---

# realm-planning — Lite: Scope & Test Definition Only

Shortcut path. Skips Phase 1 architecture ceremony (research, `architect` agent, council) and Phase 2 heavier scaffolding (contract gate, rule selection, full task plan, execution-file write). Produces exactly one thing — the Scope Summary block: Affected Files, New Files, Test Scenarios — then stops.

## Step 0 — Enter Plan Mode

Same boundary as full pipeline: `../references/plan-mode-contract.md`. Enter native planning mode before any context gathering.

## Step 1 — Graph Precondition (main thread, one Bash call)

Identical to Phase 1 Step 1 (`../phase1/PROCEDURE.md`): `test -f graphify-out/graph.json` → **fresh** (graphify active) | **stale** (graphify hints only, lower investigator trigger threshold) | **absent** (legacy grep path). Command reference, cost table, guardrails: `../references/graphify-contract.md`.

## Step 2 — Cheap Anchor Resolution (main thread, no agent spawn)

No `architect`, no `code-architect`. Resolve affected files directly:

- Graph present: `graphify query "<topic>" --budget 500` → `graphify affected "<X>" --depth 1` / `graphify explain "<X>"` per anchor kind, table in `../references/anchor-resolution.md`.
- Graph absent: `grep -ril "<topic keywords>" src/`.
- Classify each hit: modify (existing) vs new (doesn't exist yet). Note any obvious conflict/edge case in one line — no deep investigation.
- `cavecrew-investigator` fallback only under existing trigger conditions, `../references/investigator-rules.md` — same budgets, no lite-specific carve-out.
- Drift guard applies same as Phase 1 Step 2: one vocab-expansion retry before concluding nothing matches.

No Contract Gate — Phase 2 Step 1's gate (checking a written contract file exists) does not apply here, lite writes no execution file. But lite is not exempt from *detecting* API-surface impact — that's Step 3 below.

## Step 3 — API-Surface Gate (stop-and-flag)

Run every anchor Step 2 found against `../references/contract-delta-gate.md`'s affecting/not-affecting table — same single source of truth Phase 1 Step 7 and Phase 2's Contract Gate already trust, no new criteria invented. Covers route, API (REST or otherwise), API request/response shape, GraphQL, and proto/RPC surfaces alike — protocol-agnostic, per that table.

Any anchor is **affecting** (new endpoint/rpc/route/field returning data; response or request field added/removed/renamed/retyped; error/status shape changed; endpoint/field removed or deprecated) →  **STOP. Do not proceed to Step 4.** Flag to the user:

> This change touches an API surface (route/REST/GraphQL/proto — [name the anchor]). Lite mode doesn't run the Contract Delta process needed for shape-affecting changes. Escalate to `/realm-planning <topic>` (full Phase 1) so this gets a proper Contract Delta.

All anchors **not affecting** (internal refactor, perf/logging-only, auth change not touching body/error shape, comment/formatting-only, test-only) — per the same table's right column, ambiguous defaults to not-affecting — → continue to Step 4 as normal.

## Step 4 — Scope & Test Definition

Populate `../references/plan-template.md`'s `### Scope Summary` block, verbatim format (same template Phase 2 Step 4 uses):

- **Affected Files** — every existing file Step 2 marked modify, one line each: path + what changes.
- **New Files** — every file Step 2 marked new, one line each: path + purpose.
- **Test Scenarios (must pass)** — checklist, condition → expected outcome. Derive from Step 2's noted conflicts/edge cases + the obvious happy path.

Empty Affected/New Files or zero Test Scenarios → say so, do not fabricate to look complete.

## Step 5 — Exit Plan Mode, Present, Stop

Present the Scope Summary through the native plan gate. Approval = done — **perform no write, regardless of approval.** Lite has nothing to persist (no ADR, no execution file, no contract).

Escalate if scope grows: "this needs the full pipeline" → `/realm-planning <topic>` (fresh Phase 1) or `/realm-planning <topic> --phase2` (if an approved Phase 1 plan already exists).

## When NOT to Use

- Task needs a design decision between multiple valid approaches → full `/realm-planning <topic>`.
- Task is architectural or spans a real decision about direction, not just "which files" → full pipeline.
- User wants the coding agent to receive a step-by-step task list → full pipeline (Phase 2 Step 5).
- Change touches a route/API/GraphQL/REST/proto surface in a shape-affecting way — lite stops and flags this automatically at Step 3, no need to pre-empt it, but don't expect lite to push through anyway.
