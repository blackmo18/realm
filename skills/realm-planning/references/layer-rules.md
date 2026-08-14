# Layer → Rule/Skill Selection

Phase 2 Step 2. Layers classify **rules only** — scope comes from Phase 1 Anchor Set, never from a layer scan.

**Layers:**
- `frontend` — components, pages, hooks, CSS
- `backend` — API routes, server actions, middleware
- `data` — schema, migrations, repositories, queries
- `auth` — session, cookie, token, permissions
- `payments` — checkout, order, entitlement
- `infra` — env, build config, deployment

**Rules per active layer:**

| Layer | Rules |
|-------|-------|
| `frontend` | ECC `web/coding-style`, `web/patterns`, `web/performance`, `web/security` |
| `backend` | ECC `common/patterns`, `common/coding-style` |
| `data` | ECC `common/patterns` (repository section only) |
| `auth`/`payments` | ECC `common/security` (full) + `web/security` if frontend-adjacent |
| all | ECC `common/coding-style`, `common/testing` (always) |

Repository-local guidance (`AGENTS.md`, `CLAUDE.md`, or host rules) overrides defaults. Skip zero-surface rule sets.

**Skills per condition:**

| Condition | Skill |
|-----------|-------|
| New/unknown patterns | `research-ops` |
| 2+ paths from Phase 1 | `council` |
| New testable behavior | `tdd-workflow` |
