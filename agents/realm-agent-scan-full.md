# Realm Agent Scan — Full Mode Procedure

Variables already in context: `projectRoot`, `vaultPath`, `projectSlug`, `projectDir`, `docs` registry.

---

### Step 1 — Inventory existing vault docs

Read `<projectDir>/` recursively. Build list of existing `.md` files relative to `projectDir`. Check against registry:
- `committed` in state and on disk → current
- On disk but not in registry → add as `committed` (orphaned)
- `committed` in registry but missing from disk → mark `stale`

### Step 2 — Size check then spawn investigators

Count source files in `projectRoot` (exclude `node_modules/`, `.git/`, `dist/`, `build/`, `__pycache__/`):

```bash
find <projectRoot> -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.py" -o -name "*.go" -o -name "*.rs" -o -name "*.rb" -o -name "*.java" -o -name "*.swift" -o -name "*.kt" -o -name "*.dart" \) \
  ! -path "*/node_modules/*" ! -path "*/.git/*" ! -path "*/dist/*" ! -path "*/build/*" ! -path "*/__pycache__/*" \
  | wc -l
```

**< 20 source files → single investigator path:**

Spawn one `cavecrew-investigator`:

```
Map this codebase for Obsidian node-graph documentation. Find and compress:

1. SERVICES / CLASSES — each major class/service: name, responsibility, public methods, key deps
2. FUNCTIONS / UTILITIES — critical standalone functions: name, signature, responsibility, who calls it
3. EVENTS / COMMUNICATION — event names, emitters, listeners; API routes; patterns
4. DATA LAYER — DB tables/collections, Redis patterns, schema relationships
5. CONFIGURATION — env vars, config files, safety bounds, named constraints
6. TECH STACK — languages, frameworks, libraries, build/test tools
7. ENTRY POINTS — bootstrap files, CLI entry, init sequences
8. ARCHITECTURAL PATTERNS — decision evidence: "we do X instead of Y because...", naming conventions, guards
9. EXISTING DOCS — list all .md files, README*, IMPLEMENTATION_PLAN*, *.plan.md

Output format: caveman-compressed, grouped by category. For classes/functions, include caveman one-liners suitable for node frontmatter:
  - Function: signature + responsibility + typical call frequency/perf
  - Class: responsibility + key deps + typical users
  - Decision signal: code pattern with rationale

No line numbers. File paths where relevant for classes and functions.
```

**≥ 20 source files → 4-category parallel swarm:**

Spawn 4 `cavecrew-investigator` agents **in parallel**, one per category cluster:

**Investigator A — Structure:**
```
Map this codebase for Obsidian node-graph documentation. Focus ONLY on:

1. SERVICES / CLASSES — each major class/service: name, responsibility, public methods, key deps
2. ENTRY POINTS — bootstrap files, CLI entry, init sequences
3. TECH STACK — languages, frameworks, libraries, build/test tools

Output: caveman-compressed, grouped by category.
Class one-liner: responsibility + key deps + typical users.
File paths where relevant.
```

**Investigator B — Behavior:**
```
Map this codebase for Obsidian node-graph documentation. Focus ONLY on:

1. FUNCTIONS / UTILITIES — critical standalone functions: name, signature, responsibility, who calls it
2. EVENTS / COMMUNICATION — event names, emitters, listeners; API routes; patterns

Output: caveman-compressed, grouped by category.
Function one-liner: signature + responsibility + typical call frequency/perf.
File paths where relevant.
```

**Investigator C — Data & Config:**
```
Map this codebase for Obsidian node-graph documentation. Focus ONLY on:

1. DATA LAYER — DB tables/collections, Redis patterns, schema relationships
2. CONFIGURATION — env vars, config files, safety bounds, named constraints

Output: caveman-compressed, grouped by category.
No line numbers. File paths where relevant.
```

**Investigator D — Decisions & Docs:**
```
Map this codebase for Obsidian node-graph documentation. Focus ONLY on:

1. ARCHITECTURAL PATTERNS — decision evidence: "we do X instead of Y because...", naming conventions, guards
2. EXISTING DOCS — list all .md files, README*, IMPLEMENTATION_PLAN*, *.plan.md

Output: caveman-compressed, grouped by category.
Decision signal: code pattern with rationale.
```

Wait for all investigators to complete. Merge all outputs into single result set before proceeding to Step 3.

### Step 3 — Load existing vault summaries

For each `committed` doc in `overview.md`, `architecture.md`, `decisions/ADR-000-index.md`: read first 50 lines only. Used for gap analysis.

### Step 4 — Diff repo vs vault

Using investigator output and vault summaries, identify gaps:

**architecture.md gaps:** services/events/schema in code not in vault.
**overview.md gaps:** milestones completed in code but not in vault; new stack deps.

**New node candidates:**
- **Function nodes:** critical standalone functions/methods not in vault. High-call-frequency, cross-service utilities, perf-critical paths.
- **Class nodes:** major services/modules, core utilities, domain classes.
- **Decision nodes:** signals: `"DO NOT change this because..."`, `"no direct service calls"`, config bounds encoding rules, files named `*Safeguard*` / `*Guard*` / `*Validator*`.
- **Discovery nodes:** tech choices, perf characteristics, architectural constraints.
- **Session log:** always plan one entry.

### Step 5 — Draft the manifest

Write `<projectRoot>/.realm/manifest-draft.md` using format from realm-conventions.md (already in context).

Content rules:
- Full YAML frontmatter per node (id, type, status, tags, created, updated)
- Compressed one-liner per node
- Full section per node
- Wikilinks: `[[nodeId]]` for cross-refs
- overview.md: only update milestones/stack if diverged; preserve existing prose
- architecture.md: append new rows only; never rewrite existing

### Step 6 — Update realm-state.json

Run this Bash command. Do NOT use Read/Write tools for this step — one Bash call only:

```bash
STATE="<projectRoot>/.realm/realm-state.json"
NOW=$(date -u +"%Y-%m-%dT%H:%M:%S+00:00")
# PLANNED_JSON: {"path":{"status":"planned","updated":null},...} for new nodes
# STALE_JSON:   {"path":{"status":"stale","updated":null},...} for stale nodes
PLANNED_JSON='<construct from gap analysis>'
STALE_JSON='<construct from stale list, or {} if none>'
jq --arg now "$NOW" --argjson planned "$PLANNED_JSON" --argjson stale "$STALE_JSON" \
  '.phase.lastRun = $now | .phase.draftReady = true | .docs += $planned | .docs += $stale' \
  "$STATE" > "${STATE}.tmp" && mv "${STATE}.tmp" "$STATE"
```

### Step 7 — Print gap map

```
realm-agent-scan complete  [full]
  scanned:  <N services/modules> | <N events> | <N tables>

GAP MAP
  new docs planned:     <N>  (<list of relative paths>)
  docs to update:       <N>  (<list>)
  new ADR candidates:   <N>  (<list of titles>)
  vault unchanged:      <N> committed docs already current

  draft staged at: .realm/manifest-draft.md

Review the draft, then run /realm-manifest to write to vault.
```
