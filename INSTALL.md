# Install Realm

See [REQUIREMENTS.md](REQUIREMENTS.md) before proceeding.

Realm supports Claude Code, Cursor, Codex, and Gemini. Use the install path that matches your host.

## Codex, Cursor, and Gemini

### Recommended install

```bash
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent codex
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent cursor
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent gemini
```

For Codex, use the installer path above. It installs both Realm skills and the Codex-native subagent files.

### Skills-only direct install

```bash
npx skills add blackmo18/realm -a codex
npx skills add blackmo18/realm -a cursor
npx skills add blackmo18/realm -a gemini
```

The direct `npx` command installs skills only. For Codex, it does not copy Realm's native agent TOML files into `~/.codex/agents/`.

What it does:

- Installs Realm's skills into the selected host from `blackmo18/realm`
- Makes the Realm command set available in new sessions
- Leaves your current repo untouched until you actually run `/realm-forge`
- For Codex only: also installs Realm's Codex-native subagent definitions into `~/.codex/agents/`

Want to preview before installing?

```bash
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent codex --dry-run
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent cursor --dry-run
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent gemini --dry-run
```

After installing:

1. Restart your host or open a new session.
2. In the project you want to track, run `/realm-forge`.
3. Continue with the pipeline below.

### Codex local-clone install

From a local Realm clone, this installs both Skills CLI entries and Codex-native agents:

```bash
node bin/install.js --agent codex
```

Preview first:

```bash
node bin/install.js --agent codex --dry-run
```

Codex install writes:

- Skills through `npx skills add blackmo18/realm -a codex`
- Native Realm agent TOML files to `~/.codex/agents/realm-agent-*.toml`

The native agents let Codex resolve agent spawns using Codex's custom-agent format. The skills still work without them; the agents improve Codex-native delegation.

## Claude Code

Claude Code installs Realm as a local plugin. From a local clone of this repo:

```bash
# 1. Install caveman plugin (required — provides cavecrew-investigator)
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
├── architecture.md
├── decisions/
│   └── ADR-000-index.md
├── discoveries/
└── sessions/
<project-root>/.realm/
└── realm-state.json         ← pipeline state (gitignored)
<project-root>/.claude/
└── CLAUDE.md                ← project anchor (vault path + usage notes)
```

### 2. Capture a decision

After a session where you made an architectural choice, capture it:

```bash
/realm-convey
```

Realm extracts decisions from the conversation, runs a structured interview per decision (what was decided, what was rejected and why, what constraints it imposes), and stages a manifest draft. No codebase scan.

Review the draft at `.realm/manifest-draft.md`.

### 3. Write to vault

```bash
/realm-manifest
```

Writes ADR nodes to vault, generates backlinks, archives the draft.

### 4. Query

```bash
/realm-recall "why JWT"               # rationale behind a decision
/realm-recall "what was rejected for auth"   # surfaces rejected alternatives
/realm-recall "constraint on payments"       # consequences field
/realm-recall decisions               # all ADR nodes, compressed
/realm-recall decisions --full        # full prose for all ADRs
```

---

## Optional: Session Hook

Add to `.claude/settings.json` to prompt decision capture at session end:

```json
{
  "hooks": {
    "Stop": [
      {
        "command": "echo 'Session ended. Run /realm-convey if you made any architectural decisions.'",
        "description": "Prompt to capture decisions"
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
| `No staged draft. Run /realm-convey first.` | Tried to manifest without convey | `/realm-convey` |
| `No nodes in vault yet.` | Recalled before first manifest | `/realm-convey` then `/realm-manifest` |

---

## Pipeline Order

```
/realm-forge       ← once per project
    ↓
/realm-convey      ← extract decisions from conversation → staged draft
    ↓
/realm-manifest    ← write ADR nodes to vault
    ↓
/realm-recall      ← query vault anytime (read-only)
/realm-fathom      ← live code + vault combined (read-only)
/realm-status      ← health check anytime (read-only)
```

---

## Updating Realm

```bash
./update.sh
```

Pulls latest from `main`, syncs skills to the Claude Code plugin path if installed elsewhere, refreshes Codex-native agents, and checks the caveman dependency.

For Cursor or Gemini installs, re-run the matching command:

```bash
npx skills add blackmo18/realm -a cursor
npx skills add blackmo18/realm -a gemini
```

For Codex, re-run the installer so skills and native agents both refresh:

```bash
node bin/install.js --agent codex
```

Then restart your host or open a new session so the refreshed skills and agents are loaded.

---

## Uninstalling Realm

Cursor, Codex, and Gemini:

```bash
npx skills remove realm
```

Codex native agents:

```bash
rm -f ~/.codex/agents/realm-agent-*.toml
```

Claude Code and local project cleanup:

```bash
./uninstall.sh
```

Or see [UNINSTALL.md](UNINSTALL.md) for manual steps.
