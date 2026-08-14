---
name: realm-planning
description: >
  Two-phase planning skill. Phase 1: high-level plan + ADR direction. Phase 2: code-level implementation plan for a coding agent.
---

# realm-planning

Two-phase planning. P1 = high-level + ADR direction. P2 = code-level impl plan.

Runs inside native plan mode — each phase has its own Enter/Exit cycle, approval is per-phase, not inherited. Boundary + fallback: `references/plan-mode-contract.md`.

Anchor-scoped: Phase 1 detects run mode (enhancement / anchored-new / greenfield), resolves seed anchors, caps investigator reads. Phase 2 consumes Phase 1 Anchor Set — no re-scan.

## Usage

```
/realm-planning <topic>          # Phase 1
/realm-planning <topic> --phase2 # skip to Phase 2 (plan already approved)
/realm-planning <topic> --lite   # Scope & Test shortcut only — Affected Files + Test Scenarios, no ADR, no full plan
```

## When to Use

- Feature not yet implemented
- Architectural direction unclear
- Spans multiple services/files
- Need plan ready for coding agent
- Token-budget constrained, want direction only, will hand-code the implementation yourself, don't need an architecture ADR — use `--lite`

## Communication Style

Caveman mode active. Drop articles, filler, pleasantries, hedging. Fragments OK. Technical terms exact.

## Routing

- Phase 1 → load `phase1/SKILL.md`
- Phase 2 → load `phase2/SKILL.md`
- Lite → load `lite/SKILL.md` (`--lite` flag: Scope & Test Definition only, skips architecture + full plan)
- Contract → load `contract/SKILL.md` (Phase 1 Step 7 `Contract Delta` embed, or explicit `write contract` trigger below)
- `write adr` → load `write-adr/SKILL.md` (trigger below)

---

## "write contract" — Draft API Contract to Vault

Trigger: user says `write contract` or `draft contract` — any time after Phase 1 approval, before Phase 2. Does not depend on `write adr` (that can come later) — but if `## Contract Delta` is present, Phase 2 depends on **this**: `phase2/SKILL.md` Step 1 refuses to start until the contract file exists. Ordering enforced: **Phase 1 → contract (if applicable) → Phase 2.**

Only fires when Phase 1 plan output includes a `## Contract Delta` section (see `phase1/SKILL.md` Step 7, gate logic in `references/contract-delta-gate.md`). No delta → nothing to write, say so, and Phase 2's gate is a no-op for this topic.

Full logic: `contract/SKILL.md`. Writes `<projectDir>/contracts/<slug>-api-contracts.md` using `references/contract-template.md`.

Plan-mode write boundary: `references/plan-mode-contract.md`.

---

## "write adr" — Commit Decision to Vault

Trigger: user says `write adr`, `write the adr`, or `commit adr` — after Phase 1 approval or Phase 2 completion.

Full logic: `write-adr/SKILL.md` — loads state, reserves ADR number, extracts decision from Phase 1, writes planning file + ADR + index update, all direct Write tool (no manifest pipeline, no agent spawn).

Plan-mode write boundary: `references/plan-mode-contract.md`.

---

## Graphify Contract

Phase 1 discovery defaults to the `graphify` CLI when `graphify-out/graph.json` exists — pure graph traversal, zero LLM tokens, far cheaper than an investigator spawn. Command reference, cost table, and guardrails: `references/graphify-contract.md` (loaded by `phase1/SKILL.md` where these commands actually run).

## Agents & Skills Used

| Component | Role |
|-----------|------|
| `architect` agent | High-level architecture analysis (Phase 1) |
| `code-architect` agent | Codebase-aware impl blueprint + logging plan (Phase 2) |
| `graphify` CLI | Primary code discovery — mode detect, anchor resolution, 1-hop (Phase 1) |
| `cavecrew-investigator` agent | Fallback code search when graphify misses or graph absent (Phase 1) |
| `realm-recall` skill | Pull vault ADRs and prior decisions |
| `research-ops` skill | Research new/unknown topics |
| `deep-research` skill | Deep synthesis on new/unknown topics |
| `council` skill | Structured tradeoff analysis when paths tie |
| `tdd-workflow` skill | Test plan generation |
| `contract/SKILL.md` fragment | Draft + write API contract file — Phase 1 Step 7 embed (`Contract Delta`), `write contract` trigger |
| `write-adr/SKILL.md` fragment | Commit decision to vault — ADR + planning file + index update, `write adr` trigger |

## Flow

```
/realm-planning <topic>
P1 (phase1/SKILL.md):
  ↓ Step 0 EnterPlanMode ──────────────────── read-only zone
  Step 1 Graph precondition (fresh | stale | absent)
  → Step 2 Mode detect (graphify query --budget 500, drift-guarded)
  → Step 3 Anchors (graphify explain/affected/path) → [investigator fallback if triggered]
  → Step 4 [Research] → Step 5 Architect → Step 6 [Council] → Step 7 Plan [+ Contract Delta if API-surface anchor changed — proto/REST/GraphQL]
  ↓ Step 8 ExitPlanMode = Phase 1 approval ─── writes allowed
Contract Delta present in plan?
  no  → straight to P2
  yes → "write contract" REQUIRED before P2
          → contract/SKILL.md → Write contracts/<slug>-api-contracts.md (direct)
             consumer can start now — does not wait on write adr or P2
        P2 Step 1 gate checks this file exists; missing → STOPS, tells user to write contract first
  ↓
P2 (phase2/SKILL.md):
  ↓ EnterPlanMode (Phase 2's own, separate from Phase 1's) ── read-only zone
  Step 1 Contract Gate (blocks if delta unresolved)
  → Step 2 Rules from layers → Step 3 Code-Architect (Anchor Set verbatim)
  → Step 4 Scope & Test Definition (MANDATORY, always) — Affected Files, New Files, Test Scenarios (must pass)
  → Step 5 Step-by-Step Plan (every task traces to Step 4 entries)
  ↓ ExitPlanMode = Phase 2 approval ─────────── writes allowed
  → Step 6 Write execution/<NNN>-exct-<slug>.md (links: planning + contract if applicable; Write tool, no agent; NNN = next ADR number from index)
  ↓
"write adr"
  → Write planning/<NNN>-plan-<slug>.md   (Phase 1, direct)
  → Write decisions/ADR-NNN.md (compressed decision, direct)
  → Update decisions/ADR-000-index.md (direct)

--lite (lite/SKILL.md):
  ↓ EnterPlanMode ──────────────────────── read-only zone
  Step 1 Graph precondition
  → Step 2 Cheap anchor resolution (graphify only; investigator fallback per existing rules)
  → Step 3 API-surface gate (route/API/GraphQL/REST/proto shape-affecting? → STOP + flag, escalate to full pipeline)
  → Step 4 Scope & Test Definition (Affected Files / New Files / Test Scenarios)
  ↓ ExitPlanMode = present output, no Write
  (escalate to full /realm-planning <topic> or --phase2 if scope grows, or if Step 3 flagged)
```
