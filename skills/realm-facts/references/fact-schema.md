# Fact schema

Read by: `new`, `link`, `review`.

## File location

```
<facts-repo>/facts/<domain>/<id>/index.md
```

`<domain>` and `<id>` are both kebab-case (`^[a-z][a-z0-9]*(-[a-z0-9]+)*$`) and must equal the
directory names they live in — `facts.py validate` enforces this.

## Frontmatter (fixed key order)

```yaml
---
id: jwt-token-rotation
domain: platform
title: JWT Token Rotation
status: draft
owners: [@alice]
reviewers: [@bob]
tags: [auth, security]
evidence:
  - https://confluence.example.com/x/abc
related: []
depends_on: []
supersedes: null
created: 2026-08-14T00:00:00+00:00
updated: 2026-08-14T00:00:00+00:00
---
```

| Field | Type | Notes |
|---|---|---|
| `id` | str | kebab-case, equals directory name |
| `domain` | str | kebab-case, equals parent directory name |
| `title` | str | free text |
| `status` | enum | `draft` \| `review` \| `active` \| `deprecated` |
| `owners` | list | must be non-empty |
| `reviewers` | list | may be empty at `draft`; required non-empty for `--mr-ready` |
| `tags` | list | may be empty |
| `evidence` | list | URLs or repo-relative paths; may be empty at `draft`; required for `--mr-ready` |
| `related` | list | fact ids; each must resolve to an existing fact |
| `depends_on` | list | fact ids; each must resolve to an existing fact |
| `supersedes` | str \| `null` | single fact id or null |
| `created` / `updated` | ISO-8601 UTC | stamped by the script, never hand-set |

Lists render flow-style (`[a, b]`) except `evidence`, which renders as a block list when
non-empty and `evidence: []` when empty.

## Body

```markdown
## Compressed
<1-2 sentences, agent-ingestable, ≤400 chars>

## Context
<free prose — background, why this fact exists>

## Evidence
- <link or ref>
```

`## Compressed` is the only body section the script reads (for `facts-index.json` and
`FACT_BUNDLE`). `## Context` and `## Evidence` are free-form and preserved verbatim across every
script write — `link` and `set-status` only touch frontmatter, never the body.

## Validation rules (`facts.py validate`)

Always checked:
1. All 13 frontmatter keys present (a key missing means someone hand-edited the file).
2. `id` kebab-case and equal to the fact's directory name.
3. `domain` equal to the parent directory name.
4. `status` is one of the four enum values.
5. `## Compressed` present, non-empty, ≤400 chars.
6. `owners` non-empty.
7. Every `related` / `depends_on` target resolves to an existing fact id.
8. `supersedes`, if set, resolves to an existing fact id.
9. No duplicate `id` across domains.

`--mr-ready` adds:
10. `status` ∈ {`draft`, `review`} (not yet `active`/`deprecated`).
11. `evidence` non-empty.
12. `reviewers` non-empty.

Errors print one per line, `<path>:<field>: <problem>`, exit code 1 if any.

## `facts-index.json`

```json
{
  "generatedAt": "2026-08-14T00:00:00+00:00",
  "counts": { "platform": 2, "payments": 1 },
  "facts": {
    "jwt-token-rotation": {
      "path": "facts/platform/jwt-token-rotation/index.md",
      "domain": "platform",
      "status": "active",
      "title": "JWT Token Rotation",
      "tags": ["auth", "security"],
      "owners": ["@alice"],
      "compressed": "JWT 15min expiry. Refresh via silent iframe."
    }
  }
}
```

## `facts-graph.json`

```json
{
  "nodes": ["jwt-token-rotation", "session-refresh-policy"],
  "edges": [
    { "from": "jwt-token-rotation", "to": "session-refresh-policy", "type": "related" }
  ]
}
```

`type` is one of `related`, `depends_on`, `supersedes`.
