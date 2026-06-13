# Host Compatibility

Realm supports two execution shapes:

1. Claude Code plugin install
   - Claude Code loads `agents/*.md` as named subagents.
   - When a skill says to spawn `realm-agent-*`, use the matching Claude subagent if available.

2. Skills CLI / Codex install
   - Codex installs the `skills/` tree and may not have Claude-style `agents/*.md`.
   - When a skill says to spawn `realm-agent-*` and no matching subagent is available, read the matching mirrored procedure from `skills/_shared/agents/<agent-name>.md` and execute it inline.
   - If Codex-native subagents are explicitly available and approved by the user, the procedure may be delegated; otherwise the main assistant owns the work.

Path resolution:

- Prefer paths relative to the loaded skill directory.
- Shared conventions live at `skills/_shared/realm-conventions.md`.
- Mirrored agent procedures live at `skills/_shared/agents/`.
- Claude Code installs may also have canonical agent files under `<pluginRoot>/agents/`.

Write boundary:

- `.realm/` writes happen in the current project root.
- Obsidian vault writes may be outside the project root. Hosts with filesystem approvals must ask for or use the required approval before writing there.
- `realm-forge` may write `.claude/CLAUDE.md` for Claude compatibility and `AGENTS.md` for host-neutral/Codex compatibility. Never overwrite either file if it already exists.
