# Realm Vault Taxonomy

## Directory Structure

```
<vault>/projects/<slug>/
├── overview.md
├── architecture.md
├── decisions/
│   ├── ADR-000-index.md
│   └── <id>.md
├── functions/
│   └── <id>.md
├── classes/
│   └── <id>.md
├── systems/
│   └── <id>.md
├── discoveries/
│   └── YYYY-MM-DD-<topic>.md
├── sessions/
│   └── YYYY-MM-DD-<topic>.md
├── learning/
└── work/
    ├── index.md
    ├── plans/
    ├── designs/
    ├── research/
    └── scaffolds/
        └── <slug>/
            ├── _meta.md
            └── <section>.md
<vault>/_templates/
├── Decision-Node.md
├── Function-Node.md
├── Class-Node.md
├── Discovery-Note.md
└── Session-Log.md
```

Slug = project dir name, kebab-case. Derive from `package.json` `name` or repo root folder.

## Node Types

| Type | Dir | Content |
|------|-----|---------|
| `decision` | `decisions/` | ADR: context, decision, consequences, implementations |
| `function` | `functions/` | Signature, compressed one-liner, depends_on, called_by |
| `class` | `classes/` | Responsibility, methods list, dependencies, dependents |
| `system` | `systems/` | Service boundary, API surface, events, external deps |
| `discovery` | `discoveries/` | Findings, perf data, bug post-mortems |
| session log | `sessions/` | What changed, decided, discovered per session |
| work canvas | `work/` | In-progress realm-plan canvases; promoted on finalize |

## Node Templates

**Decision-Node.md** frontmatter: `id`, `title`, `type: decision`, `status`, `created`, `updated`, `tags`, optional `source_plan`.
Body sections: `## Context`, `## Decision`, `## Rejected alternatives`, `## Consequences`, `## Compressed`.

**Function-Node.md** frontmatter: `id`, `type: function`, `class`, `depends_on`, `called_by`, `tags`.
Body: `## Compressed` (one-liner), `## Full` (signature + flow).

**Class-Node.md** frontmatter: `id`, `type: class`, `dependencies`, `tags`.
Body: `## Compressed`, `## Methods`, `## Dependents`.

**Discovery-Note.md** frontmatter: `id`, `type: discovery`, `date`, `tags`.
Body: `## Finding`, `## Impact`, `## Compressed`.

**Session-Log.md** frontmatter: `tags: [session]`, `date`, `project`.
Body: `## Discovered`, `## Decided`, `## Changed`, `## Next`.

## ADR Index Maintenance

`decisions/ADR-000-index.md` is a Markdown table. realm-manifest must:
1. Read existing index
2. Append rows for new ADRs in order
3. Never remove existing rows
4. Format: `| [[ADR-NNN-slug]] | Title | status | date |`

## Decision Node — source_plan Field

```yaml
source_plan: work/plans/auth-refactor
```

Set by `realm-plan finalize` when promoting a design section to a decision node. Omit for convey/phase decisions.

## Wikilink Convention

Use `[[filename-without-extension]]` within same project dir.
Use `[[projects/slug/filename]]` for cross-project links (rare).
Every new doc: at least one wikilink to `[[overview]]` or a decision.

## Doc Detection (forge idempotency)

Scan `<projectDir>/` on init. Each `.md` found: `status: "committed"`, `updated: <file mtime>`. Never overwrite existing files.
