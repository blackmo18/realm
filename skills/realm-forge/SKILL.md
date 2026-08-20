---
name: realm-forge
description: >
  Bootstrap a project's Obsidian knowledge base and local Realm state. Creates the vault structure, writes the active host's project guidance anchor, seeds realm-state.json, and updates .gitignore without overwriting existing documentation. Use for first-time setup, a missing Realm state file, or connecting an existing vault. Supports Claude Code, Cursor, Codex, and Gemini.
---

# realm-forge

Bootstrap Obsidian knowledge base for current project. First skill in realm pipeline.

Host invocation: Claude Code, Cursor, and Gemini use `/realm-forge`; Codex uses `$realm-forge`.

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

This skill handles interactive vault path resolution, then runs the forge procedure.

### Step 1 — Resolve vault path and project slug (interactive)

1. Check args. If vault path provided, use it.
2. No arg: check if `<projectRoot>/.realm/realm-state.json` exists → reuse its `vaultPath`.
3. Still not found: ask user for Obsidian vault root. Example: `/Users/username/Documents/obsidian/universe`. **Wait for reply before proceeding.**
4. Derive `projectSlug`: read `package.json` `.name`; if absent, use repo root dir name. Normalize to kebab-case.
5. Detect active host as `claude`, `cursor`, `codex`, or `gemini`.
6. Print `Vault: <path>  Slug: <slug>  Host: <host>` and proceed.

### Step 2 — Run forge procedure

If the host exposes `realm-agent-forge` and delegation is permitted by the
current user/session policy, delegate with this prompt. Otherwise execute the
same procedure inline. Never require delegation for correctness.

```
projectRoot: <absolute path to project root>
vaultPath: <resolved vault path from Step 1>
projectSlug: <derived slug from Step 1>
host: <claude|cursor|codex|gemini>
realmForgeSkillDir: <directory containing this SKILL.md>

Bootstrap the vault and write realm-state.json.
Follow the full procedure in your instructions.
```

Surface the resulting summary to the user.
