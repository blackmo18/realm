# Confluence MCP (Optional)

Optional integration for verifying Confluence references in facts.

## Purpose

- Resolve Confluence URLs in `evidence` frontmatter
- Fetch page title and last-modified date
- Flag stale or broken Confluence links during `/realm-facts review`

## Setup

Use Atlassian MCP or REST API wrapper:

```json
{
  "mcpServers": {
    "confluence": {
      "command": "npx",
      "args": ["-y", "@atlassian/mcp-server-confluence"],
      "env": {
        "CONFLUENCE_URL": "https://company.atlassian.net/wiki",
        "CONFLUENCE_TOKEN": "<api-token>",
        "CONFLUENCE_EMAIL": "<user@company.com>"
      }
    }
  }
}
```

Or set Realm env vars:

```bash
export REALM_CONFLUENCE_URL="https://company.atlassian.net/wiki"
export REALM_CONFLUENCE_TOKEN="<token>"
export REALM_CONFLUENCE_EMAIL="<email>"
```

## Usage in Review

`/realm-facts review` optionally calls Confluence MCP:

```
for each source_url matching confluence:
  fetch page title + lastModified
  warn if 404 or >90 days stale
```

## Without MCP

Reviewer manually checks Confluence links. Validation script warns on malformed URLs only.
