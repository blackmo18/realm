# Install Realm

See [REQUIREMENTS.md](REQUIREMENTS.md) before proceeding.

Realm supports Claude Code, Cursor, Codex, and Gemini / Antigravity. Use the install path that matches your host.

Invocation syntax differs by host: Claude Code and Gemini use `/realm-forge`; Codex uses
`$realm-forge`. The same rule applies to every Realm skill name.

---

## Codex

### Recommended install

```bash
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent codex
```

This installs Realm skills to `${CODEX_HOME:-$HOME/.codex}/skills` and native
subagents to `${CODEX_HOME:-$HOME/.codex}/agents`. It does not require the
third-party Skills CLI.

From a local clone:

```bash
node bin/install.mjs --agent codex
node bin/install.mjs --agent codex --dry-run
```

## Cursor plugin install

Realm ships a Cursor plugin manifest at `.cursor-plugin/plugin.json`, so Cursor can install it
straight from the repository URL. In Cursor, open **Settings → Plugins**, choose to install from a
Git repository, and enter:

```
https://github.com/blackmo18/realm
```

This registers Realm's skills (`skills/`) and the Cursor-native agent adapters
(`.cursor/agents/`) in one step. Restart Cursor or run **Developer: Reload Window**, then run
`/realm-forge` in your project.

To test an unpublished change before pushing, load the plugin locally instead:

```bash
mkdir -p ~/.cursor/plugins/local
cp -R /path/to/realm ~/.cursor/plugins/local/realm
```

Restart Cursor and confirm the Realm skills and agents appear.

## Cursor and Gemini

The script installer remains available and is still the path for Gemini:

```bash
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent cursor
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent gemini
```

The Gemini installer also creates host-native agent adapters under `~/.gemini/agents/`.

Model tiers are adapted per host: planning/architecture use the strongest tier, while deterministic
query/concierge wrappers use the basic tier. Codex defaults to Sol/Terra/Luna and Claude to
Opus/Sonnet/Haiku. By explicit policy, Gemini uses 3.1 Pro Preview for both planning and semantic
execution, and 3.6 Flash for mechanical work. Explicit host configuration may override these defaults.
Gemini adapters omit Claude-specific tool names and inherit the Gemini session's registered tools.

### Skills CLI install for Cursor and Gemini

```bash
npx skills add blackmo18/realm -a cursor
npx skills add blackmo18/realm -a gemini
```

The direct `npx` command installs skills only. The recommended installer also installs
Cursor or Gemini native agent adapters.

What it does:

- Installs Realm's skills into the selected host from `blackmo18/realm`
- Makes the Realm command set available in new sessions
- Leaves your current repo untouched until you run the host's Realm forge command
- The recommended Codex and Gemini installers also install their native subagent definitions

Preview before installing:

```bash
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent codex --dry-run
curl -fsSL https://raw.githubusercontent.com/blackmo18/realm/main/install.sh | bash -s -- --agent gemini --dry-run
```

After installing:

1. Restart your host or open a new session.
2. In Codex run `$realm-forge`; in Claude Code or Gemini run `/realm-forge`.

### Global Install (Cursor and Gemini)

From a local Realm clone, this installs both Skills CLI entries and host-native agents globally to your machine:

```bash
node bin/install.mjs --agent gemini
```

Preview first:

```bash
node bin/install.mjs --agent gemini --dry-run
```

---

## Local / Project-Scoped Installation

If you prefer **not** to install Realm globally on your machine, you can install it into a single project workspace using `--local`:

### 1. Into the current directory
```bash
# Antigravity / Gemini
./install.sh --agent gemini --local

# Codex
./install.sh --agent codex --local

# Cursor
./install.sh --agent cursor --local

# Claude Code
./install.sh --agent claude --local
```

### 2. Into a specific project directory
```bash
./install.sh --agent gemini --local /path/to/my-project
node bin/install.mjs --agent codex --local /path/to/my-project
```

### What Local Install Does:
- **Gemini / Antigravity**: Copies skills into `<project>/.agents/skills/` and agent definitions into `<project>/.gemini/agents/`.
- **Codex**: Copies skills into `<project>/.agents/skills/` and agent definitions into `<project>/.codex/agents/`.
- **Cursor**: Copies portable skills into `<project>/.agents/skills/` and native
  subagents into `<project>/.cursor/agents/`.
- **Claude Code**: Copies skills into `<project>/.claude/skills/` and agent definitions into `<project>/.claude/agents/`.
- **Zero Global State**: Leaves your `~` user home directory completely untouched.


---

## Claude Code

Claude Code installs Realm as a local or remote plugin. From a local clone of this repo:

```bash
# 1. Install caveman plugin (required — provides cavecrew-investigator)
/plugin marketplace add ~/.claude/plugins/marketplaces/caveman

# 2. Copy Realm into the Claude plugin marketplace path
node bin/install.mjs --agent claude --force

# 3. Install realm inside Claude Code
/plugin marketplace add ~/.claude/plugins/marketplaces/realm
```

---

## Pipeline Quick Start

Codex uses the same names with a `$` prefix, for example `$realm-forge` and
`$realm-planning "refactor auth"`. The examples below use Claude/Gemini syntax.

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

Pulls latest from `main`, synchronizes Realm skills and agents under `CODEX_HOME`, refreshes Claude/Gemini adapters, and checks the caveman dependency.

---

## Uninstalling Realm

Codex native install:

```bash
rm -rf "${CODEX_HOME:-$HOME/.codex}/skills/realm-forge" \
       "${CODEX_HOME:-$HOME/.codex}/skills/realm-fathom" \
       "${CODEX_HOME:-$HOME/.codex}/skills/realm-recall" \
       "${CODEX_HOME:-$HOME/.codex}/skills/realm-status" \
       "${CODEX_HOME:-$HOME/.codex}/skills/realm-planning" \
       "${CODEX_HOME:-$HOME/.codex}/skills/realm-concise" \
       "${CODEX_HOME:-$HOME/.codex}/skills/realm-facts" \
       "${CODEX_HOME:-$HOME/.codex}/skills/realm-orchestrate"
rm -f "${CODEX_HOME:-$HOME/.codex}/agents/realm-agent-architect.toml" \
      "${CODEX_HOME:-$HOME/.codex}/agents/realm-agent-code-architect.toml" \
      "${CODEX_HOME:-$HOME/.codex}/agents/realm-agent-plan-implementor.toml" \
      "${CODEX_HOME:-$HOME/.codex}/agents/realm-agent-concise.toml" \
      "${CODEX_HOME:-$HOME/.codex}/agents/realm-agent-fathom.toml" \
      "${CODEX_HOME:-$HOME/.codex}/agents/realm-agent-forge.toml" \
      "${CODEX_HOME:-$HOME/.codex}/agents/realm-agent-planning.toml"
```

Cursor and Gemini Skills CLI installs:

```bash
npx skills remove realm
rm -f ~/.gemini/agents/realm-agent-*.md
```

Claude Code:

```bash
./uninstall.sh
```

Or see [UNINSTALL.md](UNINSTALL.md) for manual steps.
