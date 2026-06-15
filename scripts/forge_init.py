#!/usr/bin/env python3
"""
forge_init.py — deterministic vault bootstrap for realm-forge.

Replaces mechanical steps in realm-agent-forge (mkdir, gitignore update,
doc scan, realm-state.json write). Agent becomes a thin wrapper handling
only semantic prose seeds (overview.md, CLAUDE.md content).

Usage:
    python3 forge_init.py --project-root <abs> --vault-path <abs> --project-slug <slug>

Exit codes:
    0  success
    1  guard failure
    2  unexpected error
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPTS_DIR)
from realm_lib import save_state


VAULT_SUBDIRS = [
    "decisions", "functions", "classes", "systems", "discoveries", "sessions",
]


def scaffold_dirs(project_dir: str, vault_path: str) -> list:
    """Create vault dirs and _templates dir. Return list of (path, status)."""
    results = []
    dirs = [os.path.join(project_dir, s) for s in VAULT_SUBDIRS]
    dirs.append(os.path.join(vault_path, "_templates"))
    for d in dirs:
        existed = os.path.isdir(d)
        os.makedirs(d, exist_ok=True)
        results.append((d, "EXISTS " if existed else "CREATED"))
    return results


def update_gitignore(project_root: str) -> str:
    """Append .realm/ to .gitignore if not present."""
    gi_path = os.path.join(project_root, ".gitignore")
    if os.path.exists(gi_path):
        with open(gi_path, "r", encoding="utf-8") as f:
            content = f.read()
        if ".realm/" in content:
            return "already present"
        with open(gi_path, "a", encoding="utf-8") as f:
            f.write("\n.realm/\n")
    else:
        with open(gi_path, "w", encoding="utf-8") as f:
            f.write(".realm/\n")
    return "updated"


def ensure_realm_dirs(project_root: str) -> None:
    """Create .realm/ subdirs if missing."""
    for d in [
        os.path.join(project_root, ".realm"),
        os.path.join(project_root, ".realm", "plans"),
        os.path.join(project_root, ".realm", "archive"),
    ]:
        os.makedirs(d, exist_ok=True)


def scan_existing_docs(project_dir: str) -> dict:
    """Scan projectDir recursively for .md files. Return docs registry."""
    docs = {}
    now = datetime.now(timezone.utc).isoformat()
    if not os.path.isdir(project_dir):
        return docs
    for root, _, files in os.walk(project_dir):
        for fname in files:
            if not fname.endswith(".md") or fname.startswith("_"):
                continue
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, project_dir).replace(os.sep, "/")
            try:
                mtime = os.path.getmtime(full)
                updated = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
            except OSError:
                updated = now
            docs[rel] = {"status": "committed", "updated": updated}
    return docs


def write_state(
    project_root: str,
    vault_path: str,
    project_slug: str,
    project_dir: str,
    docs: dict,
) -> str:
    """Write/merge realm-state.json. Idempotent — preserves pendingDrafts and history."""
    state_path = os.path.join(project_root, ".realm", "realm-state.json")
    if os.path.exists(state_path):
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)
        state["vaultPath"] = vault_path
        state["projectSlug"] = project_slug
        state["projectDir"] = project_dir
        state.setdefault("phase", {}).setdefault("lastRun", None)
        state["phase"].setdefault("draftReady", False)
        state.setdefault("manifest", {}).setdefault("lastRun", None)
        state.setdefault("pendingDrafts", [])
        existing_docs = state.setdefault("docs", {})
        for k, v in docs.items():
            if k not in existing_docs:
                existing_docs[k] = v
    else:
        state = {
            "vaultPath": vault_path,
            "projectSlug": project_slug,
            "projectDir": project_dir,
            "phase": {"lastRun": None, "draftReady": False},
            "manifest": {"lastRun": None},
            "pendingDrafts": [],
            "docs": docs,
        }
    save_state(state, project_root)
    return state_path


def main() -> None:
    parser = argparse.ArgumentParser(description="realm vault bootstrap")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--project-slug", required=True)
    args = parser.parse_args()

    project_root = os.path.abspath(args.project_root)
    vault_path = os.path.abspath(args.vault_path)
    project_slug = args.project_slug
    project_dir = os.path.join(vault_path, "projects", project_slug)

    # Step 1: scaffold vault dirs
    dir_results = scaffold_dirs(project_dir, vault_path)
    for path, status in dir_results:
        print(f"  {status} {path}")

    # Step 2: ensure .realm/ dirs
    ensure_realm_dirs(project_root)

    # Step 3: update .gitignore
    gi_result = update_gitignore(project_root)
    print(f"  .gitignore: {gi_result}")

    # Step 4: scan existing docs
    docs = scan_existing_docs(project_dir)
    print(f"  vault docs found: {len(docs)}")

    # Step 5: write/merge realm-state.json
    state_path = write_state(project_root, vault_path, project_slug, project_dir, docs)
    print(f"  state: {state_path}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
