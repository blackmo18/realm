# Realm Facts MCP Integration

MCP servers required for team-wide facts workflow (GitLab MR + Microsoft Teams notifications).

## Required MCPs

| MCP | Purpose | Config |
|---|---|---|
| GitLab | Create MRs, approve, comment, fetch status | [gitlab/README.md](gitlab/README.md) |
| Microsoft Teams | Post review requests, approvals, digests | [teams/README.md](teams/README.md) |

## Optional MCPs

| MCP | Purpose | Config |
|---|---|---|
| Confluence | Verify Confluence links, fetch page titles | [confluence/README.md](confluence/README.md) |
| Filesystem/Git | Local facts repo read/write (built into Cursor) | Use Read/Write/Bash tools |

## Cursor Configuration

Add to `.cursor/mcp.json` (project) or Cursor Settings → MCP:

```json
{
  "mcpServers": {
    "gitlab": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-gitlab"],
      "env": {
        "GITLAB_PERSONAL_ACCESS_TOKEN": "${REALM_GITLAB_TOKEN}",
        "GITLAB_API_URL": "https://gitlab.example.com/api/v4"
      }
    },
    "teams": {
      "command": "node",
      "args": ["./mcp/teams/teams-webhook-server.js"],
      "env": {
        "REALM_TEAMS_WEBHOOK": "${REALM_TEAMS_WEBHOOK}"
      }
    }
  }
}
```

See per-server README for full setup.

## Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `REALM_GITLAB_TOKEN` | Yes | GitLab personal/project access token |
| `REALM_GITLAB_PROJECT` | Yes | Project path (e.g. `org/realm-facts`) |
| `REALM_GITLAB_API_URL` | Yes | GitLab API base URL |
| `REALM_TEAMS_WEBHOOK` | Yes* | Teams incoming webhook URL |
| `REALM_TEAMS_CHANNEL` | No | Default channel name for notifications |
| `REALM_CONFLUENCE_URL` | No | Confluence base URL |
| `REALM_CONFLUENCE_TOKEN` | No | Confluence API token |

*Webhook required unless Teams Graph MCP is configured.

## Skills Using MCPs

| Skill | GitLab MCP | Teams MCP |
|---|---|---|
| `/realm-facts submit` | create MR | review-request notification |
| `/realm-facts review` | approve, comment | approved / changes-requested |

Both follow the MCP-first → manual-fallback ladder documented in
`skills/realm-facts/references/mr-flow.md`.

## Fallback Without MCP

Skills degrade gracefully:
- GitLab: user runs `git push` + creates MR manually; paste MR URL
- Teams: `curl` webhook via `REALM_TEAMS_WEBHOOK` env var
