# Requirements

## Required

### Supported AI Host
- Install one or more supported hosts: **Claude Code**, **Cursor**, **Codex**, or **Gemini / Antigravity**.
- Cursor, Codex, and Gemini installs use the Skills CLI through `npx`.
- Codex and Gemini full installs also copy native custom-agent files (Codex: `.toml`, Gemini: `.md`) to `~/.codex/agents/` and `~/.gemini/agents/` when you use `install.sh` or `node bin/install.js --agent <codex|gemini>`.
- Claude Code installs use the local plugin marketplace path.

Install commands:

```bash
npx skills add blackmo18/realm -a codex
npx skills add blackmo18/realm -a cursor
npx skills add blackmo18/realm -a gemini
```

For Codex and Gemini native agents, use the installer instead of direct `npx`:

```bash
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent codex
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent gemini
# or from a local clone:
node bin/install.js --agent codex
node bin/install.js --agent gemini
```

### Python 3.9+
- Version: Python 3.9 or higher
- Used by: Realm helper scripts (`skills/realm-concise/scripts/concise.py` for god-file triage, `skills/realm-forge/scripts/forge_init.py` for vault bootstrap, and `skills/realm-facts/scripts/facts.py` for team facts).

### Node.js and npx
- Version: Any recent Node.js LTS release with `npx`
- Used by: Skills CLI installer and host plugin management.

### Obsidian
- Version: 1.x or later
- Download: https://obsidian.md
- Used by: Vault storage, graph view, backlinks, tag pane.
- An existing vault directory must exist before running `/realm-forge`.

### Git
- Version: Any recent version
- Used by: Remote installer scripts, team facts workflow (`realm-facts`), and repository tracking.

---

## Recommended Tools

### Graphify CLI (Optional / Recommended)
- Purpose: Fast zero-LLM-token codebase discovery, symbol resolution, and call-graph traversal for `/realm-fathom` and `/realm-planning` (Phase 1).
- Used by: Realm's code discovery layer when `graphify-out/graph.json` exists.
- Fallback: If `graphify` is absent, stale, or unavailable, Realm automatically falls back to `cavecrew-investigator`.

---

## Plugin Dependencies

Realm depends on the **caveman** plugin for compressed code investigation:

| Skill / Agent | Used By | Purpose |
|---|---|---|
| `cavecrew-investigator` agent | `realm-fathom`, `realm-planning` | Deep live code investigation; outputs caveman-compressed findings |

Install caveman first for Claude Code:

```bash
/plugin marketplace add ~/.claude/plugins/marketplaces/caveman
```

---

## Obsidian Plugins (Optional)

Enhance graph exploration — not required for Realm to function:

| Plugin | Purpose |
|---|---|
| Dataview | Query nodes by tag, type, or date |
| Graph Analysis | Enhanced backlink traversal |
| Templater | Use vault templates created by realm-forge |

---

## File System Permissions

- Write access to your Obsidian vault directory
- Write access to project root (for `.realm/` and `.claude/CLAUDE.md`)
- `.realm/` is local-only state — added to `.gitignore` by `/realm-forge`
