# Realm Shared Conventions

All realm skills read this file. Conventions here override nothing outside realm; they define how realm skills behave internally.

---

## Vault Taxonomy

Every project gets one directory under `<vault>/projects/<slug>/`:

```
<vault>/projects/<slug>/
├── overview.md          # status, stack, milestone tracker, key file links
├── architecture.md      # service map, event shapes, data flow, schema groups
├── decisions/
│   ├── ADR-000-index.md # table of all ADRs
│   └── <id>.md          # one file per decision
├── functions/
│   └── <id>.md          # one file per notable function/method
├── classes/
│   └── <id>.md          # one file per service/class
├── systems/
│   └── <id>.md          # one file per subsystem or integration
├── discoveries/
│   └── YYYY-MM-DD-<topic>.md  # ephemeral findings, perf notes, bug discoveries
├── sessions/
│   └── YYYY-MM-DD-<topic>.md  # per-session discovery log
└── learning/            # optional standalone concept notes
<vault>/_templates/
├── Decision-Node.md
├── Function-Node.md
├── Class-Node.md
├── Discovery-Note.md
└── Session-Log.md
```

Slug = project directory name (e.g. `poly-bot-v2`). Derive from `package.json` `name` field or repo root folder name; kebab-case.

**Node types and their dirs:**

| Type | Dir | Typical content |
|------|-----|----------------|
| `decision` | `decisions/` | ADR: context, decision, consequences, implementations |
| `function` | `functions/` | Signature, compressed one-liner, depends_on, called_by |
| `class` | `classes/` | Responsibility, methods list, dependencies, dependents |
| `system` | `systems/` | Service boundary, API surface, events, external deps |
| `discovery` | `discoveries/` | Findings, perf data, bug post-mortems |
| session log | `sessions/` | What changed, decided, discovered per session |

---

## realm-state.json Schema

Location: `<project-root>/.realm/realm-state.json`

```json
{
  "vaultPath": "<absolute path to Obsidian vault root>",
  "projectSlug": "<kebab-case slug>",
  "projectDir": "<vaultPath>/projects/<projectSlug>",
  "phase": {
    "lastRun": "<ISO 8601 or null>",
    "draftReady": false
  },
  "manifest": {
    "lastRun": "<ISO 8601 or null>"
  },
  "docs": {
    "<relative-to-projectDir path>": {
      "status": "committed | planned | stale",
      "updated": "<ISO 8601 or null>"
    }
  }
}
```

**Status meanings:**
- `committed` — file exists in vault, written by realm-manifest (or detected as pre-existing on init).
- `planned` — realm-phase identified this doc as needed; draft content is in `manifest-draft.md`; not yet in vault.
- `stale` — committed doc exists but realm-phase detected the repo has diverged enough to warrant an update. Manifest will overwrite.

---

## Staging Dir Layout

```
<project-root>/.realm/
├── realm-state.json
├── manifest-draft.md        # written by realm-phase, consumed by realm-manifest
└── archive/
    └── <timestamp>-draft.md # archived copies after each manifest run
```

`.realm/` MUST be in `.gitignore`. realm-forge ensures this.

---

## manifest-draft.md Format

```markdown
# Realm Manifest Draft — YYYY-MM-DD

## Meta
slug: <projectSlug>
phase-run: <ISO>
mode: full | targeted    ← "full" = whole-repo scan, "targeted" = specific entities
gap-summary: <1-line: N new functions, M new classes, K new decisions, L updates>

## Planned Node Documents

### <relative path from projectDir>      (e.g. functions/validateUser.md)
status: new | update
links: [[ADR-000-index]], [[overview]]   (optional cross-refs)
---
<full YAML frontmatter block + Compressed section + Full section>

### <next node>
...

## Updated Overview/Architecture          (only if diverged)
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

---

## Caveman Compression Policy

Apply to doc **bodies** only. Never compress:
- YAML frontmatter (between `---` delimiters)
- Fenced code blocks (` ``` ` blocks)
- URLs and file paths
- Table structure (keep columns, compress cell prose)
- `[[wikilinks]]` and `#tags`

Compress:
- Section prose: drop articles (a/an/the), filler words (basically/really/just), pleasantries
- Prefer fragments over full sentences for bullet lists
- Prefer short synonyms (use → use, implement → build, utilize → use)
- Keep technical terms exact; never abbreviate service/event/table names

ADR **Context** and **Decision** sections: compress filler but keep the full causal chain. These must be readable months later by a human who wasn't there.

---

## Ordering Guards

**realm-phase** checks at startup:
```
if .realm/realm-state.json does not exist:
  STOP → print: "No realm state found. Run /realm-forge first."
```

**realm-manifest** checks at startup:
```
if .realm/realm-state.json does not exist:
  STOP → print: "No realm state. Run /realm-forge then /realm-phase."
if realm-state.json.phase.draftReady != true:
  STOP → print: "No staged draft. Run /realm-phase first."
if .realm/manifest-draft.md does not exist:
  STOP → print: "Draft file missing. Run /realm-phase to regenerate."
```

---

## Doc Detection (for realm-forge idempotency)

When realm-forge runs on a project that already has vault docs, scan `<projectDir>/`:
- For each file found: add to `docs` registry with `status: "committed"`, `updated: <file mtime or now>`
- For `_templates/`: check vault root `_templates/`; mark `committed` if present
- Never overwrite existing files; only create missing ones

---

## ADR Index Maintenance

`decisions/ADR-000-index.md` is a Markdown table. realm-manifest must:
1. Read existing index (if any)
2. Append rows for new ADRs in order
3. Never remove existing rows
4. Format: `| [[ADR-NNN-slug]] | Title | status | date |`

---

## Wikilink Convention

Use `[[filename-without-extension]]` for cross-links within the same project dir.
Use `[[projects/slug/filename]]` for cross-project links (rare).
Every new doc should contain at least one wikilink to `[[overview]]` or a decision.
