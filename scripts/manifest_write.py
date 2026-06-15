#!/usr/bin/env python3
"""
manifest_write.py — deterministic vault-write script for realm-manifest.

Replaces the mechanical steps of realm-agent-write (Steps 0-9) with a stdlib
script. LLM tool-call chain eliminated; the agent becomes a thin wrapper that
invokes this script and handles the one semantic exception (overview.md prose
merge).

Usage:
    python3 manifest_write.py --project-root <abs-path>

Exit codes:
    0  success (warnings allowed)
    1  guard failure (missing state, draft not ready, missing draft file)
    2  unexpected error
"""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone

# Resolve script dir for sibling import
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPTS_DIR)

from realm_lib import (
    DraftNode,
    extract_wikilinks,
    load_state,
    parse_draft,
    parse_yaml_min,
    save_state,
    split_frontmatter,
)


# ---------------------------------------------------------------------------
# Guards (Step 0)
# ---------------------------------------------------------------------------

def run_guards(project_root: str, draft_path: str) -> dict:
    state_path = os.path.join(project_root, ".realm", "realm-state.json")
    if not os.path.exists(state_path):
        print("No realm state. Run /realm-forge first.")
        sys.exit(1)

    state = load_state(project_root)

    if not os.path.exists(draft_path):
        print(f"Draft file missing: {draft_path}")
        sys.exit(1)

    return state


# ---------------------------------------------------------------------------
# Validation (Step 2)
# ---------------------------------------------------------------------------

_VALID_TYPES = {"decision", "function", "class", "discovery", "system"}
_CAMEL_TRUNC_RE = re.compile(r'\b[A-Z][a-z]+[A-Z]$')


def validate_nodes(nodes: list) -> tuple:
    warnings = []
    for node in nodes:
        fm, content = split_frontmatter(node.body)
        fields = parse_yaml_min(fm) if fm else {}
        path = node.rel_path

        if "id" not in fields:
            warnings.append(f"  WARN  {path}: missing 'id' in frontmatter")

        node_type = str(fields.get("type", "")).lower()
        if node_type and node_type not in _VALID_TYPES:
            warnings.append(f"  WARN  {path}: unknown type '{node_type}'")

        if "Compressed:" not in node.body and "## Compressed" not in node.body:
            warnings.append(f"  WARN  {path}: no 'Compressed:' section found")

        if node_type in ("function", "class"):
            if not extract_wikilinks(node.body):
                warnings.append(f"  WARN  {path}: function/class node has no [[wikilinks]]")

        if node_type == "decision":
            if "## Full Decision" not in node.body:
                warnings.append(f"  WARN  {path}: decision node missing '## Full Decision' section")
            else:
                for sub in ("Context", "Decision", "Consequences"):
                    if sub not in node.body:
                        warnings.append(f"  WARN  {path}: decision '## Full Decision' missing '{sub}'")

        if _CAMEL_TRUNC_RE.search(content):
            warnings.append(f"  WARN  {path}: possible truncated CamelCase identifier")

    return warnings


# ---------------------------------------------------------------------------
# Step 4 — Write node documents to vault
# ---------------------------------------------------------------------------

def _merge_update(existing: str, new_body: str, rel_path: str) -> str:
    """Append new sections to existing file; preserve all existing content."""
    _, new_content = split_frontmatter(new_body)
    # Extract section headers from new content that don't exist in existing
    new_sections = re.split(r'\n(?=## )', new_content)
    additions = []
    for section in new_sections:
        header_match = re.match(r'## (.+)', section.strip())
        if header_match:
            header = header_match.group(1)
            if f"## {header}" not in existing:
                additions.append(section.strip())
        elif section.strip() and not existing.endswith(section.strip()):
            additions.append(section.strip())

    if additions:
        return existing.rstrip() + "\n\n" + "\n\n".join(additions) + "\n"
    return existing


def _append_architecture_rows(existing: str, new_body: str) -> str:
    """Append new table rows to architecture.md; never remove existing rows."""
    new_rows = re.findall(r'^\|[^|]+\|[^|]+\|', new_body, re.MULTILINE)
    existing_rows = set(re.findall(r'^\|[^|]+\|[^|]+\|', existing, re.MULTILINE))
    additions = [r for r in new_rows if r not in existing_rows]
    if not additions:
        return existing
    return existing.rstrip() + "\n" + "\n".join(additions) + "\n"


def _inject_links(body: str, links_line: str) -> str:
    """Append any wikilinks from the draft `links:` header that aren't already in the body."""
    if not links_line:
        return body
    missing = [lnk for lnk in extract_wikilinks(links_line) if f"[[{lnk}]]" not in body]
    if not missing:
        return body
    refs = "  ".join(f"[[{lnk}]]" for lnk in missing)
    return body.rstrip() + f"\n\n## References\n{refs}\n"


def check_conflicts(nodes: list, project_dir: str) -> list:
    """Return list of rel_paths for status=new nodes whose files already exist."""
    conflicts = []
    for node in nodes:
        if node.status == "new":
            full_path = os.path.join(project_dir, node.rel_path)
            if os.path.exists(full_path):
                conflicts.append(node.rel_path)
    return conflicts


def write_nodes(nodes: list, project_dir: str, project_root: str, overwrite: bool = False) -> dict:
    results = {"wrote": 0, "merged": 0, "skipped": 0, "deferred": 0, "written_nodes": []}
    written_info = []  # [(id, type, rel_path)]

    for node in nodes:
        rel = node.rel_path
        full_path = os.path.join(project_dir, rel)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        fm, _ = split_frontmatter(node.body)
        fields = parse_yaml_min(fm) if fm else {}
        node_id = fields.get("id", "")
        node_type = str(fields.get("type", ""))

        # overview.md prose merge is semantic — defer to agent
        if rel in ("overview.md",) and node.status == "update":
            pending_path = os.path.join(project_root, ".realm", "pending-prose-merge.md")
            with open(pending_path, "w", encoding="utf-8") as f:
                f.write(f"# Pending Prose Merge\n\n## Target\n{full_path}\n\n## Patch\n\n{node.body}\n")
            print(f"  DEFER   {rel} (prose merge → .realm/pending-prose-merge.md)")
            results["deferred"] += 1
            continue

        if node.status == "new":
            if os.path.exists(full_path):
                if not overwrite:
                    print(f"  SKIP    {rel} (exists)")
                    results["skipped"] += 1
                    continue
                print(f"  OVERWRITE {rel}  (id: {node_id})")
            body_to_write = _inject_links(node.body, node.links)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(body_to_write + "\n")
            print(f"  WROTE   {rel}  (id: {node_id})")
            results["wrote"] += 1

        elif node.status == "update":
            if not os.path.exists(full_path):
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(node.body + "\n")
                print(f"  WROTE   {rel}  (id: {node_id})")
                results["wrote"] += 1
            else:
                with open(full_path, "r", encoding="utf-8") as f:
                    existing = f.read()

                if rel == "architecture.md":
                    merged = _append_architecture_rows(existing, node.body)
                else:
                    merged = _merge_update(existing, node.body, rel)

                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(merged)
                print(f"  MERGED  {rel}")
                results["merged"] += 1

        if node_id and node_type:
            written_info.append((node_id, node_type, rel, fields))

    results["written_nodes"] = written_info
    return results


# ---------------------------------------------------------------------------
# Step 5 — ADR index + backlinks
# ---------------------------------------------------------------------------

def _adr_row(node_id: str, fields: dict) -> str:
    title = fields.get("title", node_id)
    status = fields.get("status", "proposed")
    date = fields.get("updated", fields.get("created", ""))
    return f"| [[{node_id}]] | {title} | {status} | {date} |"


def update_adr_index(written_nodes: list, project_dir: str) -> int:
    decision_nodes = [(nid, fields) for nid, ntype, _, fields in written_nodes if ntype == "decision"]
    if not decision_nodes:
        return 0

    index_path = os.path.join(project_dir, "decisions", "ADR-000-index.md")
    os.makedirs(os.path.dirname(index_path), exist_ok=True)

    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            existing = f.read()
    else:
        existing = "# ADR Index\n\n| ID | Title | Status | Date |\n|---|---|---|---|\n"

    added = 0
    for node_id, fields in decision_nodes:
        if f"[[{node_id}]]" not in existing:
            row = _adr_row(node_id, fields)
            existing = existing.rstrip() + "\n" + row + "\n"
            added += 1

    # sort table rows by ID (lines matching | [[...]])
    header_match = re.search(r'(\|[-| ]+\n)', existing)
    if header_match:
        split_pos = header_match.end()
        header_part = existing[:split_pos]
        rows_part = existing[split_pos:]
        row_lines = [l for l in rows_part.splitlines() if l.startswith("|")]
        other_lines = [l for l in rows_part.splitlines() if not l.startswith("|")]
        row_lines.sort()
        existing = header_part + "\n".join(row_lines) + "\n"
        if other_lines:
            existing += "\n".join(other_lines) + "\n"

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(existing)

    return added


def update_backlinks(written_nodes: list, project_dir: str) -> int:
    updated = 0
    for node_id, node_type, rel_path, fields in written_nodes:
        if node_type not in ("function", "class"):
            continue

        class_name = fields.get("class", "")
        depends_on = fields.get("depends_on", [])
        if isinstance(depends_on, str):
            depends_on = extract_wikilinks(depends_on)
        called_by = fields.get("called_by", [])
        if isinstance(called_by, str):
            called_by = extract_wikilinks(called_by)

        # function → add to parent class's ## Methods
        if node_type == "function" and class_name:
            class_path = os.path.join(project_dir, "classes", f"{class_name}.md")
            if os.path.exists(class_path):
                with open(class_path, "r", encoding="utf-8") as f:
                    content = f.read()
                link = f"- [[{node_id}]]"
                if link not in content:
                    if "## Methods" in content:
                        content = content.replace("## Methods\n", f"## Methods\n{link}\n")
                    else:
                        content = content.rstrip() + f"\n\n## Methods\n{link}\n"
                    with open(class_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    updated += 1

        # depends_on → add to dep's ## Dependents
        for dep_id in depends_on:
            _append_backlink_to(dep_id, node_id, "## Dependents", project_dir)
            updated += 1

        # called_by → add to caller's ## Called By / ## Dependents
        for caller_id in called_by:
            _append_backlink_to(caller_id, node_id, "## Called By", project_dir)
            updated += 1

    return updated


def _append_backlink_to(target_id: str, source_id: str, section: str, project_dir: str) -> None:
    for subdir in ("functions", "classes", "systems", "decisions"):
        candidate = os.path.join(project_dir, subdir, f"{target_id}.md")
        if os.path.exists(candidate):
            with open(candidate, "r", encoding="utf-8") as f:
                content = f.read()
            link = f"- [[{source_id}]]"
            if link not in content:
                if section in content:
                    content = content.replace(f"{section}\n", f"{section}\n{link}\n")
                else:
                    content = content.rstrip() + f"\n\n{section}\n{link}\n"
                with open(candidate, "w", encoding="utf-8") as f:
                    f.write(content)
            break


# ---------------------------------------------------------------------------
# Step 6 — Session log
# ---------------------------------------------------------------------------

def write_session_log(session_node: "DraftNode | None", project_dir: str) -> str:
    if session_node is None:
        return ""

    rel = session_node.rel_path.lstrip("/")
    full_path = os.path.join(project_dir, rel)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    body = session_node.body
    # ensure required frontmatter fields exist
    fm, content = split_frontmatter(body)
    if not fm:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        fm = f"tags: [session]\ndate: {today}\nproject: unknown"
        body = f"---\n{fm}\n---\n\n{body}"

    if os.path.exists(full_path):
        with open(full_path, "a", encoding="utf-8") as f:
            f.write("\n---\n\n" + content)
    else:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(body + "\n")

    return rel


# ---------------------------------------------------------------------------
# Step 7 — Update realm-state.json
# ---------------------------------------------------------------------------

def update_state(state: dict, written_nodes: list, deferred_count: int, project_root: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    docs = state.setdefault("docs", {})

    for node_id, node_type, rel_path, _ in written_nodes:
        docs[rel_path] = {"status": "committed", "updated": now}

    state.setdefault("manifest", {})["lastRun"] = now

    project_dir = state.get("projectDir", "")
    if project_dir and os.path.isdir(project_dir):
        state["nodeIndex"] = _build_node_index(project_dir)

    save_state(state, project_root)


# ---------------------------------------------------------------------------
# Step 8 — Archive the draft
# ---------------------------------------------------------------------------

def archive_draft(project_root: str, draft_path: str, slug: str = "") -> str:
    archive_dir = os.path.join(project_root, ".realm", "archive")
    os.makedirs(archive_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    prefix = slug.replace("/", "-") + "-" if slug else ""
    archive_path = os.path.join(archive_dir, f"{prefix}{ts}-draft.md")
    shutil.move(draft_path, archive_path)
    return os.path.relpath(archive_path, project_root)


# ---------------------------------------------------------------------------
# pendingDrafts management (C1)
# ---------------------------------------------------------------------------

def push_draft(project_root: str, draft_path: str, source: str, slug: str = None) -> None:
    state = load_state(project_root)
    pending = state.setdefault("pendingDrafts", [])
    for entry in pending:
        if entry.get("path") == draft_path:
            print(f"Already staged: {draft_path}")
            return
    entry = {
        "source": source,
        "slug": slug,
        "path": draft_path,
        "created": datetime.now(timezone.utc).isoformat(),
    }
    pending.append(entry)
    save_state(state, project_root)
    print(f"Staged: {draft_path}  (source: {source})")


def remove_draft(project_root: str, draft_path: str) -> None:
    state = load_state(project_root)
    pending = state.get("pendingDrafts", [])
    before = len(pending)
    state["pendingDrafts"] = [e for e in pending if e.get("path") != draft_path]
    save_state(state, project_root)
    removed = before - len(state["pendingDrafts"])
    print(f"Removed: {removed} draft(s) matching {draft_path}")


def list_drafts(project_root: str) -> None:
    state = load_state(project_root)
    pending = state.get("pendingDrafts", [])
    if not pending:
        print("No pending drafts.")
        return
    for i, e in enumerate(pending, 1):
        display = e.get("slug") or e.get("source", "?")
        print(f"  [{i}] {display}  {e.get('source')}  {e.get('path')}  {e.get('created', '')[:10]}")


# ---------------------------------------------------------------------------
# nodeIndex (M3)
# ---------------------------------------------------------------------------

def _build_node_index(project_dir: str) -> dict:
    """Scan vault dirs → id→path index + per-subdir counts."""
    counts = {}
    ids = {}
    for subdir in ("decisions", "functions", "classes", "systems", "discoveries", "sessions"):
        d = os.path.join(project_dir, subdir)
        if not os.path.isdir(d):
            counts[subdir] = 0
            continue
        files = [f for f in os.listdir(d) if f.endswith(".md") and not f.startswith("_")]
        counts[subdir] = len(files)
        for fname in files:
            ids[fname[:-3]] = f"{subdir}/{fname}"
    return {"counts": counts, "ids": ids, "updatedAt": datetime.now(timezone.utc).isoformat()}


# ---------------------------------------------------------------------------
# Step 9 — Summary
# ---------------------------------------------------------------------------

def print_summary(
    meta,
    validated: int,
    warnings: list,
    write_results: dict,
    backlinks_updated: int,
    adr_entries: int,
    session_rel: str,
    archive_rel: str,
    project_dir: str,
    has_prose_merge: bool,
) -> None:
    wn = write_results["written_nodes"]
    decisions  = sum(1 for _, t, _, _ in wn if t == "decision")
    functions  = sum(1 for _, t, _, _ in wn if t == "function")
    classes    = sum(1 for _, t, _, _ in wn if t == "class")
    discoveries = sum(1 for _, t, _, _ in wn if t == "discovery")

    print()
    print("realm-agent-write complete")
    print(f"  vault: {project_dir}")
    print()
    print(f"  validated: {validated} nodes  warnings: {len(warnings)}")
    print()
    print("  nodes written:")
    print(f"    decisions:    {decisions} new")
    print(f"    functions:    {functions} new")
    print(f"    classes:      {classes} new")
    print(f"    discoveries:  {discoveries} new")
    print(f"    updates:      {write_results['merged']} (overview/architecture merged)")
    print(f"    skipped:      {write_results['skipped']} (already existed)")
    print()
    print(f"  backlinks updated: {backlinks_updated} nodes")
    print(f"  decision index:    {adr_entries} entries")
    if session_rel:
        print(f"  session log:       {session_rel}")
    print(f"  draft archived:    {archive_rel}")
    if has_prose_merge:
        print()
        print("  prose merge pending: .realm/pending-prose-merge.md")
        print("  → agent will apply overview.md patch and remove the pending file")
    print()
    print("Next: /realm-status to verify  |  /realm-recall <topic> for context  |  /realm-phase after next milestone")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="realm manifest writer")
    parser.add_argument("--project-root", required=True, help="Absolute path to project root")
    parser.add_argument(
        "--draft-path",
        default=None,
        help="Absolute path to draft file (vault-write) or relative path (draft management)",
    )
    parser.add_argument("--slug", default="", help="Canvas slug for archive naming or push-draft slug")
    parser.add_argument("--source", choices=["plan", "convey"], help="Draft source (required with --push-draft)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing status=new nodes instead of skipping")
    mgmt = parser.add_mutually_exclusive_group()
    mgmt.add_argument("--push-draft", action="store_true", help="Stage a draft into pendingDrafts")
    mgmt.add_argument("--remove-draft", action="store_true", help="Remove a draft from pendingDrafts by path")
    mgmt.add_argument("--list-drafts", action="store_true", help="List all pending drafts")
    mgmt.add_argument("--check-conflicts", action="store_true", help="Dry-run: list status=new nodes whose files already exist, no writes")
    args = parser.parse_args()

    project_root = os.path.abspath(args.project_root)

    # draft management modes (C1)
    if args.list_drafts:
        list_drafts(project_root)
        return

    if args.check_conflicts:
        if not args.draft_path:
            print("ERROR: --check-conflicts requires --draft-path", file=sys.stderr)
            sys.exit(1)
        draft_path = args.draft_path
        state = run_guards(project_root, draft_path)
        vault_path = state.get("vaultPath", "")
        project_slug = state.get("projectSlug", "")
        project_dir = state.get("projectDir", os.path.join(vault_path, "projects", project_slug))
        with open(draft_path, "r", encoding="utf-8") as f:
            draft_text = f.read()
        draft = parse_draft(draft_text)
        conflicts = check_conflicts(draft.nodes, project_dir)
        for c in conflicts:
            print(f"CONFLICT: {c}")
        print(f"conflicts: {len(conflicts)}")
        return

    if args.push_draft:
        if not args.draft_path:
            print("ERROR: --push-draft requires --draft-path", file=sys.stderr)
            sys.exit(1)
        if not args.source:
            print("ERROR: --push-draft requires --source (plan|convey)", file=sys.stderr)
            sys.exit(1)
        push_draft(project_root, args.draft_path, args.source, args.slug or None)
        return

    if args.remove_draft:
        if not args.draft_path:
            print("ERROR: --remove-draft requires --draft-path", file=sys.stderr)
            sys.exit(1)
        remove_draft(project_root, args.draft_path)
        return

    # vault-write mode (original flow)
    draft_path = args.draft_path or os.path.join(project_root, ".realm", "manifest-draft.md")
    slug = args.slug or ""

    # Step 0 — guards
    state = run_guards(project_root, draft_path)
    vault_path = state.get("vaultPath", "")
    project_slug = state.get("projectSlug", "")
    project_dir = state.get("projectDir", os.path.join(vault_path, "projects", project_slug))

    # Step 1 — parse draft
    with open(draft_path, "r", encoding="utf-8") as f:
        draft_text = f.read()

    draft = parse_draft(draft_text)
    all_nodes = draft.nodes

    # Step 2 — validate (Step 3 removed — scan output authoritative)
    warnings = validate_nodes(all_nodes)
    print(f"validate: {len(all_nodes)} nodes  warnings: {len(warnings)}")
    for w in warnings:
        print(w)

    # Step 4 — write nodes
    write_results = write_nodes(all_nodes, project_dir, project_root, overwrite=args.overwrite)
    has_prose_merge = write_results["deferred"] > 0

    # Step 5 — ADR index + backlinks
    adr_entries = update_adr_index(write_results["written_nodes"], project_dir)
    backlinks_updated = update_backlinks(write_results["written_nodes"], project_dir)

    # Step 6 — session log
    session_rel = write_session_log(draft.session_log, project_dir)

    # Step 7 — update state
    update_state(state, write_results["written_nodes"], write_results["deferred"], project_root)

    # Step 8 — archive draft
    archive_rel = archive_draft(project_root, draft_path, slug)

    # Step 9 — summary
    print_summary(
        meta=draft.meta,
        validated=len(all_nodes),
        warnings=warnings,
        write_results=write_results,
        backlinks_updated=backlinks_updated,
        adr_entries=adr_entries,
        session_rel=session_rel,
        archive_rel=archive_rel,
        project_dir=project_dir,
        has_prose_merge=has_prose_merge,
    )


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
