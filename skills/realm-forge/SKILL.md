---
name: realm-forge
description: >
  Bootstrap a project's Obsidian knowledge base and local realm state. Creates the vault directory structure (overview, architecture, decisions/, sessions/, templates), writes a .claude/CLAUDE.md project anchor, seeds .realm/realm-state.json, and adds .realm/ to .gitignore. Idempotent — safe to re-run; never overwrites existing vault docs. First step in the realm pipeline.
origin: realm
---

# realm-forge

Bootstrap Obsidian knowledge base for current project. First skill in realm pipeline.

## When to Use

| Trigger | Example |
|---|---|
| First-time setup | "init realm", `/realm-forge` |
| Vault path not configured | "set up project knowledge base" |
| `.realm/realm-state.json` missing | Starting pipeline from scratch |
| Adding realm to project with existing Obsidian docs | Idempotent — detects existing docs |

## When NOT to Use

- Project initialized, want to query vault → `/realm-recall`
- Project initialized, want to investigate code → `/realm-fathom`
- Project initialized, state current → `/realm-status` to check

---

## Procedure

This skill handles interactive vault path resolution, then delegates all setup work to `realm-agent-forge`.

### Step 1 — Resolve vault path and project slug (interactive)

1. Check args. If vault path provided, use it.
2. No arg: check if `<projectRoot>/.realm/realm-state.json` exists → reuse its `vaultPath`.
3. Still not found: ask user for Obsidian vault root. Example: `/Users/username/Documents/obsidian/universe`. **Wait for reply before proceeding.**
4. Derive `projectSlug`: read `package.json` `.name`; if absent, use repo root dir name. Normalize to kebab-case.
5. Print `Vault: <path>  Slug: <slug>` and proceed.

### Step 2 — Spawn forge agent

Spawn agent `realm-agent-forge` with this prompt:

```
projectRoot: <absolute path to project root>
vaultPath: <resolved vault path from Step 1>
projectSlug: <derived slug from Step 1>

Bootstrap the vault and write realm-state.json.
Follow the full procedure in your instructions.
```

Wait for completion. Surface the agent's summary to the user.
