# Requirements

## Required

### Supported AI host
- Install one or more supported hosts: Claude Code, Cursor, Codex, or Gemini.
- Cursor, Codex, and Gemini installs use the Skills CLI through `npx`.
- Claude Code installs use the local plugin marketplace path.

Install commands:

```bash
npx skills add blackmo18/realm -a codex
npx skills add blackmo18/realm -a cursor
npx skills add blackmo18/realm -a gemini
```

### Claude Code CLI
- Version: latest
- Install: https://claude.ai/code
- Used by: Claude Code plugin installs and by Realm's Claude-oriented subagent workflow

### Node.js and npx
- Version: any recent Node.js release with `npx`
- Used by: Cursor, Codex, and Gemini installs

### Obsidian
- Version: 1.x or later
- Download: https://obsidian.md
- Used by: vault storage, graph view, backlinks, tag pane
- An existing vault must exist before running `/realm-forge`

### Git
- Any recent version
- Used by: `realm-flourish` (git diff to detect changed files since last manifest)
- Not strictly required for `realm-forge`, `realm-phase`, `realm-manifest`, `realm-recall`

## Plugin Dependencies

Realm depends on two skills from the **caveman** plugin:

| Skill | Used By | Purpose |
|---|---|---|
| `cavecrew-investigator` agent | `realm-phase`, `realm-flourish` | Scans repo; outputs caveman-compressed findings |
| `caveman-compress` skill | `realm-phase`, `realm-manifest` | Compresses node body prose before vault writes |

Install caveman first for Claude Code:

```bash
/plugin marketplace add ~/.claude/plugins/marketplaces/caveman
```

## Obsidian Plugins (Optional)

Enhance graph exploration — not required for realm to function:

| Plugin | Purpose |
|---|---|
| Dataview | Query nodes by tag, type, or date |
| Graph Analysis | Enhanced backlink traversal |
| Templater | Use vault templates created by realm-forge |

## File System

- Write access to your Obsidian vault directory
- Write access to project root (for `.realm/` and `.claude/CLAUDE.md`)
- `.realm/` is local-only — never committed (realm-forge adds it to `.gitignore`)
