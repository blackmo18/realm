#!/bin/bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REALM_PLUGIN_PATH="$HOME/.claude/plugins/marketplaces/realm"
CAVEMAN_PLUGIN_PATH="$HOME/.claude/plugins/marketplaces/caveman"

echo -e "${GREEN}Realm Update${NC}"
echo "============"
echo ""

# Guard: must be a git repo
if ! git -C "$SCRIPT_DIR" rev-parse --git-dir > /dev/null 2>&1; then
  echo -e "${RED}Not a git repository: $SCRIPT_DIR${NC}"
  exit 1
fi

# Step 1: Pull latest
echo "Pulling latest..."
BEFORE=$(git -C "$SCRIPT_DIR" rev-parse HEAD)
git -C "$SCRIPT_DIR" pull origin main
AFTER=$(git -C "$SCRIPT_DIR" rev-parse HEAD)

echo ""

if [ "$BEFORE" = "$AFTER" ]; then
  echo -e "${YELLOW}Already up to date (${AFTER:0:7}).${NC}"
else
  echo -e "${GREEN}Updated: ${BEFORE:0:7} → ${AFTER:0:7}${NC}"
  echo ""
  git -C "$SCRIPT_DIR" log --oneline "${BEFORE}..${AFTER}"
fi

echo ""

# Step 2: Sync to plugin path if different location
if [ "$SCRIPT_DIR" != "$REALM_PLUGIN_PATH" ]; then
  if [ -d "$REALM_PLUGIN_PATH" ]; then
    echo "Syncing skills to plugin path..."
    rsync -a --delete \
      --exclude='.git' \
      --exclude='.DS_Store' \
      --exclude='.realm' \
      "$SCRIPT_DIR/" "$REALM_PLUGIN_PATH/"
    echo -e "${GREEN}✓ $REALM_PLUGIN_PATH synced${NC}"
  else
    echo -e "${YELLOW}Realm plugin not found at: $REALM_PLUGIN_PATH${NC}"
    echo "  Re-run install: /plugin marketplace add $REALM_PLUGIN_PATH"
  fi
else
  echo -e "${GREEN}✓ Installed in-place — git pull is the full update${NC}"
fi

# Step 3: Sync agents to ~/.claude/agents/
AGENTS_SRC="${SCRIPT_DIR}/agents"
AGENTS_DST="$HOME/.claude/agents"
if [ -d "$AGENTS_SRC" ]; then
  mkdir -p "$AGENTS_DST"
  echo "Syncing realm agents to $AGENTS_DST..."
  for agent_file in "$AGENTS_SRC"/*.md; do
    [ -f "$agent_file" ] || continue
    cp "$agent_file" "$AGENTS_DST/"
    echo -e "${GREEN}✓ $(basename "$agent_file")${NC}"
  done
  # Remove renamed agents from previous versions
  for obsolete in realm-manifest-compress realm-manifest-write; do
    if [ -f "$AGENTS_DST/${obsolete}.md" ]; then
      rm -f "$AGENTS_DST/${obsolete}.md"
      echo -e "${YELLOW}  removed obsolete: ${obsolete}.md${NC}"
    fi
  done
fi

# Step 4: Sync Codex native agents to ~/.codex/agents/
CODEX_AGENTS_SRC="${SCRIPT_DIR}/.codex/agents"
CODEX_AGENTS_DST="$HOME/.codex/agents"
if [ -d "$CODEX_AGENTS_SRC" ]; then
  mkdir -p "$CODEX_AGENTS_DST"
  echo "Syncing Codex realm agents to $CODEX_AGENTS_DST..."
  for agent_file in "$CODEX_AGENTS_SRC"/realm-agent-*.toml; do
    [ -f "$agent_file" ] || continue
    cp "$agent_file" "$CODEX_AGENTS_DST/"
    echo -e "${GREEN}✓ $(basename "$agent_file")${NC}"
  done
fi

echo ""

# Step 5: Check caveman dependency
if [ ! -d "$CAVEMAN_PLUGIN_PATH" ]; then
  echo -e "${YELLOW}Warning: caveman plugin not found at $CAVEMAN_PLUGIN_PATH${NC}"
  echo "  realm-recall and realm-status require caveman for compressed output."
  echo "  Install: /plugin marketplace add $CAVEMAN_PLUGIN_PATH"
  echo ""
fi

echo -e "${GREEN}Done.${NC}"
echo ""
echo "Restart Claude Code or Codex sessions to apply skill/agent changes."
echo ""
