# Realm Skills — Token Efficiency Audit

Evaluated against [agent-token-efficiency.md](../.claude/rules/agent-token-efficiency.md).

Audit date: 2026-08-14. Re-baselined: 2026-08-14 (same-day pass fixed realm-forge, realm-recall,
and a dead-duplication bug found while verifying the original findings).

---

## Scorecard Summary

| Skill | Lines | Agent Spawns | Scripts? | Verdict |
|:---|:---:|:---:|:---:|:---:|
| [realm-forge](../skills/realm-forge/SKILL.md) | 54 | 1 (`realm-agent-forge`, 64 lines) | ✅ `forge_init.py` | ✅ PASS |
| [realm-recall](../skills/realm-recall/SKILL.md) | 214 + 2 fragments | 0–1 (fallback only) | ❌ | ✅ PASS |
| [realm-concise](../skills/realm-concise/SKILL.md) | routed + 3 procedures | 0 | ✅ `concise.py` | ✅ PASS |
| [realm-facts](../skills/realm-facts/SKILL.md) | routed + 8 procedures | 0 | ✅ `facts.py` | ✅ PASS |
| [realm-status](../skills/realm-status/SKILL.md) | inline | 0 | bounded live scan | ✅ PASS |
| [realm-fathom](../skills/realm-fathom/SKILL.md) | routed + 4 references | 1 only for deep reconciliation | graphify-first | ✅ PASS |
| [realm-planning](../skills/realm-planning/SKILL.md) | routed procedures | 2 semantic planners | graphify-first | ⚠️ WARN |

---

## Per-Skill Detail

### ✅ PASS — realm-concise

**Exemplary.** This skill was clearly built *after* the token efficiency rules were established.

- **Anti-Pattern 1 (LLM mechanical work)**: ✅ Not present. `concise.py` owns all LOC counting, scoring, state mutation, and ledger rendering. LLM only reasons about *one* recommended file.
- **Anti-Pattern 1a (Shared-state lifecycle)**: ✅ Not present. Script owns the full lifecycle (`scan`/`approve`/`plan`/`done`/`ignore`).
- **Anti-Pattern 3 (Fat prompt)**: ✅ Root SKILL.md is 73 lines with routing to 3 small sub-fragments (51–59 lines each). Only the relevant fragment loads.
- **Anti-Pattern 6 (Tool accumulation)**: ✅ Scan/next/query = one `python3 concise.py` call. No multi-step tool chains.
- **Anti-Pattern 7 (Monolithic reference)**: ✅ References split into `recommend-rubric.md` (58 lines) and `scoring.md`. Load-on-demand.
- **Anti-Pattern 11 (Live scan)**: ✅ Script caches state in `.realm/concise-state.json`.

**No findings.**

---

### ✅ PASS — realm-facts

**Exemplary.** Same discipline as realm-concise.

- **Anti-Pattern 1**: ✅ `facts.py` (644 lines) owns all parsing, schema validation, index/graph generation, and status transitions. LLM only interviews user for new fact content and judges reviewer quality.
- **Anti-Pattern 1a**: ✅ Explicit rule: "Never hand-edit a fact file's frontmatter, `facts-index.json`, `facts-graph.json`."
- **Anti-Pattern 3**: ✅ Root SKILL.md is 110 lines, routes to 8 small sub-fragments. Only the triggered fragment loads.
- **Anti-Pattern 4 (Whole-file reads)**: ✅ Rule 3: "State reads go through `facts.py state`" — one script call, not a full JSON read.
- **Anti-Pattern 11**: ✅ Rule 4: "`recall`/`ingest` read the index, never the tree."

**No findings.**

---

### ✅ PASS — realm-status

**Clean.** Reads state, counts nodes, prints output. No agent spawn.

- **Anti-Pattern 6**: ✅ Inline execution with Read + grep. No subagent.
- **Anti-Pattern 11**: ✅ Step 2 uses one bounded live-file scan; no stale writer-owned cache.

---

### ✅ PASS — realm-forge *(fixed 2026-08-14, was ⚠️ WARN)*

Was: `realm-agent-forge` (79 lines) did all mechanical work itself — mkdir, template writes,
ADR index stub, host guidance anchor, overview.md, `.gitignore`, `realm-state.json` — as a chain of
Write/Bash tool calls.

Fix applied: `skills/realm-forge/scripts/forge_init.py` now owns the entire bootstrap — `scaffold_dirs`,
`update_gitignore`, `write_templates`, `write_adr_index`, `write_host_anchor`, `write_overview`,
`scan_existing_docs`, `write_state` — all skip-if-exists, one `python3 forge_init.py` call.
`agents/realm-agent-forge.md` shrank 79 → 64 lines and now does only Step 1 (parse
package.json/README/plan metadata — genuine judgement) and Step 3 (print the script's summary).
Verified idempotent: two consecutive runs against a scratch project produce byte-identical output
(`md5sum` match across every written file, including `realm-state.json`).

- **Anti-Pattern 1**: ✅ Fixed. Zero mechanical Write calls remain in the agent.
- **Anti-Pattern 6**: ✅ Fixed. ~10 tool calls collapsed into 1 bash call.

**No findings.**

---

### ✅ PASS — realm-recall *(fixed 2026-08-14, was ⚠️ WARN)*

Was: 324 lines in one file — the longest SKILL.md in the repo — with canvas expansion and
output rendering loaded unconditionally.

Fix applied:
- Step 3a uses a bounded exact-ID grep against live vault files.
- Extracted `references/canvas-expansion.md` (83 lines: trigger-word table, resolution steps,
  worked examples, Step 4.5 procedure) and `references/output-format.md` (53 lines: Step 5
  rendering templates + Step 6 footer). Both load only when their step actually runs — canvas
  expansion only fires when a loaded node has `source_plan`.
- Root SKILL.md: 324 → 214 lines.

- **Anti-Pattern 3 (Fat prompt)**: ✅ Fixed. 214 lines, and canvas/format content no longer loads unconditionally.
- **Anti-Pattern 7 (Monolithic reference)**: ✅ Fixed. Two load-on-demand fragments, matching the realm-concise/realm-facts pattern.
- **Anti-Pattern 11 (Live scan vs cache)**: ✅ Exact-ID, tag, and filename searches are bounded to the project vault and always reflect current files.

**No findings.**

---

### ✅ PASS — realm-fathom

| # | Anti-Pattern | Severity | Finding |
|:---|:---|:---:|:---|
| 3 | **Fat agent prompt** | FIXED | Agent wrapper is under 80 lines. It loads one small entity-specific reference and delays output-format loading until render time. |
| 9 | **Model tier** | INTENTIONAL | Codex uses balanced Terra and Claude uses Sonnet. Gemini execution uses the latest Pro model by explicit policy; mechanical work remains on Flash. Mechanical vault lookup stays inline and index-first. |

**What's good:**
- Source hierarchy is well-defined (graphify → investigator fallback → vault).
- Drift detection is genuine LLM reasoning work — correctly assigned to an agent.
- Guards degrade gracefully (code-only when vault absent).

No HIGH finding remains. Investigator templates are split by query type; vault lookup no longer spawns a second agent.

---

### ⚠️ WARN — realm-planning

| # | Anti-Pattern | Severity | Finding |
|:---|:---|:---:|:---|
| 7 | **Monolithic reference doc** | MEDIUM | `references/vault-conventions.md` (81 lines) and `references/plan-template.md` (133 lines) are loaded by phase1/phase2. The plan template is 133 lines of boilerplate that could be a script-generated skeleton. |
| 3a | **Fat-prompt regression risk** | MEDIUM | 10 reference files totaling ~465 lines. Well-fragmented *now*, but high risk of regrowth — each new feature (contract delta, anchor resolution, logging plan) added a new reference. |

**What's good:**
- **Best-in-class fragmentation**: Root SKILL.md (127 lines) routes to 4 sub-skills + 10 reference fragments. Only the triggered path loads.
- **Correct agent usage**: `architect` (20 lines) and `code-architect` (13 lines) are ultra-slim agent definitions — genuine reasoning work, not mechanical.
- **Contract gate pattern**: Enforces ordering without LLM coordination — structural, not prompt-based.
- **Graphify-first design**: Deterministic graph traversal before any agent spawn.

**Recommendations (deferred — low return relative to churn; `plan-template.md` only loads in phase2, not by default):**
1. **Templatize plan output** (MEDIUM): `plan-template.md` (133 lines) could become a script that emits the skeleton file, with the agent filling only the semantic sections.
2. **Monitor reference growth** (LOW): 10 fragments / 465 lines is approaching the boundary. Track total reference line count as a metric — if it exceeds ~600 lines, audit for consolidation.

---

## Anti-Pattern 10 finding (outside SKILL.md scope, found during re-verification)

Verifying the original audit's "no dead duplication" claim against the live tree turned up a real
hit: `.gemini/agents/*.md` were hand-maintained byte copies of `agents/*.md`, committed separately.
Seven of eight were identical; `.gemini/agents/architect.md` had **drifted** — missing the
"Tool discipline (keep token spend low)" block present in `agents/architect.md`, meaning Gemini
users got an architect agent without the graphify-first / grep-before-read discipline the other
hosts had. `.claude/agents/*.md` already avoided this — it's gitignored and generated at
install/update time from `agents/*.md`, never committed.

**Fixed 2026-08-14**: `.gemini/agents/*.md` removed from git, `.gemini/` added to `.gitignore`,
and `bin/install.js` / `install.sh` / `update.sh` now copy Gemini's native agent files straight
from `agents/*.md` (mirroring the existing Claude branch), so `agents/` is the single source of
truth and this class of drift is now structurally impossible. Verified: a scratch local install
(`node bin/install.js --agent gemini --local <dir>`) derives every agent from `agents/` and changes
only the host-specific model identifier while removing Claude-only tool names so Gemini inherits
its registered host tools. Also fixed adjacent doc/uninstall bugs where `INSTALL.md`/`UNINSTALL.md`/`REQUIREMENTS.md`
told users to `rm -f ~/.gemini/agents/*.toml` — Gemini agents are `.md`, not `.toml`; that glob
matched nothing and left stale agent files behind on uninstall.

This wasn't in the original rubric's per-skill scope (it's install-tooling, not a SKILL.md), but
it's the same category (10 — dead duplication) and cost real correctness, not just tokens.

---

## Anti-Pattern Heatmap (Across All Skills)

| Anti-Pattern | realm-forge | realm-fathom | realm-recall | realm-planning | realm-concise | realm-facts | realm-status |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 — LLM mechanical work | ✅ | — | — | — | ✅ | ✅ | ✅ |
| 1a — Shared-state lifecycle | — | — | — | — | ✅ | ✅ | — |
| 2 — Redundant cross-stage | — | — | — | — | — | — | — |
| 3 — Fat prompt | — | ✅ | ✅ | — | ✅ | ✅ | ✅ |
| 3a — Fat-prompt regression | — | — | — | 🟡 MED | — | — | — |
| 4 — Whole-file reads | — | — | — | — | — | ✅ | — |
| 5 — Read-modify-write churn | — | — | — | — | — | — | — |
| 6 — Tool accumulation | ✅ | — | — | — | ✅ | — | ✅ |
| 7 — Monolithic reference | — | ✅ | ✅ | 🟡 MED | ✅ | — | — |
| 8 — Variable data early | — | — | — | — | — | — | — |
| 9 — Over-strong model | — | ✅ | — | — | ✅ | ✅ | — |
| 10 — Dead duplication | — | — | — | — | — | — | — |
| 11 — Live scan vs cache | — | — | 🟡 partial (3b/3c) | — | ✅ | ✅ | 🟢 LOW |

(`agents/*.md` vs `.gemini/agents/*.md` duplication is tracked separately above — it isn't a
per-skill row since it spans install tooling, not a single SKILL.md.)

---

## Priority Recommendations

### HIGH — Fix before next release

None.

### MEDIUM — Fix when practical

| # | Skill | Action |
|:---|:---|:---|
| 3 | **realm-planning** | Convert `plan-template.md` to a script-generated skeleton. |

---

## Verdict

| Category | Count |
|:---|:---:|
| ✅ PASS | 6 (realm-concise, realm-facts, realm-status, realm-forge, realm-recall, realm-fathom) |
| ⚠️ WARN | 1 (realm-planning) |
| 🛑 BLOCK | 0 |

**No CRITICAL or HIGH anti-pattern remains.** Realm-fathom now uses a sub-80-line semantic agent,
one small query-specific reference, delayed output-format loading, and bounded vault lookup inline.
The only remaining warning is the planning pipeline's medium-sized reference surface.

## Spawn Graph and Budgets

| Entry | Delegation | Model class | Expected tool budget |
|---|---|---|---:|
| realm-concise | none; deterministic script | basic | 1 script call per command |
| realm-facts | none; deterministic script | current session | 1–3 script/git calls |
| realm-recall/status | none; bounded live lookup | current session | 1 state read + bounded scan |
| realm-forge | realm-agent-forge → forge_init.py | balanced execution | metadata reads + 1 script call |
| realm-fathom | realm-agent-fathom → optional investigator only | balanced reasoning | graph query + bounded vault lookup; one fallback spawn maximum |
| realm-planning phase 1 | architect | strongest planning | graph-first bounded reads |
| realm-planning phase 2 | code-architect | strongest planning | at most 3 graph gap-fill calls |

Agent prompt sizes: architect 20 lines, code-architect 13, concise 22, fathom 70,
forge 65, planning 22. Query agent removed. Host adapters select the cheapest tier that
holds the quality bar; deterministic work remains in scripts.
