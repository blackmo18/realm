# Uninstalling Realm

This guide covers removing the Realm plugin and associated local state from your system.

## Codex Uninstall

Remove only Realm-owned skill directories and agent definitions from `CODEX_HOME`:

```bash
codex_home="${CODEX_HOME:-$HOME/.codex}"
rm -rf "$codex_home/skills/realm-forge" "$codex_home/skills/realm-fathom" \
  "$codex_home/skills/realm-recall" "$codex_home/skills/realm-status" \
  "$codex_home/skills/realm-planning" "$codex_home/skills/realm-concise" \
  "$codex_home/skills/realm-facts" "$codex_home/skills/realm-orchestrate"
rm -f "$codex_home/agents/realm-agent-architect.toml" \
  "$codex_home/agents/realm-agent-code-architect.toml" \
  "$codex_home/agents/realm-agent-plan-implementor.toml" \
  "$codex_home/agents/realm-agent-concise.toml" "$codex_home/agents/realm-agent-fathom.toml" \
  "$codex_home/agents/realm-agent-forge.toml" "$codex_home/agents/realm-agent-planning.toml"
```

If Realm was previously installed through `npx skills`, also run `npx skills remove realm`.

## Cursor and Gemini Uninstall

If you installed Realm with `npx skills add`, remove it with:

```bash
npx skills remove realm
```

If you installed Realm for Gemini with `install.sh` or `node bin/install.js`, also remove its host-native Realm agents:

```bash
rm -f ~/.gemini/agents/realm-agent-*.md
```

Start a new host session after removal so the old skill set is no longer cached.

---

## Quick Uninstall

For Claude Code installs, run the automated uninstall script:

```bash
./uninstall.sh
```

The script prompts for each step and only removes what you choose to remove.

---

## Manual Uninstall

If you prefer to uninstall manually, follow these steps:

### 1. Remove Plugins

Realm depends on the caveman plugin. Remove both:

```bash
# Remove realm plugin
rm -rf ~/.claude/plugins/marketplaces/realm

# Remove caveman plugin (if no longer needed elsewhere)
rm -rf ~/.claude/plugins/marketplaces/caveman
```

Verify they're gone:

```bash
ls ~/.claude/plugins/marketplaces/
```

### 2. Remove Local Project State

In your project root, delete the local realm state directory:

```bash
rm -rf .realm/
```

This removes:
- `realm-state.json` — pipeline state and vault path
- `concise-state.json` — god-file concierge triage queue
- `archive/` — past snapshots

### 3. (Optional) Remove Project Anchor

If you want to remove the project anchor file:

```bash
rm -f .claude/CLAUDE.md
```

This file stores the vault path and usage notes. Keep it if you plan to reinstall realm later.

### 4. (Optional) Remove from .gitignore

Realm adds `.realm/` to `.gitignore`. You can remove that line manually if desired:

```bash
# Edit .gitignore and remove the line:
# .realm/
```

---

## Obsidian Vault

**Your Obsidian vault nodes are NOT deleted during uninstall.**

If you want to remove them:

1. Open Obsidian
2. Navigate to `<vault>/projects/<project-slug>/`
3. Delete the folder and all its contents

---

## After Uninstall

### Realm Skills No Longer Available

These skills will no longer work in the host where Realm was removed. Codex uses
the same names with a `$` prefix; Claude Code and Gemini use `/`:

- `/realm-forge` — Bootstrap vault
- `/realm-fathom` — Parallel code + vault investigation
- `/realm-recall` — Query decision vault
- `/realm-status` — Health check
- `/realm-planning` — Two-phase architecture and impl planning
- `/realm-concise` — God-file concierge triage queue

### Session Hooks

If you added a Stop hook to remind you to sync the vault (in `.claude/settings.json`), remove it:

```json
// REMOVE this from hooks.Stop[]
{
  "command": "echo 'Session ended. Run /realm-convey to capture discoveries or /realm-flourish to sync code changes.'",
  "description": "Remind to sync realm vault"
}
```

---

## Reinstalling

To reinstall realm later:

1. Run the installation steps from [INSTALL.md](INSTALL.md)
2. If you kept the vault nodes, run `/realm-forge` to reconnect them
3. `realm-state.json` will be recreated with the same vault path if `CLAUDE.md` exists

---

## Troubleshooting

**Plugins still showing in Claude Code?**
- Restart Claude Code after deletion
- Verify the directories are actually gone: `ls ~/.claude/plugins/marketplaces/`

**Can't delete `.realm/` or `.claude/CLAUDE.md`?**
- Check permissions: `ls -la .realm .claude/CLAUDE.md`
- Close any open processes accessing the project
- Try: `sudo rm -rf .realm` (if needed)

**Want to keep vault but remove plugins?**
- Just delete the plugin directories — the vault remains in Obsidian
- Your vault nodes will be accessible in Obsidian even without realm

---

## Questions?

For issues during uninstall, open an issue at: https://github.com/anthropics/claude-code/issues
