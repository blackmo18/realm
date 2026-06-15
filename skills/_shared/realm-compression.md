# Caveman Compression Policy

Apply to doc **bodies** only. Never compress:
- YAML frontmatter (between `---` delimiters)
- Fenced code blocks
- URLs and file paths
- Table structure (keep columns, compress cell prose)
- `[[wikilinks]]` and `#tags`

Compress:
- Section prose: drop articles (a/an/the), filler words (basically/really/just)
- Prefer fragments over full sentences in bullet lists
- Prefer short synonyms (use not utilize, build not implement)
- Keep technical terms exact; never abbreviate service/event/table names

ADR **Context** and **Decision** sections: compress filler but keep the full causal chain. Must be readable months later by someone who wasn't there.

## manifest-draft.md Format

```markdown
# Realm Manifest Draft — YYYY-MM-DD

## Meta
slug: <projectSlug>
phase-run: <ISO>
mode: full | targeted
gap-summary: <1-line: N new functions, M new classes, K decisions, L updates>

## Planned Node Documents

### <relative path from projectDir>
status: new | update
links: [[ADR-000-index]], [[overview]]
---
<full YAML frontmatter + Compressed section + Full section>

### <next node>
...

## Updated Overview/Architecture
### overview.md
status: update
---
[milestone/stack patches only; preserve existing prose]

### architecture.md
status: update
---
[new service/event rows only; don't rewrite existing]

## Session Log Entry
### sessions/YYYY-MM-DD-<topic>.md
status: new
---
<session log with ## Discovered / ## Decided / ## Changed / ## Next>
```

realm-manifest reads each `### <path>` section, extracts body, writes to vault. Sections are self-contained.
