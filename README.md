# Realm

<p align="center">
  <img src="images/realm_icon.png" alt="Realm" width="250" />
</p>

**Decision capture & knowledge pipeline for Claude Code, Cursor, Codex, and Gemini.** Persists the WHY behind your code — decisions made, alternatives rejected, constraints imposed — as interlinked ADR nodes in an Obsidian vault.

---

## Table of Contents

- [What is Realm?](#what-is-realm)
- [Why Realm?](#why-realm)
- [How It Works](#how-it-works)
- [Skills](#skills)
- [Installation](#installation)
- [Claude Plugin Publication](#claude-plugin-publication)
- [Uninstallation](#uninstallation)
- [Quick Start](#quick-start)
- [Querying the Vault](#querying-the-vault)
- [Token Economics](#token-economics)
- [Vault Structure](#vault-structure)
- [Dependencies](#dependencies)

---

## What is Realm?

Realm is an AI-coding-host skill/plugin system that captures architectural decisions as you make them — the choices, the alternatives you rejected, and the constraints those decisions impose — and stores them as compressed, interlinked ADR nodes in an Obsidian vault.

Every new AI session starts cold. Code tells AI *what* exists. Realm tells AI *why* it exists that way, what was tried and discarded, and what must not change.

---

## Why Realm?

Code captures the surviving solution. It does not capture the graveyard of rejected alternatives, the constraint that forced an unusual pattern, or the incident that made you write "DO NOT change this order."

Without a decision record, AI assistants re-derive or re-propose settled questions every session. You answer the same "why not Redis pub/sub?" question repeatedly. A rejected approach gets proposed again in session 12.

| Problem | Realm's Answer |
|---------|----------------|
| AI starts cold every session | Vault persists decisions across sessions |
| Code doesn't explain WHY | ADR nodes store rationale + rejected alternatives |
| Rejected approaches get re-proposed | `realm-recall "tried X"` surfaces prior art instantly |
| Constraints are invisible in code | Consequences field captures what must not change |
| Oversized god files accumulate tech debt | `realm-concise` triages and queues refactors deterministically |
| Architectural changes lack structure | `realm-planning` provides two-phase execution blueprints |

---

## How It Works

```
/realm-forge     ← Bootstrap vault directory structure and project state (once per repo)
/realm-fathom    ← Investigate code + vault rationale in parallel before changing code
/realm-recall    ← Instant decision queries (~20 tokens/node)
/realm-planning  ← Two-phase planning (P1: High-level + ADR direction; P2: Impl blueprint)
/realm-concise   ← God-file concierge triage queue (scripts/concise.py + committed ledger)
/realm-status    ← Read-only vault & pipeline health check
```

### 1. Bootstrap — realm-forge

Run `/realm-forge` once per project to link an Obsidian vault, create directory conventions, and seed pipeline state.

### 2. Investigate — realm-fathom

Before touching unfamiliar code:

```bash
/realm-fathom function:validateUser   # live code (ground truth) + vault WHY
/realm-fathom "how does auth flow"    # end-to-end + ADR context
```

Live code is always ground truth. Vault adds the architectural intent. Conflicts flagged as `VAULT DRIFT`.

### 3. Query — realm-recall

```bash
/realm-recall "why JWT"               # ~20 tokens
/realm-recall "what was rejected for auth"   # surfaces rejected_alternatives
/realm-recall "constraint on payments"       # consequences field
/realm-recall decisions               # all ADR nodes, compressed
```

### 4. Planning — realm-planning

Two-phase planning skill operating inside native plan mode:
- **Phase 1**: High-level architectural analysis and ADR direction.
- **Phase 2**: Code-level implementation blueprint for coding agents.

```bash
/realm-planning "refactor auth to JWT"
/realm-planning "distributed caching" --phase2
```

### 5. God-File Triage — realm-concise

Deterministic crawler (`scripts/concise.py`) finds oversized files, scores blast radius, maintains persistent queue in `.realm/concise-state.json`, and updates committed `docs/GOD_FILES.md` ledger.

```bash
/realm-concise                        # scan & print top god files
/realm-concise recommend <file>       # single-file refactor recommendation
/realm-concise plan <file>            # delegate approved candidate to /realm-planning
```

---

## Skills

| Skill | Purpose |
|-------|---------|
| `/realm-forge` | Bootstrap vault directory structure and local state. Run once per project. |
| `/realm-fathom` | Deep investigation: live code + vault in parallel. Returns what (code) + why (vault). Flags drift. Zero writes. |
| `/realm-recall` | Query vault by decision keyword, tag, or semantic phrase. Optimized for ADR queries: "why X", "rejected for Y", "constraint on Z". |
| `/realm-planning` | Two-phase architecture and implementation plan. Phase 1: High-level + ADR direction; Phase 2: Code blueprint. |
| `/realm-concise` | God-file triage concierge. Deterministic LOC/blast-radius scoring, persistent refactor queue, committed `docs/GOD_FILES.md` ledger. |
| `/realm-status` | Read-only health check. Lists node counts, stale docs, pipeline state. |

### Team-Wide Facts (Organization)

Central GitLab `realm-facts` repo for organization knowledge. GitLab MR review + Microsoft Teams notifications.

One routed skill, `/realm-facts`, with 8 subcommands:

| Subcommand | Purpose |
|-------|---------|
| `/realm-facts forge` | Connect product repo to central facts repo |
| `/realm-facts new` | Create a new team fact |
| `/realm-facts link` | Link facts (related, depends_on, supersedes) |
| `/realm-facts submit` | Submit for GitLab MR review + Teams notification |
| `/realm-facts review` | Reviewer approve or request changes |
| `/realm-facts sync` | Pull latest approved facts |
| `/realm-facts recall` | Query facts (compressed by default) |
| `/realm-facts ingest` | Bundle facts for other agents |

See [docs/realm-facts-workflow.md](docs/realm-facts-workflow.md) for full team workflow.

---

## Installation

See [REQUIREMENTS.md](REQUIREMENTS.md) for prerequisites.

### Codex, Cursor, and Gemini

```bash
# Recommended installer
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent codex
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent cursor
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent gemini

# Skills-only direct installs
npx skills add blackmo18/realm -a codex
npx skills add blackmo18/realm -a cursor
npx skills add blackmo18/realm -a gemini
```

From a local clone:

```bash
# Global install
node bin/install.js --agent codex
node bin/install.js --agent gemini

# Local project-only install (does not touch ~)
./install.sh --agent gemini --local
./install.sh --agent codex --local
```


### Claude Code

```bash
# 1. Install caveman plugin (required dependency)
/plugin marketplace add ~/.claude/plugins/marketplaces/caveman

# 2. Copy Realm into the Claude plugin marketplace path from a local clone
node bin/install.js --agent claude --force

# 3. Install realm inside Claude Code
/plugin marketplace add ~/.claude/plugins/marketplaces/realm
```

Full step-by-step guide: [INSTALL.md](INSTALL.md)

---

## Claude Plugin Publication

To publish or update Realm on the Claude Code marketplace:

1. **Verify Plugin Manifests**:
   - `.claude-plugin/plugin.json` — contains plugin name, version, description, and author.
   - `.claude-plugin/marketplace.json` — contains plugin entry, category, and source repository pointer (`https://github.com/blackmo18/realm.git`).

2. **Update Release Version & Git Commit SHA**:
   - Bump version in `.claude-plugin/plugin.json` (e.g., `"version": "0.1.6"`).
   - Get current git commit SHA: `git rev-parse HEAD`.
   - Update `sha` in `.claude-plugin/marketplace.json`.

3. **Commit & Push to GitHub**:
   ```bash
   git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
   git commit -m "chore(release): update plugin manifest and commit SHA"
   git push origin main
   ```

4. **Add or Refresh in Claude Code**:
   ```bash
   # Add plugin from local marketplace path or git endpoint:
   /plugin marketplace add ~/.claude/plugins/marketplaces/realm
   # Or from public/remote git URL:
   /plugin marketplace add blackmo18/realm
   ```

---

## Uninstallation

```bash
# Skills CLI installs (Cursor, Codex, Gemini)
npx skills remove realm
```

For Claude Code installs:

```bash
./uninstall.sh
```

Full uninstall guide: [UNINSTALL.md](UNINSTALL.md)

---

## Quick Start

```bash
# 1. Bootstrap the vault for your project
/realm-forge

# 2. Investigate before changing code
/realm-fathom function:validateUser

# 3. Query existing ADRs
/realm-recall "why JWT"

# 4. Plan complex architectural changes
/realm-planning "refactor payment module"

# 5. Check god-file tech debt queue
/realm-concise
```

---

## Querying the Vault

### Decision queries (primary use case)

```bash
/realm-recall "why did we choose X"       # rationale field
/realm-recall "what was rejected for Y"   # rejected_alternatives field
/realm-recall "constraint on Z"           # consequences field
/realm-recall decisions                   # all ADR nodes, compressed
```

### Before touching unfamiliar code

```bash
/realm-fathom function:validateUser       # signature, flow, callers + vault why + drift check
/realm-fathom class:AuthService           # class responsibility + vault ADR context
/realm-fathom "how does auth flow work"   # freeform → relevant code mapped + vault decisions
```

---

## Token Economics

### What realm-recall saves

| Question | Without vault | With realm-recall | Savings |
|----------|--------------|-------------------|---------|
| "Why did we choose JWT?" | 500–2K tokens (multi-file + reasoning) | ~20 tokens | 97% |
| "What was rejected for auth?" | Cannot answer without docs | ~30 tokens | — |
| "Any constraint on payment module?" | Cannot answer without docs | ~25 tokens | — |

---

## Vault Structure

```
<vault>/projects/<slug>/
├── overview.md          # status, stack, milestone tracker, key file links
├── architecture.md      # service map, event shapes, data flow, schema groups
├── decisions/
│   ├── ADR-000-index.md # table of all ADRs
│   └── <id>.md          # one file per decision
├── discoveries/
│   └── YYYY-MM-DD-<topic>.md  # perf notes, bug discoveries
└── sessions/
    └── YYYY-MM-DD-<topic>.md  # per-session logs
```

---

## Dependencies

| Dependency | Purpose |
|---|---|
| Supported host: Claude Code, Cursor, Codex, or Gemini | Runtime for Realm skills |
| Node.js with `npx` | Installs Realm for Cursor, Codex, and Gemini |
| [Obsidian](https://obsidian.md) 1.x+ | Vault storage, graph view, backlinks |
| Graphify CLI (optional) | Fast zero-token codebase discovery for `realm-fathom` & `realm-planning` |

**Diagrams:** [VISUALS.md](VISUALS.md) — pipeline flows & architecture diagrams.
