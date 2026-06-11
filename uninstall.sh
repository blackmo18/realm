#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Realm Uninstall${NC}"
echo "================"
echo ""

# Check if caveman and realm plugins exist
CAVEMAN_PATH="$HOME/.claude/plugins/marketplaces/caveman"
REALM_PATH="$HOME/.claude/plugins/marketplaces/realm"

FOUND_PLUGINS=false

if [ -d "$CAVEMAN_PATH" ]; then
  echo -e "${YELLOW}Found caveman plugin at:${NC} $CAVEMAN_PATH"
  FOUND_PLUGINS=true
fi

if [ -d "$REALM_PATH" ]; then
  echo -e "${YELLOW}Found realm plugin at:${NC} $REALM_PATH"
  FOUND_PLUGINS=true
fi

if [ "$FOUND_PLUGINS" = false ]; then
  echo -e "${YELLOW}No plugins found to uninstall${NC}"
fi

echo ""
read -p "Uninstall caveman plugin? (y/n) " -n 1 -r CAVEMAN_UNINSTALL
echo ""

read -p "Uninstall realm plugin? (y/n) " -n 1 -r REALM_UNINSTALL
echo ""

# Check for local project state
if [ -d ".realm" ]; then
  echo -e "${YELLOW}Found local realm state at:${NC} .realm/"
  read -p "Remove local realm state (.realm directory)? (y/n) " -n 1 -r REALM_STATE_REMOVE
  echo ""
fi

if [ -f ".claude/CLAUDE.md" ]; then
  echo -e "${YELLOW}Found project anchor at:${NC} .claude/CLAUDE.md"
  read -p "Remove project anchor (.claude/CLAUDE.md)? (y/n) " -n 1 -r CLAUDE_ANCHOR_REMOVE
  echo ""
fi

# Confirm before proceeding
echo -e "${RED}⚠️  This will remove:${NC}"
[[ $CAVEMAN_UNINSTALL =~ ^[Yy]$ ]] && echo "  - Caveman plugin ($CAVEMAN_PATH)"
[[ $REALM_UNINSTALL =~ ^[Yy]$ ]] && echo "  - Realm plugin ($REALM_PATH)"
[[ $REALM_STATE_REMOVE =~ ^[Yy]$ ]] && echo "  - Local realm state (.realm/)"
[[ $CLAUDE_ANCHOR_REMOVE =~ ^[Yy]$ ]] && echo "  - Project anchor (.claude/CLAUDE.md)"

echo ""
read -p "Continue with uninstall? (y/n) " -n 1 -r CONFIRM
echo ""

if [[ ! $CONFIRM =~ ^[Yy]$ ]]; then
  echo -e "${YELLOW}Uninstall cancelled${NC}"
  exit 0
fi

echo ""
echo -e "${GREEN}Uninstalling...${NC}"

# Remove caveman plugin
if [[ $CAVEMAN_UNINSTALL =~ ^[Yy]$ ]]; then
  if [ -d "$CAVEMAN_PATH" ]; then
    rm -rf "$CAVEMAN_PATH"
    echo -e "${GREEN}✓ Removed caveman plugin${NC}"
  fi
fi

# Remove realm plugin
if [[ $REALM_UNINSTALL =~ ^[Yy]$ ]]; then
  if [ -d "$REALM_PATH" ]; then
    rm -rf "$REALM_PATH"
    echo -e "${GREEN}✓ Removed realm plugin${NC}"
  fi
fi

# Remove local realm state
if [[ $REALM_STATE_REMOVE =~ ^[Yy]$ ]]; then
  if [ -d ".realm" ]; then
    rm -rf ".realm"
    echo -e "${GREEN}✓ Removed local realm state (.realm/)${NC}"
  fi
fi

# Remove project anchor
if [[ $CLAUDE_ANCHOR_REMOVE =~ ^[Yy]$ ]]; then
  if [ -f ".claude/CLAUDE.md" ]; then
    rm -f ".claude/CLAUDE.md"
    echo -e "${GREEN}✓ Removed project anchor (.claude/CLAUDE.md)${NC}"
  fi
fi

echo ""
echo -e "${GREEN}Uninstall complete!${NC}"
echo ""
echo "Notes:"
echo "  - Obsidian vault nodes remain unchanged (at your vault root)"
echo "  - To remove vault nodes, delete the vault directory manually"
echo "  - Realm skills will no longer be available in Claude Code"
echo ""
