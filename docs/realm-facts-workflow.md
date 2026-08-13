# Realm Facts — Team Workflow

Organization-wide knowledge facts: GitLab review, Microsoft Teams notifications, agent-ingestable.

## Overview

```
Setup → Create Fact → Submit MR → Teams Notify → Review → Approve → Merge → Team Sync → Agent Ingest
```

Central repo: `realm-facts` on GitLab. Product repos hold a pointer in `.realm/realm-state.json`.

## Roles

| Role | Actions |
|---|---|
| **Author** | Create facts, submit MRs, respond to review feedback |
| **Reviewer** | Review MRs, approve or request changes |
| **Team member** | Pull synced facts, query via `/realm-fact-recall`, ingest for agents |
| **Agent** | Consume compressed fact bundles via `/realm-fact-ingest` |

## Phase 1 — Setup (once per org)

### 1.1 Create central GitLab repo

```bash
# Create org/realm-facts on GitLab
git clone git@gitlab.example.com:org/realm-facts.git
cd realm-facts

# Bootstrap layout
python3 /path/to/realm/scripts/facts_init.py --facts-root .
git add . && git commit -m "init realm-facts" && git push
```

### 1.2 Configure MCP (Cursor)

Copy [mcp/cursor-mcp.example.json](../mcp/cursor-mcp.example.json) to `.cursor/mcp.json`.
Set env vars: `REALM_GITLAB_TOKEN`, `REALM_GITLAB_API_URL`, `REALM_TEAMS_WEBHOOK`.

### 1.3 Connect product repos

In each product repo:

```bash
/realm-facts-forge
# Provide path to local realm-facts clone
# Or: /realm-facts-forge --facts-url https://gitlab.example.com/org/realm-facts.git
```

Writes to `.realm/realm-state.json`:

```json
"factsRepo": {
  "url": "https://gitlab.example.com/org/realm-facts.git",
  "localPath": "/path/to/realm-facts",
  "branch": "main",
  "lastSync": null
}
```

## Phase 2 — Create a Fact

```bash
/realm-fact-new platform jwt-token-rotation
```

Agent gathers:
- Compressed summary (1-2 sentences)
- Evidence (Confluence links, repo refs)
- Owners and reviewers
- Tags

Output: `facts/platform/jwt-token-rotation/index.md` (status: `draft`)

Optional:
- Add docs in `docs/`
- Add diagrams in `diagrams/`
- Link related facts: `/realm-fact-link jwt-token-rotation --related session-refresh-policy`

## Phase 3 — Submit for Review

```bash
/realm-fact-submit jwt-token-rotation
```

Pipeline:
1. `facts_validate.py --mr-ready` — schema check
2. Git branch `fact/jwt-token-rotation` → push
3. GitLab MR created via MCP
4. Fact status → `review`
5. Microsoft Teams notification to org channel

Teams message:
```
📋 New fact review: JWT Token Rotation
Author: @alice | Reviewers: @bob
MR: https://gitlab.../merge_requests/42
Summary: JWT 15min expiry. Refresh via silent iframe.
```

## Phase 4 — Review and Approve

Reviewer:

```bash
/realm-fact-review jwt-token-rotation
/realm-fact-review jwt-token-rotation --approve
# or
/realm-fact-review jwt-token-rotation --request-changes "missing Confluence evidence"
```

Review checklist:
- [ ] Schema valid
- [ ] Compressed summary agent-useful
- [ ] Evidence links present
- [ ] No duplicate id
- [ ] Links consistent

On approval:
- MR merged on GitLab
- Fact status → `active`
- Teams: "✅ Fact approved — team pull latest"

On changes requested:
- MR comment posted
- Teams notifies author

## Phase 5 — Team Sync

After merge, team members:

```bash
/realm-fact-sync
```

Pulls latest from `main`, refreshes `facts-index.json`, updates `lastSync`.

## Phase 6 — Query and Agent Ingest

### Query facts

```bash
/realm-fact-recall jwt                          # tag/domain search
/realm-fact-recall jwt-token-rotation --deps    # with dependencies
/realm-fact-recall "payment settlement"         # semantic search
```

### Hand off to coding agent

```bash
/realm-fact-ingest jwt-token-rotation --bundle impl
```

Produces compact bundle for implementation agents:

```
FACT_BUNDLE:
  id: jwt-token-rotation
  compressed: JWT 15min expiry. Refresh via silent iframe.
  deps: [...]
  repo_refs: [...]
  drift_policy: live code wins; facts = intent
```

Paste bundle into agent prompt or use as session context.

## Fact Lifecycle

```mermaid
stateDiagram-v2
  [*] --> draft: realm-fact-new
  draft --> review: realm-fact-submit
  review --> draft: changes-requested
  review --> active: approved-and-merged
  active --> deprecated: superseded
  deprecated --> [*]
```

## Repository Structure

```
realm-facts/
├── facts/<domain>/<fact-id>/index.md
├── decisions/ADR-*.md
├── references/
├── facts-index.json      # generated
├── facts-graph.json      # generated
└── .realm/facts-state.json
```

## GitLab CI (recommended)

```yaml
validate-facts:
  script:
    - python3 scripts/facts_validate.py --facts-root .
    - python3 scripts/facts_index.py --facts-root .
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

## Skills Reference

| Skill | Purpose |
|---|---|
| `/realm-facts-forge` | Connect product repo to central facts |
| `/realm-fact-new` | Create new fact |
| `/realm-fact-link` | Link facts together |
| `/realm-fact-submit` | GitLab MR + Teams notification |
| `/realm-fact-review` | Reviewer approve/request changes |
| `/realm-fact-sync` | Pull latest approved facts |
| `/realm-fact-recall` | Query facts |
| `/realm-fact-ingest` | Bundle for other agents |

## Operating Rules

1. **One source of truth** — central `realm-facts` repo on GitLab `main`
2. **No direct push to main** — all facts via MR review
3. **Compressed required** — every active fact must have agent-ingestable `## Compressed`
4. **Owners assigned** — every fact has `@owner` responsible for accuracy
5. **Sync cadence** — run `/realm-fact-sync` at session start or after Teams approval notice
6. **Drift policy** — live code wins for behavior; facts explain intent; flag `FACT DRIFT`

## Troubleshooting

| Issue | Fix |
|---|---|
| No facts repo connected | `/realm-facts-forge` |
| MR validation fails | Fix errors from `facts_validate.py --mr-ready` |
| Teams notification skipped | Set `REALM_TEAMS_WEBHOOK` |
| GitLab MCP unavailable | Create MR manually, paste URL to skill |
| Stale local facts | `/realm-fact-sync --rebuild-index` |
