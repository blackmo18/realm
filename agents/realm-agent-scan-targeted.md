# Realm Agent Scan — Targeted Mode Procedure

Variables already in context: `projectRoot`, `vaultPath`, `projectSlug`, `projectDir`, `targets`, `docs` registry.

**STOP after Step T5. Do not continue to any full-mode steps.**

---

### Step T1 — Locate target source files

For each target in `targets`:
1. Search `projectRoot` for source file:
   - `function:validateUser` → grep for `function validateUser`, `def validate_user`, `func validateUser`, `validateUser(` etc.
   - `class:UserService` → grep for `class UserService`, `struct UserService`, etc.
   - Multiple hits: pick primary definition (exclude test files).
2. Not found → print `Cannot locate source for <target>. Run full /realm-phase.` skip this target.

If already-read files are listed in the invocation prompt — do NOT re-read them. Use their content from context.

### Step T2 — Cluster targets and spawn parallel investigators

**Clustering rules:**
- Group located targets by source directory prefix (first two path segments from `projectRoot`).
- Total located targets ≤ 2 → skip clustering, use single investigator (spawn overhead not justified).
- Total ≥ 3 → form domain clusters. Merge any cluster with < 2 members into nearest directory neighbor. Cap at 4 clusters.

**Single investigator path** (≤ 2 targets):

Spawn one `cavecrew-investigator`:

```
Analyze ONLY these entities in this repo:
<list of targets with file paths from T1>

For each, extract:
- Full signature (params + return type)
- Responsibility (one-liner)
- Dependencies ([[links]])
- Callers / dependents (if findable)
- Any inline architectural comments ("DO NOT", "invariant", "perf note")
- Performance characteristics if benchmarks/comments present

Output: caveman-compressed, one block per entity.
```

**Swarm path** (≥ 3 targets → N clusters, max 4):

Spawn N `cavecrew-investigator` agents **in parallel** — one per cluster:

```
Analyze ONLY these entities (cluster <label — e.g. auth, payment, infra>):
<list of targets in this cluster with file paths>

For each, extract:
- Full signature (params + return type)
- Responsibility (one-liner)
- Dependencies ([[links]])
- Callers / dependents (if findable)
- Any inline architectural comments ("DO NOT", "invariant", "perf note")
- Performance characteristics if benchmarks/comments present

Output: caveman-compressed, one block per entity.
```

Wait for all N investigators to complete. Merge all outputs into single result set before proceeding to T3.

### Step T3 — Diff targeted entities vs vault

For each target, check if node exists (`<projectDir>/functions/<id>.md`, `<projectDir>/classes/<id>.md`).
- Exists: diff investigator output vs node first 50 lines → plan `status: update`
- Missing: plan `status: new`

### Step T4 — Draft targeted manifest

Write `<projectRoot>/.realm/manifest-draft.md` with targeted node sections only. Set `mode: targeted` in Meta block. Use manifest-draft.md format from realm-conventions.md (already in context).

### Step T5 — Update realm-state.json and print gap map

Run this Bash command to update realm-state.json. Do NOT use Read/Write tools for this step — one Bash call only:

```bash
STATE="<projectRoot>/.realm/realm-state.json"
NOW=$(date -u +"%Y-%m-%dT%H:%M:%S+00:00")
# Construct DOCS_JSON: JSON object mapping each planned node path to its status entry.
# e.g. '{"functions/CartProvider.md":{"status":"planned","updated":null}}'
DOCS_JSON='<construct from planned nodes list>'
jq --arg now "$NOW" --argjson docs "$DOCS_JSON" \
  '.phase.lastRun = $now | .phase.draftReady = true | .docs += $docs' \
  "$STATE" > "${STATE}.tmp" && mv "${STATE}.tmp" "$STATE"
```

Print:
```
realm-agent-scan complete  [targeted]
  entities:  <list of targets>

GAP MAP
  new docs planned:  <N>
  docs to update:    <N>

  draft staged at: .realm/manifest-draft.md
  cost:            <"single investigator (<N> targets)" | "swarm: <N> parallel investigators (<N> clusters)">

Review, then run /realm-manifest to write to vault.
```
