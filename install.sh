#!/bin/bash
set -euo pipefail

# Local clones and remote curl|bash installs both delegate to bin/install.js so
# installation behavior has one authoritative implementation.
SCRIPT_DIR=""
if [ -n "${BASH_SOURCE[0]-}" ]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || true)"
fi
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/bin/install.js" ]; then
  exec node "$SCRIPT_DIR/bin/install.js" "$@"
fi

REPO_SLUG="blackmo18/realm"
ARGS=("$@")
for ((index = 0; index < ${#ARGS[@]}; index += 1)); do
  if [ "${ARGS[$index]}" = "--repo" ] && [ $((index + 1)) -lt ${#ARGS[@]} ]; then
    REPO_SLUG="${ARGS[$((index + 1))]}"
  fi
done

if ! command -v git >/dev/null 2>&1; then
  echo "git is required to install Realm remotely." >&2
  exit 1
fi
if ! command -v node >/dev/null 2>&1; then
  echo "Node.js is required to install Realm remotely." >&2
  exit 1
fi

BOOTSTRAP_DIR="$(mktemp -d)"
trap 'rm -rf "$BOOTSTRAP_DIR"' EXIT
git clone --depth 1 "https://github.com/${REPO_SLUG}.git" "$BOOTSTRAP_DIR/realm" >/dev/null 2>&1
node "$BOOTSTRAP_DIR/realm/bin/install.js" "${ARGS[@]}"
