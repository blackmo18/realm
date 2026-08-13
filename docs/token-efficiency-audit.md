# Realm Skills — Token Efficiency Audit

Evaluated against [agent-token-efficiency.md](.claude/rules/agent-token-efficiency.md).

Audit date: 2026-08-14

---

## Scorecard Summary

| Skill | Lines | Agent Spawns | Scripts? | Verdict |
|:---|:---:|:---:|:---:|:---:|
| [realm-forge](skills/realm-forge/SKILL.md) | 54 | 1 (`realm-agent-forge`) | ❌ | ⚠️ WARN |
| [realm-fathom](skills/realm-fathom/SKILL.md) | 120 | 1 (`realm-agent-fathom`) | ❌ | ⚠️ WARN |
| [realm-recall](skills/realm-recall/SKILL.md) | 324 | 0–1 (fallback only) | ❌ | ⚠️ WARN |
| [realm-planning](skills/realm-planning/SKILL.md) | 115 + 4 fragments | 2 (`architect`, `code-architect`) | ❌ | ⚠️ WARN |
| [realm-concise](skills/realm-concise/SKILL.md) | 73 + 3 fragments | 0 | ✅ `concise.py` | ✅ PASS |
| [realm-facts](skills/realm-facts/SKILL.md) | 110 + 8 fragments | 0 | ✅ `facts.py` | ✅ PASS |
| [realm-status](skills/realm-status/SKILL.md) | 83 | 0 | ❌ | ✅ PASS |

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
- **Anti-Pattern 11**: ✅ Step 2 checks `nodeIndex` in state first, falls back to `find` only if cache absent.

> [!TIP]
> **Minor opportunity (LOW):** Step 2 tag-frequency grep (`grep -rh ... | sort | uniq -c | sort -rn`) runs on every invocation. If tag counts were cached in `nodeIndex` by the write script, this grep could be eliminated. Not a blocker — this is a single bash call, ~10 tokens of stdout.

---

### ⚠️ WARN — realm-recall

| # | Anti-Pattern | Severity | Finding |
|:---|:---|:---:|:---|
| 3 | **Fat prompt** | HIGH | 324 lines — the longest SKILL.md in the entire repo. Loaded into context on every recall invocation. |
| 7 | **Monolithic reference** | MEDIUM | Unlike realm-concise and realm-facts, realm-recall has **no** sub-fragments or `references/` directory. The full 324-line procedure, canvas lazy-load logic, and output formatting are all in one file. |
| 11 | **Live scan replacing cacheable index** | MEDIUM | Step 3a/3b/3c use `grep -rl` and glob over `<projectDir>/` on every invocation. If the write script cached a `nodeIndex` (id→path, tag→paths maps) in `realm-state.json`, these could be simple JSON lookups. |

**What's good:**
- Resolution ladder (3a→3b→3c→3d) minimizes agent spawns — only 3d (semantic NL fallback) spawns `realm-agent-query`.
- `--count` and `--trace` flags are token-efficient by design.
- Canvas lazy-load intent-mapping is well-designed (deterministic word-match, not LLM reasoning).

**Recommendations:**
1. **Split into fragments** (HIGH): Move Steps 4.5 (canvas expansion) and Step 5 (output formatting) into `references/canvas-expansion.md` and `references/output-format.md`. Root SKILL.md becomes ~130 lines — a routing + procedure skeleton. Canvas and format rules load on-demand.
2. **Cache a node index** (MEDIUM): Have the vault write script (realm-forge, write-adr) maintain `nodeIndex: { byId: {}, byTag: {}, counts: {} }` in `realm-state.json`. Steps 3a/3b become JSON key lookups instead of grep.

---

### ⚠️ WARN — realm-forge

| # | Anti-Pattern | Severity | Finding |
|:---|:---|:---:|:---|
| 1 | **LLM doing mechanical work** | HIGH | `realm-agent-forge` (79 lines) creates directories, writes template files, seeds `realm-state.json`, and appends `.gitignore`. These are all deterministic operations with exactly one correct output. |
| 6 | **Mid-chain tool accumulation** | MEDIUM | The forge agent likely emits 8–12+ tool calls (mkdir, write overview.md, write architecture.md, write ADR index, write state JSON, append .gitignore, etc.) — each result accumulates in context. |

**What's good:**
- SKILL.md is slim (54 lines) and cleanly separates interactive (vault path resolution) from mechanical (agent spawn).
- Idempotent design is correct.

**Recommendations:**
1. **Move to a script** (HIGH): Create `scripts/forge.sh` or `scripts/forge.py` that accepts `--vault-path` and `--project-slug` arguments. Handles all directory creation, template writing, state seeding, and .gitignore mutation in one invocation. The skill SKILL.md handles the interactive Step 1 (vault path resolution with user), then runs the script instead of spawning an agent.
2. This collapses ~10 tool calls into 1 bash call with small stdout.

---

### ⚠️ WARN — realm-fathom

| # | Anti-Pattern | Severity | Finding |
|:---|:---|:---:|:---|
| 3 | **Fat agent prompt** | HIGH | `realm-agent-fathom` is 81 lines + it loads `realm-agent-fathom-templates` (134 lines) for output formatting. That's 215 lines of system prompt on every spawn. |
| 9 | **Over-strong model** | MEDIUM | Fathom always spawns a full agent to do graphify query + vault lookup + drift detection. For simple named-entity queries (`function:validateUser`), the skill itself could run `graphify query validateUser`, read the vault via inline grep, and only spawn the agent for complex freeform questions. |

**What's good:**
- Source hierarchy is well-defined (graphify → investigator fallback → vault).
- Drift detection is genuine LLM reasoning work — correctly assigned to an agent.
- Guards degrade gracefully (code-only when vault absent).

**Recommendations:**
1. **Split fathom-templates** (HIGH): The 134-line template file is loaded every spawn regardless of query type. Split into per-output-type fragments so only the relevant template loads.
2. **Inline simple entity lookups** (MEDIUM): For `function:X` or `class:X` queries where graphify exists and is fresh, the skill can run `graphify query X` inline, grep the vault, and only spawn the agent if: graphify is absent/stale, the query is freeform, or drift is detected. This avoids an agent spawn for the 80% case.

---

### ⚠️ WARN — realm-planning

| # | Anti-Pattern | Severity | Finding |
|:---|:---|:---:|:---|
| 7 | **Monolithic reference doc** | MEDIUM | `references/vault-conventions.md` (81 lines) and `references/plan-template.md` (133 lines) are loaded by phase1/phase2. The plan template is 133 lines of boilerplate that could be a script-generated skeleton. |
| 3a | **Fat-prompt regression risk** | MEDIUM | 10 reference files totaling ~465 lines. Well-fragmented *now*, but high risk of regrowth — each new feature (contract delta, anchor resolution, logging plan) added a new reference. |

**What's good:**
- **Best-in-class fragmentation**: Root SKILL.md (115 lines) routes to 4 sub-skills + 10 reference fragments. Only the triggered path loads.
- **Correct agent usage**: `architect` (13 lines) and `code-architect` (13 lines) are ultra-slim agent definitions — genuine reasoning work, not mechanical.
- **Contract gate pattern**: Enforces ordering without LLM coordination — structural, not prompt-based.
- **Graphify-first design**: Deterministic graph traversal before any agent spawn.

**Recommendations:**
1. **Templatize plan output** (MEDIUM): `plan-template.md` (133 lines) could become a script that emits the skeleton file, with the agent filling only the semantic sections. Currently the agent reads the full template and hand-assembles the output.
2. **Monitor reference growth** (LOW): 10 fragments / 465 lines is approaching the boundary. Track total reference line count as a metric — if it exceeds ~600 lines, audit for consolidation.

---

## Anti-Pattern Heatmap (Across All Skills)

| Anti-Pattern | realm-forge | realm-fathom | realm-recall | realm-planning | realm-concise | realm-facts | realm-status |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 — LLM mechanical work | 🔴 HIGH | — | — | — | ✅ | ✅ | ✅ |
| 1a — Shared-state lifecycle | — | — | — | — | ✅ | ✅ | — |
| 2 — Redundant cross-stage | — | — | — | — | — | — | — |
| 3 — Fat prompt | — | 🔴 HIGH | 🔴 HIGH | — | ✅ | ✅ | ✅ |
| 3a — Fat-prompt regression | — | — | — | 🟡 MED | — | — | — |
| 4 — Whole-file reads | — | — | — | — | — | ✅ | — |
| 5 — Read-modify-write churn | — | — | — | — | — | — | — |
| 6 — Tool accumulation | 🟡 MED | — | — | — | ✅ | — | ✅ |
| 7 — Monolithic reference | — | 🟡 MED | 🟡 MED | 🟡 MED | ✅ | — | — |
| 8 — Variable data early | — | — | — | — | — | — | — |
| 9 — Over-strong model | — | 🟡 MED | — | — | — | — | — |
| 10 — Dead duplication | — | — | — | — | — | — | — |
| 11 — Live scan vs cache | — | — | 🟡 MED | — | ✅ | ✅ | 🟢 LOW |

---

## Priority Recommendations

### HIGH — Fix before next release

| # | Skill | Action | Est. Savings |
|:---|:---|:---|:---|
| 1 | **realm-forge** | Replace `realm-agent-forge` with `scripts/forge.sh`. Skill handles interactive vault path, script handles all writes. | ~8–12 tool calls → 1 bash call. ~5k tokens/run saved. |
| 2 | **realm-recall** | Split SKILL.md (324→~130 lines) into root + `references/canvas-expansion.md` + `references/output-format.md`. | ~190 lines removed from default load. |
| 3 | **realm-fathom** | Split `fathom-templates.md` (134 lines) into per-type fragments. Inline simple entity lookups for the graphify-present case. | ~134 lines removed from default agent prompt. Avoid agent spawn for 80% of queries. |

### MEDIUM — Fix when practical

| # | Skill | Action |
|:---|:---|:---|
| 4 | **realm-recall** | Cache `nodeIndex` (id→path, tag→paths) in `realm-state.json`, refreshed by write operations. Steps 3a/3b become JSON lookups. |
| 5 | **realm-planning** | Convert `plan-template.md` to a script-generated skeleton. |
| 6 | **realm-status** | Cache tag frequency in `nodeIndex`. |

---

## Verdict

| Category | Count |
|:---|:---:|
| ✅ PASS | 3 (realm-concise, realm-facts, realm-status) |
| ⚠️ WARN | 4 (realm-forge, realm-fathom, realm-recall, realm-planning) |
| 🛑 BLOCK | 0 |

**No CRITICAL anti-patterns remain** (realm-forge's mechanical-work issue is HIGH, not CRITICAL, because the agent prompt is slim at 79 lines and the tool chain is bounded). **Overall: the pipeline is shippable** but has clear optimization headroom in the four WARN skills.

The two newest skills (realm-concise, realm-facts) demonstrate the correct pattern: **script owns state, LLM only reasons**. The older skills (forge, fathom, recall) predate the efficiency rules and would benefit from the same treatment.
