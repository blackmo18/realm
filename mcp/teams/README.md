# Microsoft Teams MCP for Realm Facts

Teams integration for organization channel notifications: new fact reviews, approvals, change requests.

## Setup Options

### Option A — Incoming Webhook (Recommended, simplest)

1. Teams → Channel → Connectors → Incoming Webhook
2. Create webhook, copy URL
3. Set `REALM_TEAMS_WEBHOOK=<url>`

`/realm-facts submit` and `/realm-facts review` call this directly — either the `post_message`
MCP tool below, or a `curl` fallback when the MCP server isn't configured.

#### Cursor MCP config (webhook server)

```json
{
  "mcpServers": {
    "teams": {
      "command": "node",
      "args": ["mcp/teams/teams-webhook-server.js"],
      "env": {
        "REALM_TEAMS_WEBHOOK": "<webhook-url>"
      }
    }
  }
}
```

### Option B — Microsoft Graph API

For richer integration (channel picker, @mentions):

1. Register Azure AD app
2. Grant `ChannelMessage.Send` permission
3. Use Graph MCP or custom server

Env vars:
```bash
export AZURE_TENANT_ID="<tenant>"
export AZURE_CLIENT_ID="<client>"
export AZURE_CLIENT_SECRET="<secret>"
export REALM_TEAMS_TEAM_ID="<team-id>"
export REALM_TEAMS_CHANNEL_ID="<channel-id>"
```

## Notification Types

| Mode | Trigger | Channel message |
|---|---|---|
| `review-request` | `/realm-facts submit` | New fact needs review + MR link |
| `approved` | `/realm-facts review --approve` | Fact merged, team should sync |
| `changes-requested` | `/realm-facts review --request-changes` | Author notified with reason |
| `weekly-digest` | scheduled (not yet implemented) | Summary of new/updated facts |

## Message Format

Teams Adaptive Card (via webhook):

```json
{
  "@type": "MessageCard",
  "@context": "http://schema.org/extensions",
  "themeColor": "0076D7",
  "summary": "Realm Fact Review",
  "sections": [{
    "activityTitle": "New fact review: JWT Token Rotation",
    "facts": [
      {"name": "Author", "value": "@alice"},
      {"name": "Reviewers", "value": "@bob"},
      {"name": "MR", "value": "[View MR](https://gitlab.../merge_requests/42)"}
    ],
    "text": "JWT rotation every 15min. Refresh via silent iframe."
  }]
}
```

## Environment Variables

| Variable | Purpose |
|---|---|
| `REALM_TEAMS_WEBHOOK` | Incoming webhook URL |
| `REALM_TEAMS_CHANNEL` | Human-readable channel name (for logs) |

## Fallback Without MCP

`/realm-facts submit` and `/realm-facts review` run:

```bash
curl -X POST "$REALM_TEAMS_WEBHOOK" -H "Content-Type: application/json" -d '<message-card-json>'
```

Works without MCP server if webhook env is set.
