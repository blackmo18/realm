# Install Realm

See [REQUIREMENTS.md](REQUIREMENTS.md) before proceeding.

Realm supports Claude Code, Cursor, Codex, and Gemini / Antigravity. Use the install path that matches your host.

---

## Codex, Cursor, and Gemini

### Recommended install

```bash
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent codex
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent cursor
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent gemini
```

For Codex and Gemini, the installer copies both Realm skills and the native subagent files into `~/.codex/agents/` and `~/.gemini/agents/`.

### Skills-only direct install

```bash
npx skills add blackmo18/realm -a codex
npx skills add blackmo18/realm -a cursor
npx skills add blackmo18/realm -a gemini
```

The direct `npx` command installs skills only. For Codex and Gemini, it does not copy Realm's native agent TOML files into `~/.codex/agents/` or `~/.gemini/agents/`.

What it does:

- Installs Realm's skills into the selected host from `blackmo18/realm`
- Makes the Realm command set available in new sessions
- Leaves your current repo untouched until you actually run `/realm-forge`
- For Codex & Gemini: also installs native subagent definitions when using `install.sh` or `node bin/install.js`

Preview before installing:

```bash
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent codex --dry-run
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent gemini --dry-run
```

After installing:

1. Restart your host or open a new session.
2. In the project you want to track, run `/realm-forge`.

### Local-clone install (Codex & Gemini)

From a local Realm clone, this installs both Skills CLI entries and host-native agents:

```bash
node bin/install.js --agent codex
node bin/install.js --agent gemini
```

Preview first:

```bash
node bin/install.js --agent codex --dry-run
node bin/install.js --agent gemini --dry-run
```

---

## Claude Code

Claude Code installs Realm as a local or remote plugin. From a local clone of this repo:

```bash
# 1. Install caveman plugin (required — provides cavecrew-investigator)
/plugin marketplace add ~/.claude/plugins/marketplaces/caveman

# 2. Copy Realm into the Claude plugin marketplace path
node bin/install.js --agent claude --force

# 3. Install realm inside Claude Code
/plugin marketplace add ~/.claude/plugins/marketplaces/realm
```

---

## Uploading & Publishing to Claude Plugins

To upload, publish, or update Realm on the Claude Code plugin marketplace:

### 1. Structure Requirements

Claude Code plugins require a `.claude-plugin/` metadata folder with two key JSON files:
- `.claude-plugin/plugin.json`: Defines the plugin name, version, description, and author.
- `.claude-plugin/marketplace.json`: Defines the plugin marketplace entry, repository URL, commit SHA, and category.

### 2. Update Manifest Files

Before publishing a release:

1. Bump the version in `.claude-plugin/plugin.json`:
   ```json
   {
     "name": "realm",
     "description": "Obsidian project-knowledge & decision memory pipeline...",
     "version": "0.1.6",
     "author": { ... }
   }
   ```

2. Get your latest git commit SHA and update `.claude-plugin/marketplace.json`:
   ```bash
   git rev-parse HEAD
   ```
   Update `plugins[0].source.sha` in `.claude-plugin/marketplace.json`:
   ```json
   {
     "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
     "name": "realm",
     "description": "Obsidian project-knowledge & decision memory pipeline...",
     "plugins": [
       {
         "name": "realm",
         "source": {
           "source": "url",
           "url": "https://github.com/blackmo18/realm.git",
           "sha": "<YOUR_COMMIT_SHA>"
         }
       }
     ]
   }
   ```

### 3. Push to GitHub

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore(release): update plugin manifest and commit SHA"
git push origin main
```

### 4. Register / Add Plugin in Claude Code

Users or team members can now install the plugin directly via GitHub URL or local marketplace path:

```bash
# From GitHub repository:
/plugin marketplace add blackmo18/realm

# Or from local clone:
/plugin marketplace add ~/.claude/plugins/marketplaces/realm
```

---

## Pipeline Quick Start

```bash
# 1. Bootstrap a project
/realm-forge

# 2. Investigate code + vault rationale before changing code
/realm-fathom function:validateUser

# 3. Query existing ADR decisions
/realm-recall "why JWT"

# 4. Plan complex architectural changes
/realm-planning "refactor auth"

# 5. Check god-file tech debt queue
/realm-concise
```

---

## Updating Realm

```bash
./update.sh
```

Pulls latest from `main`, syncs skills to the Claude Code plugin path, refreshes Codex and Gemini native agents, and checks the caveman dependency.

---

## Uninstalling Realm

Cursor, Codex, and Gemini:

```bash
npx skills remove realm
rm -f ~/.codex/agents/realm-agent-*.toml ~/.codex/agents/architect.toml ~/.codex/agents/code-architect.toml
rm -f ~/.gemini/agents/realm-agent-*.toml ~/.gemini/agents/architect.toml ~/.gemini/agents/code-architect.toml
```

Claude Code:

```bash
./uninstall.sh
```

Or see [UNINSTALL.md](UNINSTALL.md) for manual steps.
