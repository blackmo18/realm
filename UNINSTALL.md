# Uninstalling Realm

This guide covers removing the Realm plugin and associated local state from your system.

## Cursor, Codex, and Gemini Uninstall

If you installed Realm with `npx skills add`, remove it with:

```bash
npx skills remove realm
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
- `manifest-draft.md` — staged changes (if any)
- `archive/` — past manifest snapshots

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
2. Navigate to `<vault>/projects/<project-slug>/` (the slug is your project name, lowercased)
3. Delete the folder and all its contents
4. Optional: Also delete `<vault>/_templates/` if no other projects use realm

Or delete from the command line:

```bash
rm -rf /path/to/your/vault/projects/<project-slug>
rm -rf /path/to/your/vault/_templates/  # only if no other projects use it
```

---

## After Uninstall

### Realm Skills No Longer Available

These skills will no longer work in the host where Realm was removed:

- `/realm-forge` — Bootstrap vault
- `/realm-phase` — Scan and stage
- `/realm-manifest` — Write to vault
- `/realm-flourish` — Incremental update
- `/realm-convey` — Conversation capture
- `/realm-recall` — Query vault
- `/realm-status` — Health check

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
2. If you kept the vault nodes, run `/realm-phase` to detect them
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
