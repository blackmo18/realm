#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || echo "")"
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/bin/install.js" ]; then
  exec node "$SCRIPT_DIR/bin/install.js" "$@"
fi

REPO_SLUG="blackmo18/realm"
AGENT="codex"
DRY_RUN=false
FORCE=false
IS_LOCAL=false
TARGET_DIR=""
PLUGIN_DIR="${HOME}/.claude/plugins/marketplaces/realm"

usage() {
  cat <<'EOF'
Realm installer

Usage:
  ./install.sh [--dry-run] [--local [dir]] [--repo <owner/repo>] [--agent <claude|cursor|codex|gemini>]

Options:
  --agent <agent>          Install target: claude, cursor, codex, gemini. Default: codex
  --local [dir], -l [dir]  Install locally into a project workspace (defaults to current directory)
  --target-dir <dir>       Explicit project destination directory for local installation
  --repo <owner/repo>      Repo slug used for Skills CLI installs. Default: blackmo18/realm
  --plugin-dir <path>      Claude plugin destination. Default: ~/.claude/plugins/marketplaces/realm
  --dry-run                Print planned actions without changing anything
  --force                  Overwrite existing files
  -h, --help               Show this help

Examples:
  ./install.sh
  ./install.sh --dry-run
  ./install.sh --agent gemini
  ./install.sh --agent gemini --local
  ./install.sh --agent gemini --local /path/to/project
  ./install.sh --agent codex --local
  ./install.sh --agent cursor --local
  ./install.sh --agent claude --local
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
    --local|-l)
      IS_LOCAL=true
      if [ $# -ge 2 ] && [[ "$2" != -* ]]; then
        TARGET_DIR="$2"
        shift 2
      else
        TARGET_DIR="$(pwd)"
        shift
      fi
      ;;
    --target-dir|--project-dir)
      if [ $# -lt 2 ]; then
        echo "Missing value for $1" >&2
        exit 1
      fi
      IS_LOCAL=true
      TARGET_DIR="$2"
      shift 2
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

if [ "$IS_LOCAL" = true ]; then
  TARGET_DIR="${TARGET_DIR/#\~/$HOME}"
  [ -z "$TARGET_DIR" ] && TARGET_DIR="$(pwd)"
  mkdir -p "$TARGET_DIR"
  TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"

  echo "Realm local install target: $TARGET_DIR"
  echo "Agent: $AGENT"

  if [ "$DRY_RUN" = true ]; then
    echo "Planned Local Actions:"
    case "$AGENT" in
      gemini)
        echo "- Copy skills -> $TARGET_DIR/.agents/skills"
        echo "- Copy .gemini/agents/*.md -> $TARGET_DIR/.gemini/agents"
        ;;
      codex)
        echo "- Copy skills -> $TARGET_DIR/.agents/skills and $TARGET_DIR/.codex/skills"
        echo "- Copy .codex/agents/*.toml -> $TARGET_DIR/.codex/agents"
        ;;
      cursor)
        echo "- Copy skills -> $TARGET_DIR/.cursor/skills and $TARGET_DIR/.agents/skills"
        ;;
      claude)
        echo "- Copy skills -> $TARGET_DIR/.claude/skills"
        echo "- Copy agents/*.md -> $TARGET_DIR/.claude/agents"
        ;;
    esac
    echo "Dry run complete."
    exit 0
  fi

  TMP_DIR="$(mktemp -d)"
  git clone --depth 1 "https://github.com/${REPO_SLUG}.git" "$TMP_DIR/realm" >/dev/null 2>&1
  SOURCE_DIR="$TMP_DIR/realm"

  case "$AGENT" in
    gemini)
      mkdir -p "$TARGET_DIR/.agents/skills" "$TARGET_DIR/.gemini/agents"
      cp -r "$SOURCE_DIR"/skills/* "$TARGET_DIR/.agents/skills/"
      cp "$SOURCE_DIR"/.gemini/agents/*.md "$TARGET_DIR/.gemini/agents/"
      ;;
    codex)
      mkdir -p "$TARGET_DIR/.agents/skills" "$TARGET_DIR/.codex/skills" "$TARGET_DIR/.codex/agents"
      cp -r "$SOURCE_DIR"/skills/* "$TARGET_DIR/.agents/skills/"
      cp -r "$SOURCE_DIR"/skills/* "$TARGET_DIR/.codex/skills/"
      cp "$SOURCE_DIR"/.codex/agents/*.toml "$TARGET_DIR/.codex/agents/"
      ;;
    cursor)
      mkdir -p "$TARGET_DIR/.agents/skills" "$TARGET_DIR/.cursor/skills"
      cp -r "$SOURCE_DIR"/skills/* "$TARGET_DIR/.agents/skills/"
      cp -r "$SOURCE_DIR"/skills/* "$TARGET_DIR/.cursor/skills/"
      ;;
    claude)
      mkdir -p "$TARGET_DIR/.claude/skills" "$TARGET_DIR/.claude/agents"
      cp -r "$SOURCE_DIR"/skills/* "$TARGET_DIR/.claude/skills/"
      cp "$SOURCE_DIR"/agents/*.md "$TARGET_DIR/.claude/agents/"
      ;;
  esac

  rm -rf "$TMP_DIR"

  echo ""
  echo "Realm is installed locally for $AGENT in $TARGET_DIR."
  echo ""
  echo "Next steps:"
  echo "1. Open $TARGET_DIR in $AGENT."
  echo "2. Run /realm-forge to bootstrap local Realm vault state for this project."
  echo "3. Query with /realm-recall or investigate with /realm-fathom."
  exit 0
fi

case "$AGENT" in
  codex|cursor|gemini)
    CMD=(npx skills add "$REPO_SLUG" -a "$AGENT")

    echo "Realm install target: $REPO_SLUG"
    echo "Agent: $AGENT"
    echo "Command: ${CMD[*]}"

    if [ "$DRY_RUN" = true ]; then
      if [ "$AGENT" = "codex" ]; then
        echo "Planned Codex native agent install:"
        echo "- Copy .codex/agents/*.toml into ~/.codex/agents/"
        echo "- If this script is run remotely, clone https://github.com/${REPO_SLUG}.git into a temp dir first"
      elif [ "$AGENT" = "gemini" ]; then
        echo "Planned Gemini native agent install:"
        echo "- Copy .gemini/agents/*.md into ~/.gemini/agents/"
        echo "- If this script is run remotely, clone https://github.com/${REPO_SLUG}.git into a temp dir first"
      fi
      echo "Dry run complete."
      exit 0
    fi

    if ! command -v npx >/dev/null 2>&1; then
      echo "npx is required to install Realm for $AGENT. Install Node.js first." >&2
      exit 1
    fi

    "${CMD[@]}"

    if [ "$AGENT" = "codex" ] || [ "$AGENT" = "gemini" ]; then
      TARGET_DIR="${HOME}/.${AGENT}/agents"
      TMP_DIR="$(mktemp -d)"
      git clone --depth 1 "https://github.com/${REPO_SLUG}.git" "$TMP_DIR/realm" >/dev/null 2>&1
      AGENTS_SRC="$TMP_DIR/realm/.$AGENT/agents"
      EXT="toml"
      [ "$AGENT" = "gemini" ] && EXT="md"

      if [ -n "$AGENTS_SRC" ] && [ -d "$AGENTS_SRC" ]; then
        mkdir -p "$TARGET_DIR"
        cp "$AGENTS_SRC"/*."$EXT" "$TARGET_DIR"/
        echo "$AGENT-native Realm agents installed to $TARGET_DIR"
      fi

      rm -rf "$TMP_DIR"
    fi

    cat <<EOF

Realm is installed globally for $AGENT.

Next steps:
1. Restart $AGENT or open a new session so the new skills are loaded cleanly.
2. In your project, run /realm-forge to bootstrap the local Realm state.
3. Query with /realm-recall or investigate with /realm-fathom.
EOF
    ;;
  claude)
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

