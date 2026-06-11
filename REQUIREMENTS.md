# Requirements

## Required

### Claude Code CLI
- Version: latest
- Install: https://claude.ai/code
- Used by: all realm skills

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

Install caveman first:

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
