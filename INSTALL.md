# Install Realm

See [REQUIREMENTS.md](REQUIREMENTS.md) before proceeding.

Realm supports Claude Code, Cursor, Codex, and Gemini. Use the install path that matches your host.

## Cursor, Codex, and Gemini

### One-liner

```bash
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent codex
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent cursor
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent gemini
```

### Direct install

```bash
npx skills add blackmo18/realm -a codex
npx skills add blackmo18/realm -a cursor
npx skills add blackmo18/realm -a gemini
```

What it does:

- Installs Realm's skills into the selected host from `blackmo18/realm`
- Makes the Realm command set available in new sessions
- Leaves your current repo untouched until you actually run `/realm-forge`

Want to preview before installing?

```bash
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent codex --dry-run
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent cursor --dry-run
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent gemini --dry-run
```

After installing:

1. Restart your host or open a new session.
2. In the project you want to map, run `/realm-forge`.
3. Continue with the pipeline below.

## Claude Code

Claude Code installs Realm as a local plugin. From a local clone of this repo:

```bash
# 1. Install caveman plugin (required — provides cavecrew-investigator and caveman-compress)
/plugin marketplace add ~/.claude/plugins/marketplaces/caveman

# 2. Copy Realm into the Claude plugin marketplace path
node bin/install.js --agent claude --force

# 3. Install realm inside Claude Code
/plugin marketplace add ~/.claude/plugins/marketplaces/realm
```

Preview the local copy step first:

```bash
node bin/install.js --agent claude --dry-run
```

## Pipeline Quick Start

Once Realm is installed in your host, use the same project pipeline everywhere.

### 1. Bootstrap a project

Run once per project. Creates vault structure and local state:

```bash
/realm-forge
```

Prompts for your Obsidian vault root if not already configured (e.g. `/Users/you/Documents/obsidian/universe`).

What it creates:

```
<vault>/projects/<slug>/
├── overview.md
├── architecture.md          ← written after first realm-manifest
├── decisions/
│   └── ADR-000-index.md
├── functions/
├── classes/
├── systems/
├── discoveries/
└── sessions/
<vault>/_templates/          ← Decision-Node, Function-Node, Class-Node, etc.
<project-root>/.realm/
└── realm-state.json         ← pipeline state (gitignored)
<project-root>/.claude/
└── CLAUDE.md                ← project anchor (vault path + usage notes)
```

### 2. First scan

Scans the codebase and stages a doc plan for review. No vault writes yet:

```bash
/realm-phase
```

Review the draft at `.realm/manifest-draft.md`. Edit or discard sections as needed.

### 3. Write to vault

Writes staged draft to vault, generates backlinks, archives draft:

```bash
/realm-manifest
```

Vault is now populated. Open in Obsidian to explore the graph.

### 4. Query

```bash
/realm-recall auth                    # all #auth nodes, compressed
/realm-recall validateUser            # function node + deps
/realm-recall "why JWT"               # semantic → decision nodes
/realm-recall auth --trace            # link tree only, explore in Obsidian
/realm-recall auth --count            # estimate tokens before pulling
```

### 5. Keep vault current

After small code changes:

```bash
/realm-flourish
```

After specific function/class changed:

```bash
/realm-phase function:validateUser
/realm-manifest
```

After a coding session with new discoveries:

```bash
/realm-convey
```

After major milestone:

```bash
/realm-phase
/realm-manifest
```

---

## Optional: Session Hooks

Add to `.claude/settings.json` to prompt vault sync at session end:

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

## Guards and Error Messages

| Message | Cause | Fix |
|---|---|---|
| `No realm state found. Run /realm-forge first.` | `.realm/realm-state.json` missing | `/realm-forge` |
| `No staged draft. Run /realm-phase first.` | Tried to manifest without phase | `/realm-phase` |
| `Staged draft exists. Run /realm-manifest first.` | Phase run pending | `/realm-manifest` or delete `.realm/manifest-draft.md` |
| `No nodes in vault yet.` | Recalled before first manifest | `/realm-phase` then `/realm-manifest` |

---

## Pipeline Order

```
/realm-forge       ← once per project
    ↓
/realm-phase       ← scan + stage (review .realm/manifest-draft.md)
    ↓
/realm-manifest    ← write staged draft to vault
    ↓
/realm-recall      ← query vault anytime (read-only)
/realm-status      ← health check anytime (read-only)

Incremental:
/realm-flourish    ← git diff → targeted scan → auto-commit minor changes
/realm-convey      ← compress conversation → user picks topics → targeted phase
```

---

## Updating Realm

```bash
./update.sh
```

Pulls latest from `main`, syncs skills to the Claude Code plugin path if installed elsewhere, and checks the caveman dependency. Restart Claude Code after.

If installed in-place (repo cloned directly to `~/.claude/plugins/marketplaces/realm`), the git pull is the full update — no sync needed.

For Cursor, Codex, or Gemini installs, re-run the matching command:

```bash
npx skills add blackmo18/realm -a codex
npx skills add blackmo18/realm -a cursor
npx skills add blackmo18/realm -a gemini
```

Then restart your host or open a new session so the refreshed skills are loaded.

---

## Uninstalling Realm

Cursor, Codex, and Gemini:

```bash
npx skills remove realm
```

Claude Code and local project cleanup:

```bash
./uninstall.sh
```

Or see [UNINSTALL.md](UNINSTALL.md) for manual uninstall steps.
