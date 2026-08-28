#!/usr/bin/env python3
"""
forge_init.py — deterministic vault bootstrap for realm-forge.

Owns all deterministic bootstrap work: directories, templates, host guidance,
overview, document scan, and realm-state.json.

Usage:
    python3 forge_init.py --project-root <abs> --vault-path <abs> --project-slug <slug> --host <claude|cursor|codex|gemini>

Exit codes:
    0  success
    1  guard failure
    2  unexpected error
"""

import argparse
import json
import os
import sys

VAULT_SUBDIRS = [
    "decisions", "functions", "classes", "systems", "discoveries", "sessions",
    "orchestration",
]


def save_state(state: dict, project_root: str) -> None:
    """Atomically write the project Realm state without external dependencies."""
    state_path = os.path.join(project_root, ".realm", "realm-state.json")
    temporary_path = state_path + ".tmp"
    with open(temporary_path, "w", encoding="utf-8") as state_file:
        json.dump(state, state_file, indent=2)
        state_file.write("\n")
    os.replace(temporary_path, state_path)


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


_NODE_TEMPLATES = {
    "Decision-Node.md": """---
id: ADR-<NNN>-<slug>
type: decision
status: proposed
tags: [decision]
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---

Compressed: <one-line decision summary>

## Full Decision

### Context
<why this decision was needed>

### Decision
<what was decided>

### Consequences
<tradeoffs, follow-on work>

rejected_alternatives: <alternatives considered and why rejected>
""",
    "Function-Node.md": """---
id: <function-name>
type: function
tags: [function]
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---

Compressed: <one-line summary of what this function does>

Signature: `<signature>`

Related: [[<caller-or-class>]]
""",
    "Class-Node.md": """---
id: <ClassName>
type: class
tags: [class]
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---

Compressed: <one-line summary of what this class does>

Related: [[<related-node>]]
""",
    "Discovery-Note.md": """---
id: <discovery-slug>
type: discovery
tags: [discovery]
created: <YYYY-MM-DD>
---

Compressed: <one-line summary of the discovery>

<details, evidence, links to source>
""",
    "Session-Log.md": """---
tags: [session]
date: <YYYY-MM-DD>
project: <project-slug>
---

## Session Summary
<what happened this session>

## Nodes Touched
<[[node-id]] links>
""",
}


def write_templates(vault_path: str) -> list:
    """Write standard node templates to _templates/ if missing. Return (path, status) list."""
    templates_dir = os.path.join(vault_path, "_templates")
    os.makedirs(templates_dir, exist_ok=True)
    results = []
    for fname, content in _NODE_TEMPLATES.items():
        path = os.path.join(templates_dir, fname)
        if os.path.exists(path):
            results.append((path, "EXISTS "))
            continue
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        results.append((path, "CREATED"))
    return results


def write_adr_index(project_dir: str) -> str:
    """Write decisions/ADR-000-index.md stub if missing."""
    index_path = os.path.join(project_dir, "decisions", "ADR-000-index.md")
    if os.path.exists(index_path):
        return "already existed"
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# ADR Index\n\n| ID | Title | Status | Date |\n|---|---|---|---|\n")
    return "created"


def write_host_anchor(project_root: str, vault_path: str, project_dir: str, project_name: str, description: str, host: str) -> tuple:
    """Write the active host's project guidance file if missing."""
    relative_paths = {
        "claude": os.path.join(".claude", "CLAUDE.md"),
        "cursor": "AGENTS.md",
        "codex": "AGENTS.md",
        "gemini": "GEMINI.md",
    }
    relative_path = relative_paths[host]
    anchor_path = os.path.join(project_root, relative_path)
    if os.path.exists(anchor_path):
        return relative_path, "already existed"
    os.makedirs(os.path.dirname(anchor_path), exist_ok=True)
    rel_project_dir = os.path.relpath(project_dir, project_root)
    content = f"""# {project_name}

{description}

## Realm Vault

- Vault: `{vault_path}`
- Project docs: `{rel_project_dir}`
- Overview: `{rel_project_dir}/overview.md`
- Architecture: `{rel_project_dir}/architecture.md`
- Decisions: `{rel_project_dir}/decisions/`
- Sessions: `{rel_project_dir}/sessions/`
"""
    with open(anchor_path, "w", encoding="utf-8") as f:
        f.write(content)
    return relative_path, "created"


def write_overview(project_dir: str, project_root: str, project_name: str, description: str, stack: str, milestones: str) -> str:
    """Seed projectDir/overview.md if missing."""
    overview_path = os.path.join(project_dir, "overview.md")
    if os.path.exists(overview_path):
        return "already existed"
    stack_block = stack.strip() or "<tech stack>"
    milestones_block = milestones.strip() or "<milestones>"
    content = f"""---
tags: [project]
status: active
repo: {project_root}
---

# {project_name}

{description}

## Stack

{stack_block}

## Milestones

{milestones_block}

## Knowledge

- [[architecture]]
- [[decisions/ADR-000-index]]

## Key Source Files

<links to frequently-touched source files, added over time>
"""
    with open(overview_path, "w", encoding="utf-8") as f:
        f.write(content)
    return "created"


def write_state(
    project_root: str,
    vault_path: str,
    project_slug: str,
    project_dir: str,
) -> str:
    """Write/merge realm-state.json and remove retired pipeline state."""
    state_path = os.path.join(project_root, ".realm", "realm-state.json")
    if os.path.exists(state_path):
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)
        state["vaultPath"] = vault_path
        state["projectSlug"] = project_slug
        state["projectDir"] = project_dir
        for retired_key in ("phase", "manifest", "pendingDrafts", "nodeIndex", "docs"):
            state.pop(retired_key, None)
    else:
        state = {
            "vaultPath": vault_path,
            "projectSlug": project_slug,
            "projectDir": project_dir,
        }
    save_state(state, project_root)
    return state_path


def main() -> None:
    parser = argparse.ArgumentParser(description="realm vault bootstrap")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--project-slug", required=True)
    parser.add_argument("--project-name", default=None, help="Defaults to project-slug")
    parser.add_argument(
        "--host",
        choices=("claude", "cursor", "codex", "gemini"),
        default="claude",
    )
    parser.add_argument("--description", default="<one-line project description>")
    parser.add_argument("--stack", default="", help="Tech stack summary, freeform")
    parser.add_argument("--milestones", default="", help="Milestone list, freeform")
    args = parser.parse_args()

    project_root = os.path.abspath(args.project_root)
    vault_path = os.path.abspath(args.vault_path)
    project_slug = args.project_slug
    project_name = args.project_name or project_slug
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

    # Step 4: write node templates
    for path, status in write_templates(vault_path):
        print(f"  {status} {path}")

    # Step 5: write ADR index stub
    adr_result = write_adr_index(project_dir)
    print(f"  ADR index: {adr_result}")

    # Step 6: write active-host guidance anchor
    anchor_path, anchor_result = write_host_anchor(
        project_root, vault_path, project_dir, project_name, args.description, args.host
    )
    print(f"  {anchor_path} anchor: {anchor_result}")

    # Step 7: seed overview.md
    overview_result = write_overview(project_dir, project_root, project_name, args.description, args.stack, args.milestones)
    print(f"  overview.md: {overview_result}")

    # Step 8: write/merge realm-state.json
    state_path = write_state(project_root, vault_path, project_slug, project_dir)
    print(f"  state: {state_path}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
