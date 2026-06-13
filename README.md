# Realm

<p align="center">
  <img src="images/realm_icon.png" alt="Realm" width="250" />
</p>

**Project-knowledge pipeline for Claude Code, Cursor, Codex, and Gemini.** Keeps architectural knowledge in structured, caveman-compressed Obsidian nodes — cheap to pull into any AI context, human-readable in Obsidian's graph view.

---

## Table of Contents

- [What is Realm?](#what-is-realm)
- [Why Realm?](#why-realm)
- [How It Works](#how-it-works)
- [Skills](#skills)
- [Installation](#installation)
- [Uninstallation](#uninstallation)
- [Quick Start](#quick-start)
- [Querying the Vault](#querying-the-vault)
- [Keeping the Vault Current](#keeping-the-vault-current)
- [Token Economics](#token-economics)
- [Vault Structure](#vault-structure)
- [Local Pipeline State](#local-pipeline-state)
- [Guards](#guards)
- [Dependencies](#dependencies)

---

## What is Realm?

Realm is an AI-coding-host skill/plugin that bridges your codebase and your Obsidian vault. It scans your project, extracts architectural knowledge — functions, classes, decisions, systems — and writes that knowledge as compressed, interlinked nodes into an Obsidian vault.

The vault becomes a persistent, human-browsable knowledge graph. When you start a new Claude session, you query the vault instead of re-reading source files. You get the same context at a fraction of the token cost.

---

## Why Realm?

Every new Claude session starts cold. Without a knowledge system, Claude re-derives architecture from source files on every session. That is expensive in tokens, slow in wall time, and imprecise — important decisions and their rationale live in your head, not in the code.

Realm solves three problems:

| Problem | Realm's Answer |
|---------|----------------|
| Context is lost between sessions | Vault persists knowledge across sessions |
| Pulling full source files is token-expensive | Compressed node headers cost 85–98% fewer tokens |
| Architecture decisions are not captured | ADR nodes store decisions, rationale, and links to implementations |

Realm is not a documentation generator. It is a token-efficient memory layer between your codebase and your AI assistant.

---

## How It Works

Realm has three layers:

### 1. Write — Obsidian nodes

Each architectural entity (function, class, decision, system) becomes one Markdown file in your vault. Every node stores two representations:

- **Compressed** — a one-liner summary (~20 tokens). Loaded by default.
- **Full** — full prose documentation. Loaded on demand.

YAML frontmatter, wikilinks, and tags are never compressed — only prose bodies.

### 2. Sync — the realm pipeline

```
/realm-forge      ← once per project: bootstrap vault dirs + local state
/realm-phase      ← scan repo → diff vs vault → stage manifest-draft.md
/realm-manifest   ← review draft → write nodes → generate backlinks → archive draft
```

No vault writes happen at phase time. You review the staged draft before anything is committed to the vault.

For incremental updates:

```
/realm-flourish   ← git diff → targeted scan → auto-commit minor changes
/realm-convey     ← compress conversation → pick topics → targeted phase
```

### 4. Plan — free-form ideation canvas

Think, research, design, and plan inside a persistent canvas. No manual MD files. Pre-loads vault context before spawning agents. Saves across sessions. Finalizes to vault when ready.

```bash
# Single section
/realm-plan plan "refactor auth to JWT"          # planner → decisions/ + sessions/
/realm-plan design "API versioning strategy"     # architect → decisions/ + architecture.md
/realm-plan scaffold "NotificationService"       # code-architect → classes/ + systems/ stubs
/realm-plan investigate "caching bug"            # cavecrew-investigator → discoveries/
/realm-plan deep-research "event sourcing"       # firecrawl+exa → discoveries/ + learning/

# Chain — generation order hint, not a hard pipeline
/realm-plan deep-research->design->plan "auth refactor"
/realm-plan investigate->plan "caching bug"
/realm-plan scaffold->design->plan "PaymentService"

# Session management
/realm-plan list                                 # all in-progress work, grouped by category
/realm-plan resume plans/auth-refactor           # continue saved canvas
```

Work items persist in vault under `work/` — categorized by intent (`plans/`, `designs/`, `research/`, `scaffolds/`). Resumable across sessions. One free-form collaboration loop; no forced stage gates.

### 3. Query — realm-recall

Pull node content into Claude's context surgically:

```bash
/realm-recall validateUser            # ~20 tokens
/realm-recall validateUser --with-deps  # ~80 tokens
/realm-recall @auth                   # all auth nodes, ~200 tokens
/realm-recall "why JWT"               # semantic → decision nodes
/realm-recall auth --trace            # link tree only (<10 tokens)
```

See [VISUALS.md](VISUALS.md) for pipeline flow diagrams.

---

## Skills

| Skill | Purpose |
|-------|---------|
| `/realm-forge` | Bootstrap vault directory structure and local state. Run once per project. |
| `/realm-phase` | Scan repo with `cavecrew-investigator`, diff against vault, stage `manifest-draft.md`. No vault writes. |
| `/realm-manifest` | Write staged draft to vault, generate backlinks, archive draft, update doc registry. |
| `/realm-flourish` | Git-diff-based incremental update. Auto-commits minor changes; falls back to staged mode for structural decisions. |
| `/realm-convey` | Compress the current conversation, extract topics (functions, classes, decisions, discoveries), route to targeted phase. |
| `/realm-recall` | Query vault by tag, function name, class name, or semantic phrase. Returns compressed context. |
| `/realm-fathom` | Deep investigation: live code + vault in parallel. Returns consolidated what (code) + why (vault). Flags drift. Zero writes. |
| `/realm-plan` | Free-form ideation canvas. Optional chain syntax defines generation order (not a hard pipeline). Categorized `work/` persistence (`plans/`, `designs/`, `research/`, `scaffolds/`). Resume across sessions. Finalizes sections to proper vault nodes. |
| `/realm-status` | Read-only health check. Lists node counts, stale docs, pipeline state. |

---

## Installation

See [REQUIREMENTS.md](REQUIREMENTS.md) for prerequisites.

### Cursor, Codex, and Gemini

```bash
# One-liners
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent codex
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent cursor
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent gemini

# Direct installs
npx skills add blackmo18/realm -a codex
npx skills add blackmo18/realm -a cursor
npx skills add blackmo18/realm -a gemini
```

After install, restart your host or open a new session so the new skills are loaded, then run:

```bash
/realm-forge
```

### Claude Code

```bash
# 1. Install caveman plugin (required dependency)
/plugin marketplace add ~/.claude/plugins/marketplaces/caveman

# 2. Copy Realm into the Claude plugin marketplace path from a local clone
node bin/install.js --agent claude --force

# 3. Install realm
/plugin marketplace add ~/.claude/plugins/marketplaces/realm
```

Full step-by-step guide: [INSTALL.md](INSTALL.md)

---

## Uninstallation

To remove Realm and its dependencies:

```bash
# Skills CLI installs (Cursor, Codex, Gemini)
npx skills remove realm
```

For Claude Code installs:

```bash
# Automated uninstall (recommended)
./uninstall.sh

# Or manually remove plugins
rm -rf ~/.claude/plugins/marketplaces/realm
rm -rf ~/.claude/plugins/marketplaces/caveman
```

Full uninstall guide: [UNINSTALL.md](UNINSTALL.md)

Notes:
- Local project state (`.realm/`) can be removed separately
- Obsidian vault nodes are preserved unless manually deleted
- Start a new host session after uninstall so removed skills are not cached

---

## Quick Start

```bash
# Bootstrap the vault for your project
/realm-forge

# Scan the codebase and stage a doc plan (no vault writes yet)
/realm-phase

# Review .realm/manifest-draft.md, then write to vault
/realm-manifest

# Open Obsidian — your knowledge graph is ready
```

After that, query anytime:

```bash
/realm-recall auth
/realm-status
```

---

## Querying the Vault

### Deep investigation (code + vault)

```bash
/realm-fathom function:validateUser       # signature, flow, callers + vault why + drift check
/realm-fathom class:AuthService           # class responsibility, methods, deps + vault context
/realm-fathom system:PaymentPipeline      # subsystem boundary, API surface + vault ADRs
/realm-fathom "how does auth flow work"   # freeform → relevant files/functions mapped end-to-end
```

Use `realm-fathom` before modifying unfamiliar code. Live code is ground truth; vault adds architectural context. Conflicts are flagged as `VAULT DRIFT` — never silently blended.

### By entity (vault only)

```bash
/realm-recall validateUser            # function node (compressed, ~20 tokens)
/realm-recall validateUser --with-deps  # function + dependency nodes (~80 tokens)
/realm-recall AuthService             # class node
/realm-recall "why JWT"               # semantic search → decision nodes
```

### By tag

```bash
/realm-recall @auth                   # all #auth nodes (~200 tokens for 10 nodes)
/realm-recall @auth --trace           # link tree only (<10 tokens) — explore in Obsidian
/realm-recall @auth --count           # estimate tokens before pulling
```

### By dependency

```bash
/realm-recall validateUser --with-dependents  # everything that calls validateUser
/realm-recall decision:auth-flow --with-implementations  # decision + implementing nodes
```

### Targeted phase (skips full scan)

```bash
/realm-phase function:validateUser        # ~10–20× cheaper than full scan
/realm-phase class:AuthService
/realm-phase function:validateUser class:TokenCodec   # multi-target
```

---

## Keeping the Vault Current

| Trigger | Command | Cost |
|---------|---------|------|
| Small code change | `/realm-flourish` | ~500–2K tokens |
| Specific entity changed | `/realm-phase function:X` | ~1–4K tokens |
| Conversation with new discoveries | `/realm-convey` | ~2–4K tokens |
| After a major milestone | `/realm-phase` (full) | ~15–80K tokens |

**Default flow:** `realm-convey` or `realm-flourish` for 95% of updates. Full phase reserved for post-milestone sync.

### Optional: session-end reminder hook

Add to `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "command": "echo 'Session ended. Run /realm-convey to capture discoveries or /realm-flourish to sync code changes.'",
        "description": "Remind to sync realm vault"
      }
    ]
  }
}
```

---

## Token Economics

### Query savings vs pulling full source files

| Query | Without Realm | With Realm | Savings |
|-------|--------------|------------|---------|
| Single function + deps | 500–800 tokens | ~80 tokens | 90% |
| Auth cluster (10 nodes) | 3–4K tokens | ~200 tokens | 95% |
| Architecture orientation | 5–10K tokens | ~500 tokens | 90–95% |
| "Why was X decided?" | 1K tokens | ~20 tokens | 98% |
| Dependency tree | 500 tokens | <10 tokens | 99% |

### Initial mapping cost (one-time)

| Project Size | Files | Phase Cost |
|---|---|---|
| Small (<5K LOC) | ~50 files | ~5–8K tokens |
| Medium (5–50K LOC) | ~200–500 files | ~15–25K tokens |
| Large (50K+ LOC) | ~1000+ files | ~40–80K tokens |

### Break-even

A medium project maps for ~20K tokens. An average session saves ~2K tokens (3–4 queries). Break-even: **10 sessions**. Large projects with deep queries: 5–7 sessions.

---

## Vault Structure

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
└── work/                      # in-progress realm-plan canvases
    ├── index.md               # auto-maintained master list
    ├── plans/                 # building something
    ├── designs/               # deciding / architecting
    ├── research/              # learning / investigating
    └── scaffolds/             # blueprinting modules / services
```

**Node types:**

| Type | Directory | Typical content |
|------|-----------|----------------|
| `decision` | `decisions/` | ADR: context, decision, consequences, implementations |
| `function` | `functions/` | Signature, compressed one-liner, depends_on, called_by |
| `class` | `classes/` | Responsibility, methods, dependencies, dependents |
| `system` | `systems/` | Service boundary, API surface, events, external deps |
| `discovery` | `discoveries/` | Findings, perf data, bug post-mortems |
| session log | `sessions/` | What changed, decided, discovered per session |
| work canvas | `work/<category>/` | In-progress ideation — promoted to real nodes on `finalize` |

Each node stores two representations in the same file:

```markdown
---
id: validateUser
type: function
tags: [auth, critical-path]
---

# validateUser()

Compressed: Validates JWT. Decodes → verifies → checks expiry. Cache: 99%. <1ms p95.

## Full

[Full prose documentation, examples, edge cases, benchmarks...]
```

Default recall loads the `Compressed` section only. Pass `--expand` to load full prose.

---

## Local Pipeline State

```
<project-root>/.realm/
├── realm-state.json        # doc registry + pipeline state
├── manifest-draft.md       # staged draft (phase → manifest)
└── archive/
    └── <timestamp>-draft.md  # past drafts after each manifest run
```

`.realm/` is added to `.gitignore` by `realm-forge`. It is local state, not repo state.

`realm-state.json` tracks:
- Vault path and project slug
- Phase and manifest timestamps
- Per-doc status: `committed | planned | stale`

---

## Guards

| Condition | Blocked skill | Message | Fix |
|-----------|--------------|---------|-----|
| `.realm/realm-state.json` missing | `realm-phase`, `realm-convey` | `No realm state found. Run /realm-forge first.` | `/realm-forge` |
| `phase.draftReady != true` | `realm-manifest` | `No staged draft. Run /realm-phase first.` | `/realm-phase` |
| `manifest-draft.md` missing | `realm-manifest` | `Draft file missing. Run /realm-phase to regenerate.` | `/realm-phase` |
| Staged draft pending | `realm-flourish` | `Staged draft exists. Run /realm-manifest first.` | `/realm-manifest` or delete draft |
| No vault nodes | `realm-recall` | `No nodes in vault yet.` | `/realm-phase` then `/realm-manifest` |

---

## Dependencies

### Required

| Dependency | Purpose |
|---|---|
| Supported host: Claude Code, Cursor, Codex, or Gemini | Runtime for Realm skills |
| Node.js with `npx` | Installs Realm for Cursor, Codex, and Gemini |
| [Obsidian](https://obsidian.md) 1.x+ | Vault storage, graph view, backlinks, tag pane |
| Git (any recent version) | Used by `realm-flourish` for diff-based incremental updates |

### Plugin dependencies

Realm depends on two skills from the **caveman** plugin:

| Skill | Used by | Purpose |
|-------|---------|---------|
| `cavecrew-investigator` agent | `realm-phase`, `realm-flourish`, `realm-fathom` | Scans repo; outputs caveman-compressed findings |
| `caveman-compress` skill | `realm-phase`, `realm-manifest` | Compresses node body prose before vault writes |

Install caveman first for Claude Code:

```bash
/plugin marketplace add ~/.claude/plugins/marketplaces/caveman
```

### Optional Obsidian plugins

Enhance graph exploration — not required for realm to function:

| Plugin | Purpose |
|---|---|
| Dataview | Query nodes by tag, type, or date |
| Graph Analysis | Enhanced backlink traversal |
| Templater | Use vault templates created by realm-forge |

---

**Diagrams:** [VISUALS.md](VISUALS.md) — pipeline flows, vault graph, guards, handoff state
