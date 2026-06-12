#!/bin/bash
set -euo pipefail

REPO_SLUG="blackmo18/realm"
AGENT="codex"
DRY_RUN=false
FORCE=false
PLUGIN_DIR="${HOME}/.claude/plugins/marketplaces/realm"

usage() {
  cat <<'EOF'
Realm installer

Usage:
  ./install.sh [--dry-run] [--repo <owner/repo>] [--agent <claude|cursor|codex|gemini>]

Examples:
  ./install.sh
  ./install.sh --dry-run
  ./install.sh --agent cursor
  ./install.sh --agent gemini
  ./install.sh --agent claude --plugin-dir ~/.claude/plugins/marketplaces/realm
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --force)
      FORCE=true
      shift
      ;;
    --repo)
      if [ $# -lt 2 ]; then
        echo "Missing value for --repo" >&2
        exit 1
      fi
      REPO_SLUG="$2"
      shift 2
      ;;
    --agent)
      if [ $# -lt 2 ]; then
        echo "Missing value for --agent" >&2
        exit 1
      fi
      AGENT="$2"
      shift 2
      ;;
    --plugin-dir)
      if [ $# -lt 2 ]; then
        echo "Missing value for --plugin-dir" >&2
        exit 1
      fi
      PLUGIN_DIR="${2/#\~/$HOME}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

case "$AGENT" in
  codex|cursor|gemini)
    if ! command -v npx >/dev/null 2>&1; then
      echo "npx is required to install Realm for $AGENT. Install Node.js first." >&2
      exit 1
    fi

    CMD=(npx skills add "$REPO_SLUG" -a "$AGENT")

    echo "Realm install target: $REPO_SLUG"
    echo "Agent: $AGENT"
    echo "Command: ${CMD[*]}"

    if [ "$DRY_RUN" = true ]; then
      echo "Dry run complete."
      exit 0
    fi

    "${CMD[@]}"

    cat <<EOF

Realm is installed for $AGENT.

Next steps:
1. Restart $AGENT or open a new session so the new skills are loaded cleanly.
2. In your project, run /realm-forge to bootstrap the local Realm state.
3. Then run /realm-phase and /realm-manifest for the first vault sync.
EOF
    ;;
  claude)
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    if [ -f "$SCRIPT_DIR/bin/install.js" ]; then
      CMD=(node "$SCRIPT_DIR/bin/install.js" --agent claude --plugin-dir "$PLUGIN_DIR")
      [ "$DRY_RUN" = true ] && CMD+=(--dry-run)
      [ "$FORCE" = true ] && CMD+=(--force)

      echo "Realm install target: local clone"
      echo "Agent: claude"
      echo "Command: ${CMD[*]}"

      "${CMD[@]}"
      exit 0
    fi

    if ! command -v git >/dev/null 2>&1; then
      echo "git is required for one-line Claude Code install. Install git or clone ${REPO_SLUG} manually." >&2
      exit 1
    fi

    AGENTS_DIR="${HOME}/.claude/agents"
    CAVEMAN_DIR="${HOME}/.claude/plugins/marketplaces/caveman"

    echo "Realm install target: https://github.com/${REPO_SLUG}.git"
    echo "Agent: claude"
    echo "Plugin dir: $PLUGIN_DIR"

    if [ -e "$PLUGIN_DIR" ] && [ "$FORCE" != true ]; then
      echo "Claude plugin destination already exists: $PLUGIN_DIR" >&2
      echo "Use --force to replace it, or choose a different --plugin-dir." >&2
      exit 1
    fi

    if [ "$DRY_RUN" = true ]; then
      echo "Planned actions:"
      echo "- Clone https://github.com/${REPO_SLUG}.git into $PLUGIN_DIR"
      echo "- Copy realm agents into $AGENTS_DIR"
      [ ! -d "$CAVEMAN_DIR" ] && echo "- Warn that caveman is not present at $CAVEMAN_DIR"
      echo "- Remind you to run /plugin marketplace add inside Claude Code"
      echo "Dry run complete."
      exit 0
    fi

    if [ -e "$PLUGIN_DIR" ]; then
      rm -rf "$PLUGIN_DIR"
    fi

    mkdir -p "$(dirname "$PLUGIN_DIR")"
    git clone "https://github.com/${REPO_SLUG}.git" "$PLUGIN_DIR"

    if [ -d "$PLUGIN_DIR/agents" ]; then
      mkdir -p "$AGENTS_DIR"
      cp "$PLUGIN_DIR"/agents/*.md "$AGENTS_DIR"/
    fi

    if [ ! -d "$CAVEMAN_DIR" ]; then
      echo "Warning: caveman dependency not found at $CAVEMAN_DIR" >&2
      echo "Install caveman first if you have not already."
    fi

    cat <<EOF

Realm files copied for Claude Code.
Plugin path: $PLUGIN_DIR

Next steps inside Claude Code:
1. Run /plugin marketplace add $PLUGIN_DIR
2. Restart Claude Code so the refreshed skills are loaded.
3. In your project, run /realm-forge to bootstrap local Realm state.
EOF
    ;;
  *)
    echo "Unsupported agent: $AGENT" >&2
    echo "Supported agents: claude, cursor, codex, gemini" >&2
    exit 1
    ;;
esac
