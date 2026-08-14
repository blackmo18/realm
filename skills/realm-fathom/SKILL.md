---
name: realm-fathom
description: >
  Deep investigation skill. Accepts a function, class, concept, or freeform question and consolidates live code with cached vault context. Uses graphify first, a bounded investigator fallback only when needed, and inline indexed vault lookup. Detects code/vault drift explicitly. Use before modifying unfamiliar code or auditing whether documentation matches implementation. Zero writes.
---

# realm-fathom

Investigate anything. Code truth + vault context. Drift flagged.

Host invocation: Claude Code and Gemini use `/realm-fathom`; Codex uses `$realm-fathom`.

## Syntax

```bash
/realm-fathom function:validateUser          # named function
/realm-fathom class:UserService              # named class
/realm-fathom system:PaymentPipeline         # named subsystem
/realm-fathom "how does auth flow work"      # freeform question
/realm-fathom validateUser                   # bare name (auto-detect type)
/realm-fathom "payment pipeline"             # concept
```

## Examples

```bash
/realm-fathom function:validateUser
→ Live: signature, flow, callers, error paths
→ Vault: why JWT, ADR refs, invariant notes
→ DRIFT flagged if vault says bool return but code returns Result<User>

/realm-fathom "how does the auth middleware chain work"
→ Investigator maps relevant files + functions end-to-end
→ Vault adds architectural intent, prior decisions
→ VERDICT: consolidated what + why

/realm-fathom class:PaymentService
→ Full class: responsibility, methods, deps from live code
→ Vault: why this abstraction exists, linked ADRs
```

## Source Hierarchy

| Source | Authoritative for |
|--------|------------------|
| Live code — graphify first, `cavecrew-investigator` as backup | behavior, signatures, flow, callers, current state |
| Vault (indexed inline lookup) | why, ADR refs, architectural intent, invariant rationale |
| Conflict | flagged as `VAULT DRIFT` — never silently blended |

Code truth is resolved cheapest-first: graphify's cached graph answers most
queries for the cost of one `graphify query` call, no subagent spawn. The
`cavecrew-investigator` crawler only runs as backup — when graphify is
missing, stale (source files changed since last index), or its match is too
thin to answer the query. This keeps token cost flat without losing
context: the report always states which source answered (`graphify` vs
`investigator`) so nothing is silently degraded.

## Guards

| Condition | Behavior |
|-----------|----------|
| `.realm/realm-state.json` missing | SOFT — proceed code-only, note vault unavailable |
| Vault initialized but no nodes match query | Note "no vault nodes" — proceed code-only |
| `graphify-out/graph.json` missing | SOFT — skip graphify seed, investigator runs cold |
| Graphify present but stale (files changed since index) | SOFT — investigator runs as backup, seed used as hint only |
| Graphify present, fresh, seed thin/no match | SOFT — investigator runs as backup |
| Entity not found in codebase | Flag "cannot locate in codebase" |
| Vault and code conflict on any fact | Flag `VAULT DRIFT` with both values |

## When to Use

| Trigger | Example |
|---------|---------|
| Understand how a function works before modifying it | `/realm-fathom function:processPayment` |
| Map a class before refactoring | `/realm-fathom class:AuthMiddleware` |
| Answer a freeform design question | `/realm-fathom "how does session refresh work"` |
| Audit: what vault says vs what code actually does | any vaulted entity |

## When NOT to Use

- Vault-only decision lookup → `/realm-recall`
- Planning architectural changes → `/realm-planning`
- Pipeline health check → `/realm-status`

---

## Procedure

### Step 0 — Parse input

From invocation args:
- Detect entity specifiers: `function:X`, `class:X`, `system:X` → extract `entityType` and `entityName`
- No specifier → set `entityType: freeform`, `entityName: ""`, use full arg as `query`
- Bare single word without prefix → treat as `freeform` (investigator will auto-detect type)

### Step 1 — Soft vault guard

Read `.realm/realm-state.json` from current working directory:
- Present → load `vaultPath`, `projectSlug`, `projectDir` → set `vaultAvailable: true`
- Missing → set `vaultAvailable: false`
  - Print: `Vault not initialized — proceeding code-only. Run /realm-forge to enable architectural context.`

### Step 2 — Run fathom procedure

If the host exposes `realm-agent-fathom` and delegation is permitted by the
current user/session policy, delegate with this prompt. Otherwise execute the
same investigation inline. Never require delegation for correctness.

```
projectRoot: <absolute path to current working directory>
realmFathomSkillDir: <directory containing this SKILL.md>
query: <full original query string, e.g. "function:validateUser" or "how does auth flow work">
entityType: <function|class|system|freeform>
entityName: <extracted name, or empty string if freeform>
vaultAvailable: <true|false>
vaultPath: <vaultPath or empty>
projectSlug: <projectSlug or empty>
projectDir: <projectDir or empty>

Investigate the query and return a consolidated fathom report.
Follow the full procedure in your instructions.
```

Surface the resulting fathom report directly to the user.
