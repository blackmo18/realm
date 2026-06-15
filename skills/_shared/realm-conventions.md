# Realm Shared Conventions

> **Load-on-demand fragments available** — prefer these over reading this full file:
> - `realm-schema.md` — state.json schema, pendingDrafts, nodeIndex, docs, staging layout, ordering guards
> - `realm-taxonomy.md` — vault dirs, node types, templates, ADR index, wikilinks, doc detection
> - `realm-compression.md` — caveman compression policy, manifest-draft.md format
>
> Read only the fragment your skill needs. Read this master file only when all sections are required.

All realm skills read the relevant fragment. Conventions here override nothing outside realm; they define how realm skills behave internally.

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
├── learning/            # optional standalone concept notes
└── work/                # in-progress realm-plan canvases (never directly vaulted)
    ├── index.md         # auto-maintained master list, grouped by category
    ├── plans/           # building something — terminal mode: plan
    ├── designs/         # deciding/architecting something — terminal mode: design
    ├── research/        # learning/investigating — terminal mode: research or investigate
    └── scaffolds/       # blueprinting a module/service — terminal mode: scaffold
        └── <slug>/
            ├── _meta.md     # category, chain, status, section registry
            └── <section>.md # one file per section (research, design, plan, scaffold)
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
| work canvas | `work/` | In-progress realm-plan canvases; promoted to real nodes on `finalize` |

---

## realm-state.json Schema

Location: `<project-root>/.realm/realm-state.json`

```json
{
  "vaultPath": "<absolute path to Obsidian vault root>",
  "projectSlug": "<kebab-case slug>",
  "projectDir": "<vaultPath>/projects/<projectSlug>",
  "manifest": {
    "lastRun": "<ISO 8601 or null>"
  },
  "pendingDrafts": [
    {
      "source": "plan | convey",
      "slug": "<category>/<slug> | null",
      "path": "<path to manifest-draft.md relative to projectRoot>",
      "created": "<ISO 8601>"
    }
  ],
  "docs": {
    "<relative-to-projectDir path>": {
      "status": "committed | planned | stale",
      "updated": "<ISO 8601 or null>"
    }
  }
}
```

**pendingDrafts entries:**
- `source: plan` — produced by `realm-plan finalize`. `slug` = `work/<category>/<slug>`. `path` = `work/<category>/<slug>/manifest-draft.md` (relative to projectRoot, inside vault).
- `source: convey` — produced by `realm-convey`. `slug` = null. `path` = `.realm/manifest-draft.md`.
- Removed when `realm-manifest` commits that entry.

**docs status meanings:**
- `committed` — file exists in vault, written by realm-manifest (or detected as pre-existing on init).
- `planned` — doc staged in a pending draft; not yet in vault.
- `stale` — committed doc exists but codebase has diverged enough to warrant an update.

---

## Staging Dir Layout

```
<project-root>/.realm/
├── realm-state.json
├── manifest-draft.md        # written by realm-convey only
└── archive/
    └── <slug>-<timestamp>-draft.md   # archived after each manifest run

<vault>/projects/<slug>/work/<category>/<slug>/
├── _meta.md
├── <section>.md             # canvas section files
└── manifest-draft.md        # written by realm-plan finalize (local to canvas)
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

**realm-manifest** checks at startup:
```
if .realm/realm-state.json does not exist:
  STOP → print: "No realm state. Run /realm-forge first."
if realm-state.json.pendingDrafts is empty (or missing):
  STOP → print: "No pending drafts. Run /realm-plan finalize or /realm-convey."
if selected draft file does not exist:
  STOP → print: "Draft file missing: <path>. Stage again with /realm-plan finalize."
```

**realm-plan** checks at startup (Step 0):
```
if .realm/realm-state.json does not exist:
  STOP → print: "No realm state. Run /realm-forge first."
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

## Decision Node — source_plan Field

Decision nodes promoted from `realm-plan` carry a `source_plan` frontmatter field:

```yaml
source_plan: work/plans/auth-refactor   # relative to projectDir; omit if not from realm-plan
```

Rules:
- Set by realm-plan Step 5 (finalize) when promoting a `design` section to a decision node.
- Omit for decisions captured directly via realm-convey or realm-phase (no planning canvas).
- realm-recall can filter/surface by `source_plan` to trace a decision back to its planning context.
- The ADR body includes `## Origin` with a wikilink to the plan canvas `_meta.md`.

Corresponding `_meta.md` update (written by realm-plan finalize before producing manifest-draft):

```yaml
promoted_to:
  - decisions/<adr-id>.md
```

---

## Wikilink Convention

Use `[[filename-without-extension]]` for cross-links within the same project dir.
Use `[[projects/slug/filename]]` for cross-project links (rare).
Every new doc should contain at least one wikilink to `[[overview]]` or a decision.
Decision nodes promoted from realm-plan include `[[work/<category>/<slug>/_meta|<topic>]]` in `## Origin`.
