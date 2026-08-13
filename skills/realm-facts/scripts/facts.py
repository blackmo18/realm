#!/usr/bin/env python3
"""Fact node lifecycle owner for realm-facts.

All mechanical work lives here: fact-file parsing/rendering, schema
validation, index/graph generation, link resolution, status transitions,
and the factsRepo pointer in a product repo's realm-state.json. The
SKILL.md layer never hand-edits a fact file, facts-index.json,
facts-graph.json, or realm-state.json — it only calls this CLI and reads
its stdout. The two genuinely semantic steps (interviewing the user for a
new fact's content, judging whether a compressed summary is agent-useful)
stay in the skill; everything else is here.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

FACT_STATUSES = {"draft", "review", "active", "deprecated"}
ID_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
MAX_COMPRESSED_CHARS = 400
FRONTMATTER_ORDER = (
    "id", "domain", "title", "status", "owners", "reviewers", "tags",
    "evidence", "related", "depends_on", "supersedes", "created", "updated",
)
LIST_FIELDS = ("owners", "reviewers", "tags", "evidence", "related", "depends_on")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Vendored from scripts/realm_lib.py (not installed alongside skills/, so the
# two helpers this script needs are copied here rather than imported).
# ---------------------------------------------------------------------------

def split_frontmatter(body: str) -> tuple[str, str]:
    lines = body.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", body
    end = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end = idx
            break
    if end is None:
        return "", body
    yaml_text = "\n".join(lines[1:end])
    content = "\n".join(lines[end + 1:]).lstrip("\n")
    return yaml_text, content


def parse_yaml_min(yaml_text: str) -> dict:
    result: dict = {}
    lines = yaml_text.splitlines()
    current_key = None
    current_list: list | None = None

    for line in lines:
        if current_list is not None:
            stripped = line.strip()
            if stripped.startswith("- "):
                current_list.append(stripped[2:].strip())
                continue
            else:
                result[current_key] = current_list
                current_list = None
                current_key = None

        if ":" not in line:
            continue

        colon = line.index(":")
        key = line[:colon].strip()
        raw_val = line[colon + 1:].strip()

        if raw_val == "":
            current_key = key
            current_list = []
        elif raw_val.startswith("[") and raw_val.endswith("]"):
            items = [v.strip() for v in raw_val[1:-1].split(",") if v.strip()]
            result[key] = items
        else:
            result[key] = raw_val

    if current_key is not None and current_list is not None:
        result[current_key] = current_list

    return result


# ---------------------------------------------------------------------------
# Fact file I/O
# ---------------------------------------------------------------------------

def fact_path(facts_root: Path, domain: str, fact_id: str) -> Path:
    return facts_root / "facts" / domain / fact_id / "index.md"


def iter_fact_paths(facts_root: Path) -> list[Path]:
    return sorted(facts_root.glob("facts/*/*/index.md"))


def find_fact_path(facts_root: Path, fact_id: str) -> Path | None:
    matches = list(facts_root.glob(f"facts/*/{fact_id}/index.md"))
    return matches[0] if matches else None


def load_fact(path: Path) -> tuple[dict, str]:
    yaml_text, body = split_frontmatter(path.read_text())
    meta = parse_yaml_min(yaml_text)
    if meta.get("supersedes") == "null":
        meta["supersedes"] = None
    return meta, body


def render_frontmatter(meta: dict) -> str:
    lines = ["---"]
    for key in FRONTMATTER_ORDER:
        value = meta.get(key)
        if key in LIST_FIELDS:
            value = value or []
            if key == "evidence" and value:
                lines.append(f"{key}:")
                lines.extend(f"  - {v}" for v in value)
            else:
                lines.append(f"{key}: [{', '.join(value)}]")
        elif value is None:
            lines.append(f"{key}: null")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


def write_fact(path: Path, meta: dict, body: str) -> None:
    content = render_frontmatter(meta) + "\n\n" + body.rstrip("\n") + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content)
    tmp.replace(path)


def render_body(summary: str, evidence: list[str]) -> str:
    lines = ["## Compressed", summary.strip(), "", "## Context", "", "## Evidence"]
    lines.extend(f"- {e}" for e in evidence)
    lines.append("")
    return "\n".join(lines)


def extract_section(body: str, heading: str) -> str:
    collecting = False
    collected: list[str] = []
    for line in body.splitlines():
        if line.strip() == heading:
            collecting = True
            continue
        if collecting and line.strip().startswith("## "):
            break
        if collecting:
            collected.append(line)
    return "\n".join(collected).strip()


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    tmp.replace(path)


def split_csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


# ---------------------------------------------------------------------------
# Index / graph
# ---------------------------------------------------------------------------

def rebuild_index(facts_root: Path) -> tuple[int, int]:
    paths = iter_fact_paths(facts_root)
    counts: Counter = Counter()
    facts_entry: dict = {}
    nodes: list[str] = []
    edges: list[dict] = []

    for path in paths:
        meta, body = load_fact(path)
        fid = meta.get("id", path.parent.name)
        domain = meta.get("domain", path.parent.parent.name)
        counts[domain] += 1
        facts_entry[fid] = {
            "path": path.relative_to(facts_root).as_posix(),
            "domain": domain,
            "status": meta.get("status"),
            "title": meta.get("title"),
            "tags": meta.get("tags") or [],
            "owners": meta.get("owners") or [],
            "compressed": extract_section(body, "## Compressed"),
        }
        nodes.append(fid)
        for target in meta.get("related") or []:
            edges.append({"from": fid, "to": target, "type": "related"})
        for target in meta.get("depends_on") or []:
            edges.append({"from": fid, "to": target, "type": "depends_on"})
        if meta.get("supersedes"):
            edges.append({"from": fid, "to": meta["supersedes"], "type": "supersedes"})

    now = now_iso()
    write_json(facts_root / "facts-index.json",
               {"generatedAt": now, "counts": dict(counts), "facts": facts_entry})
    write_json(facts_root / "facts-graph.json", {"nodes": nodes, "edges": edges})
    write_json(facts_root / ".realm" / "facts-state.json",
               {"lastIndex": now, "counts": dict(counts), "factCount": len(paths)})
    return len(paths), len(counts)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_fact(
    path: Path, meta: dict, body: str, all_ids: set[str], id_counts: Counter, mr_ready: bool,
) -> list[str]:
    errs: list[str] = []

    for field in FRONTMATTER_ORDER:
        if field == "supersedes":
            continue
        if field not in meta:
            errs.append(f"{path}:{field}: missing")

    fact_id = meta.get("id", "")
    if fact_id and not ID_RE.match(fact_id):
        errs.append(f"{path}:id: '{fact_id}' not kebab-case")
    if fact_id and fact_id != path.parent.name:
        errs.append(f"{path}:id: '{fact_id}' does not match directory '{path.parent.name}'")

    domain = meta.get("domain", "")
    if domain and domain != path.parent.parent.name:
        errs.append(f"{path}:domain: '{domain}' does not match parent directory '{path.parent.parent.name}'")

    status = meta.get("status", "")
    if status and status not in FACT_STATUSES:
        errs.append(f"{path}:status: '{status}' not one of {sorted(FACT_STATUSES)}")

    compressed = extract_section(body, "## Compressed")
    if not compressed:
        errs.append(f"{path}:compressed: missing or empty")
    elif len(compressed) > MAX_COMPRESSED_CHARS:
        errs.append(f"{path}:compressed: {len(compressed)} chars exceeds {MAX_COMPRESSED_CHARS}")

    if not (meta.get("owners") or []):
        errs.append(f"{path}:owners: must be non-empty")

    for link_field in ("related", "depends_on"):
        for target in meta.get(link_field) or []:
            if target not in all_ids:
                errs.append(f"{path}:{link_field}: '{target}' does not resolve to an existing fact")

    supersedes = meta.get("supersedes")
    if supersedes and supersedes not in all_ids:
        errs.append(f"{path}:supersedes: '{supersedes}' does not resolve to an existing fact")

    if fact_id and id_counts.get(fact_id, 0) > 1:
        errs.append(f"{path}:id: duplicate id '{fact_id}' used in {id_counts[fact_id]} facts")

    if mr_ready:
        if status not in ("draft", "review"):
            errs.append(f"{path}:status: mr-ready requires draft or review, got '{status}'")
        if not (meta.get("evidence") or []):
            errs.append(f"{path}:evidence: mr-ready requires non-empty evidence")
        if not (meta.get("reviewers") or []):
            errs.append(f"{path}:reviewers: mr-ready requires non-empty reviewers")

    return errs


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_init(args: argparse.Namespace) -> None:
    facts_root = Path(args.facts_root).resolve()
    for sub in ("facts", "decisions", "references", "scripts"):
        (facts_root / sub).mkdir(parents=True, exist_ok=True)
    (facts_root / ".realm").mkdir(parents=True, exist_ok=True)

    # Vendor this script into the central repo so its own CI (which has no
    # realm plugin installed) can call `scripts/facts.py` locally.
    self_path = Path(__file__).resolve()
    dest = facts_root / "scripts" / "facts.py"
    if self_path != dest:
        shutil.copy2(self_path, dest)

    fact_count, domain_count = rebuild_index(facts_root)
    print(f"init: {facts_root} ready. domains:{domain_count} facts:{fact_count}")


def cmd_new(args: argparse.Namespace) -> None:
    facts_root = Path(args.facts_root).resolve()
    fact_id = args.id
    domain = args.domain

    if not ID_RE.match(fact_id):
        print(f"new: id '{fact_id}' not kebab-case", file=sys.stderr)
        sys.exit(1)
    if not ID_RE.match(domain):
        print(f"new: domain '{domain}' not kebab-case", file=sys.stderr)
        sys.exit(1)
    existing = list(facts_root.glob(f"facts/*/{fact_id}/index.md"))
    if existing:
        print(f"new: id '{fact_id}' already exists at {existing[0]}", file=sys.stderr)
        sys.exit(1)
    if len(args.summary) > MAX_COMPRESSED_CHARS:
        print(f"new: summary {len(args.summary)} chars exceeds {MAX_COMPRESSED_CHARS}", file=sys.stderr)
        sys.exit(1)

    owners = split_csv(args.owners)
    reviewers = split_csv(args.reviewers)
    tags = split_csv(args.tags) if args.tags else []
    evidence = args.evidence or []
    now = now_iso()

    meta = {
        "id": fact_id, "domain": domain, "title": args.title, "status": "draft",
        "owners": owners, "reviewers": reviewers, "tags": tags, "evidence": evidence,
        "related": [], "depends_on": [], "supersedes": None,
        "created": now, "updated": now,
    }
    path = fact_path(facts_root, domain, fact_id)
    write_fact(path, meta, render_body(args.summary, evidence))
    rebuild_index(facts_root)
    print(f"new: facts/{domain}/{fact_id}/index.md created (status: draft)")


def cmd_link(args: argparse.Namespace) -> None:
    facts_root = Path(args.facts_root).resolve()
    path = find_fact_path(facts_root, args.fact)
    if path is None:
        print(f"link: fact not found: {args.fact}", file=sys.stderr)
        sys.exit(1)

    meta, body = load_fact(path)
    all_ids = {p.parent.name for p in iter_fact_paths(facts_root)}
    changed: list[str] = []

    if args.related:
        for target in args.related:
            if target not in all_ids:
                print(f"link: related target not found: {target}", file=sys.stderr)
                sys.exit(1)
        meta["related"] = sorted(set((meta.get("related") or []) + args.related))
        changed.append(f"related+=[{', '.join(args.related)}]")

    if args.depends_on:
        for target in args.depends_on:
            if target not in all_ids:
                print(f"link: depends-on target not found: {target}", file=sys.stderr)
                sys.exit(1)
        meta["depends_on"] = sorted(set((meta.get("depends_on") or []) + args.depends_on))
        changed.append(f"depends_on+=[{', '.join(args.depends_on)}]")

    if args.supersedes:
        if args.supersedes not in all_ids:
            print(f"link: supersedes target not found: {args.supersedes}", file=sys.stderr)
            sys.exit(1)
        meta["supersedes"] = args.supersedes
        changed.append(f"supersedes={args.supersedes}")

    if not changed:
        print("link: nothing to do (pass --related/--depends-on/--supersedes)", file=sys.stderr)
        sys.exit(1)

    meta["updated"] = now_iso()
    write_fact(path, meta, body)
    rebuild_index(facts_root)
    print(f"link: {args.fact} " + " ".join(changed))


def cmd_validate(args: argparse.Namespace) -> None:
    facts_root = Path(args.facts_root).resolve()
    all_paths = iter_fact_paths(facts_root)

    if args.fact:
        paths = [p for p in all_paths if p.parent.name == args.fact]
        if not paths:
            print(f"validate: fact not found: {args.fact}", file=sys.stderr)
            sys.exit(1)
    else:
        paths = all_paths

    all_ids = {p.parent.name for p in all_paths}
    id_counts = Counter(p.parent.name for p in all_paths)

    errors: list[str] = []
    for path in paths:
        meta, body = load_fact(path)
        errors.extend(validate_fact(path, meta, body, all_ids, id_counts, args.mr_ready))

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        sys.exit(1)
    suffix = " (mr-ready)" if args.mr_ready else ""
    print(f"validate: {len(paths)} fact(s) ok{suffix}")


def cmd_index(args: argparse.Namespace) -> None:
    facts_root = Path(args.facts_root).resolve()
    fact_count, domain_count = rebuild_index(facts_root)
    print(f"index: {fact_count} facts across {domain_count} domains -> facts-index.json, facts-graph.json")


def cmd_search(args: argparse.Namespace) -> None:
    facts_root = Path(args.facts_root).resolve()
    index_path = facts_root / "facts-index.json"
    if not index_path.exists():
        print("search: facts-index.json missing. run: facts.py index --facts-root .", file=sys.stderr)
        sys.exit(1)

    index_doc = json.loads(index_path.read_text())
    query = (args.query or "").lower()
    results = []
    for fid, entry in index_doc.get("facts", {}).items():
        if args.domain and entry.get("domain") != args.domain:
            continue
        if args.status and entry.get("status") != args.status:
            continue
        if args.tag and args.tag not in (entry.get("tags") or []):
            continue
        haystack = " ".join([
            fid, entry.get("title", ""), entry.get("compressed", ""),
            " ".join(entry.get("tags") or []),
        ]).lower()
        if query and query not in haystack:
            continue
        results.append((fid, entry))

    if not results:
        print(f'search: no facts matched "{args.query}"')
        return

    for fid, entry in sorted(results, key=lambda kv: kv[0]):
        tags = " ".join(f"#{t}" for t in entry.get("tags") or [])
        print(f"{fid} [{entry.get('domain')}·{entry.get('status')}] {tags}")
        print(f"  {entry.get('compressed')}")


def cmd_bundle(args: argparse.Namespace) -> None:
    facts_root = Path(args.facts_root).resolve()
    index_path = facts_root / "facts-index.json"
    if not index_path.exists():
        print("bundle: facts-index.json missing. run: facts.py index --facts-root .", file=sys.stderr)
        sys.exit(1)

    index_doc = json.loads(index_path.read_text())
    facts_map = index_doc.get("facts", {})
    entry = facts_map.get(args.fact)
    if entry is None:
        print(f"bundle: fact not found: {args.fact}. run index first, or check id.", file=sys.stderr)
        sys.exit(1)

    path = find_fact_path(facts_root, args.fact)
    meta, body = load_fact(path) if path else ({}, "")
    deps = meta.get("depends_on") or []
    evidence = meta.get("evidence") or []
    repo_refs = [e for e in evidence if not e.startswith("http")]

    print("FACT_BUNDLE:")
    print(f"  id: {args.fact}")
    print(f"  compressed: {entry.get('compressed')}")

    if args.bundle in ("context", "full"):
        print(f"  title: {entry.get('title')}")
        print(f"  domain: {entry.get('domain')}")
        print(f"  tags: [{', '.join(entry.get('tags') or [])}]")
        print(f"  owners: [{', '.join(entry.get('owners') or [])}]")

    print(f"  deps: [{', '.join(deps)}]")
    if args.deps or args.bundle == "full":
        for dep_id in deps:
            dep_entry = facts_map.get(dep_id, {})
            print(f"    - {dep_id}: {dep_entry.get('compressed', '')}")

    print(f"  repo_refs: [{', '.join(repo_refs)}]")
    print("  drift_policy: live code wins; facts = intent")

    if args.bundle == "full":
        print("  body: |")
        for line in body.splitlines():
            print(f"    {line}")


def cmd_set_status(args: argparse.Namespace) -> None:
    if args.status not in FACT_STATUSES:
        print(f"set-status: invalid status '{args.status}'. one of {sorted(FACT_STATUSES)}", file=sys.stderr)
        sys.exit(1)

    facts_root = Path(args.facts_root).resolve()
    path = find_fact_path(facts_root, args.fact)
    if path is None:
        print(f"set-status: fact not found: {args.fact}", file=sys.stderr)
        sys.exit(1)

    meta, body = load_fact(path)
    meta["status"] = args.status
    meta["updated"] = now_iso()
    write_fact(path, meta, body)
    rebuild_index(facts_root)
    print(f"set-status: {args.fact} -> {args.status}")


def cmd_connect(args: argparse.Namespace) -> None:
    project_root = Path(args.project_root).resolve()
    state_path = project_root / ".realm" / "realm-state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    state["factsRepo"] = {
        "url": args.facts_url,
        "localPath": args.local_path,
        "branch": args.branch or "main",
        "lastSync": None,
    }
    write_json(state_path, state)
    print(f"connect: factsRepo -> {args.facts_url} ({args.local_path})")


def cmd_state(args: argparse.Namespace) -> None:
    project_root = Path(args.project_root).resolve()
    state_path = project_root / ".realm" / "realm-state.json"
    if not state_path.exists():
        print("FACTS_CONNECTED=false")
        return

    state = json.loads(state_path.read_text())
    facts_repo = state.get("factsRepo")
    if not facts_repo:
        print("FACTS_CONNECTED=false")
        return

    if args.stamp_sync:
        facts_repo["lastSync"] = now_iso()
        state["factsRepo"] = facts_repo
        write_json(state_path, state)

    print("FACTS_CONNECTED=true")
    print(f"FACTS_URL={facts_repo.get('url', '')}")
    print(f"FACTS_LOCAL_PATH={facts_repo.get('localPath', '')}")
    print(f"FACTS_BRANCH={facts_repo.get('branch', '')}")
    print(f"FACTS_LAST_SYNC={facts_repo.get('lastSync') or ''}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="facts.py")
    sub = p.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("--facts-root", required=True)
    init.set_defaults(func=cmd_init)

    new = sub.add_parser("new")
    new.add_argument("--facts-root", required=True)
    new.add_argument("--domain", required=True)
    new.add_argument("--id", required=True)
    new.add_argument("--title", required=True)
    new.add_argument("--summary", required=True)
    new.add_argument("--owners", required=True, help="comma-separated, e.g. @alice,@bob")
    new.add_argument("--reviewers", required=True, help="comma-separated")
    new.add_argument("--tags", default="", help="comma-separated")
    new.add_argument("--evidence", action="append", help="repeatable")
    new.set_defaults(func=cmd_new)

    link = sub.add_parser("link")
    link.add_argument("--facts-root", required=True)
    link.add_argument("--fact", required=True)
    link.add_argument("--related", action="append")
    link.add_argument("--depends-on", action="append")
    link.add_argument("--supersedes")
    link.set_defaults(func=cmd_link)

    val = sub.add_parser("validate")
    val.add_argument("--facts-root", required=True)
    val.add_argument("--fact")
    val.add_argument("--mr-ready", action="store_true")
    val.set_defaults(func=cmd_validate)

    idx = sub.add_parser("index")
    idx.add_argument("--facts-root", required=True)
    idx.set_defaults(func=cmd_index)

    srch = sub.add_parser("search")
    srch.add_argument("--facts-root", required=True)
    srch.add_argument("--query", default="")
    srch.add_argument("--domain")
    srch.add_argument("--tag")
    srch.add_argument("--status")
    srch.set_defaults(func=cmd_search)

    bnd = sub.add_parser("bundle")
    bnd.add_argument("--facts-root", required=True)
    bnd.add_argument("--fact", required=True)
    bnd.add_argument("--bundle", choices=("impl", "context", "full"), default="impl")
    bnd.add_argument("--deps", action="store_true")
    bnd.set_defaults(func=cmd_bundle)

    ss = sub.add_parser("set-status")
    ss.add_argument("--facts-root", required=True)
    ss.add_argument("--fact", required=True)
    ss.add_argument("--status", required=True)
    ss.set_defaults(func=cmd_set_status)

    conn = sub.add_parser("connect")
    conn.add_argument("--project-root", required=True)
    conn.add_argument("--facts-url", required=True)
    conn.add_argument("--local-path", required=True)
    conn.add_argument("--branch", default="main")
    conn.set_defaults(func=cmd_connect)

    st = sub.add_parser("state")
    st.add_argument("--project-root", required=True)
    st.add_argument("--stamp-sync", action="store_true")
    st.set_defaults(func=cmd_state)

    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
