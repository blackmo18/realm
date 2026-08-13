# GitLab MCP for Realm Facts

GitLab integration for fact MR workflow: branch push → merge request → review → merge.

## Setup

### 1. Create GitLab Access Token

GitLab → Settings → Access Tokens:
- Scopes: `api`, `read_repository`, `write_repository`
- Store as `REALM_GITLAB_TOKEN`

### 2. Configure Cursor MCP

Project-level `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "gitlab": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-gitlab"],
      "env": {
        "GITLAB_PERSONAL_ACCESS_TOKEN": "<your-token>",
        "GITLAB_API_URL": "https://gitlab.example.com/api/v4"
      }
    }
  }
}
```

Set environment variables:

```bash
export REALM_GITLAB_TOKEN="<token>"
export REALM_GITLAB_PROJECT="org/realm-facts"
export REALM_GITLAB_API_URL="https://gitlab.example.com/api/v4"
```

### 3. Verify Connection

In Cursor, ask agent to list open merge requests on `org/realm-facts`.

## MCP Tools Used by Realm Facts

| Tool | Used by | Purpose |
|---|---|---|
| `create_merge_request` | `/realm-fact-submit` | Open fact review MR |
| `get_merge_request` | `/realm-fact-review` | Check MR status |
| `create_merge_request_note` | `/realm-fact-review` | Post review comments |
| `approve_merge_request` | `/realm-fact-review --approve` | Approve fact |
| `merge_merge_request` | `/realm-fact-review` | Merge after approval |
| `list_merge_requests` | status checks | List pending fact MRs |

## MR Conventions

- Branch: `fact/<fact-id>`
- Title: `[fact] <title> (<fact-id>)`
- Target: `main`
- Labels: `realm-facts`, `needs-review`

## GitLab CI (optional)

Add `.gitlab-ci.yml` to facts repo:

```yaml
validate-facts:
  stage: test
  script:
    - python3 scripts/facts_validate.py --facts-root .
    - python3 scripts/facts_index.py --facts-root .
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

Blocks MR merge if validation fails.

## Self-Hosted GitLab

Set `GITLAB_API_URL` to your instance:
- `https://gitlab.company.com/api/v4`

No code changes required.
