#!/usr/bin/env python3
"""God-file crawler, scorer, and state lifecycle owner for realm-concise.

All mechanical work lives here: file walking, LOC counting, fan-in
resolution, git churn, score/tier computation, state JSON mutation, and
ledger markdown rendering. The SKILL.md layer never hand-edits state or
counts lines itself — it only calls this CLI and reads its stdout.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path

SOURCE_EXTS = (".ts", ".tsx", ".js", ".jsx")
DEFAULT_MIN_LOC = 450
SKIP_DIRS = {
    "node_modules", ".next", "dist", "build", "out", "coverage",
    ".git", ".turbo", ".vercel", "__pycache__",
}
TEST_PATTERNS = ("*.test.*", "*.spec.*")
IMPORT_RE = re.compile(
    r"""(?:import|export)\s[^;]*?\sfrom\s+['"]([^'"]+)['"]"""
    r"""|require\(\s*['"]([^'"]+)['"]\s*\)""",
)
EXPORT_RE = re.compile(r"^export\b", re.MULTILINE)
STATUSES = {"candidate", "approved", "in-progress", "refactored", "ignored"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def is_test_file(path: Path) -> bool:
    name = path.name
    if any(fnmatch(name, pat) for pat in TEST_PATTERNS):
        return True
    return "__tests__" in path.parts


def load_conciseignore(root: Path) -> list[str]:
    ignore_file = root / ".conciseignore"
    if not ignore_file.exists():
        return []
    lines = ignore_file.read_text().splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]


def is_ignored(rel_path: str, patterns: list[str]) -> bool:
    return any(fnmatch(rel_path, pat) for pat in patterns)


def count_loc(path: Path) -> int:
    """Count physical source lines containing code, excluding comments/docs.

    This is deliberately a lightweight lexer rather than a line-prefix check:
    documentation blocks can begin after code, and code can resume after a block
    comment closes. Comment markers inside string literals are treated as code.
    """
    loc = 0
    in_block_comment = False
    quote: str | None = None
    escaped = False

    for raw_line in path.read_text(errors="replace").splitlines():
        has_code = False
        i = 0
        while i < len(raw_line):
            char = raw_line[i]
            following = raw_line[i + 1] if i + 1 < len(raw_line) else ""

            if in_block_comment:
                if char == "*" and following == "/":
                    in_block_comment = False
                    i += 2
                else:
                    i += 1
                continue

            if quote is not None:
                if not char.isspace():
                    has_code = True
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = None
                i += 1
                continue

            if char == "/" and following == "/":
                break
            if char == "/" and following == "*":
                in_block_comment = True
                i += 2
                continue
            if char in {'"', "'", "`"}:
                quote = char
                has_code = True
                i += 1
                continue
            if not char.isspace():
                has_code = True
            i += 1

        if has_code:
            loc += 1

        # Single- and double-quoted JavaScript strings cannot continue across a
        # physical line without an escape. Template literals can.
        if quote in {'"', "'"}:
            quote = None
            escaped = False

    return loc


def load_tsconfig_alias(root: Path) -> tuple[str, str] | None:
    tsconfig = root / "tsconfig.json"
    if not tsconfig.exists():
        return None
    try:
        raw = tsconfig.read_text()
        raw = re.sub(r"//.*", "", raw)
        raw = re.sub(r",(\s*[}\]])", r"\1", raw)
        data = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return None
    paths = data.get("compilerOptions", {}).get("paths", {})
    for alias, targets in paths.items():
        if alias.endswith("/*") and targets:
            target = targets[0]
            if target.endswith("/*"):
                return alias[:-2], target[:-2]
    return None


@dataclass
class FileMetrics:
    loc: int
    exports: int
    fan_in: int
    has_test: bool
    churn: int


@dataclass
class ScoredFile:
    metrics: FileMetrics
    score: int
    tier: str


def compute_score(metrics: FileMetrics, min_loc: int) -> int:
    size = min(metrics.loc / min_loc, 3.0) / 3.0
    isolation = 1.0 / (1 + metrics.fan_in)
    safety = 1.0 if metrics.has_test else 0.4
    heat = min(metrics.churn / 20, 1.0)
    return round(100 * (0.40 * size + 0.25 * isolation + 0.20 * safety + 0.15 * heat))


def compute_tier(metrics: FileMetrics) -> str:
    if metrics.fan_in <= 2 and metrics.has_test and metrics.loc < 900:
        return "low-hanging"
    if metrics.fan_in >= 8 or (not metrics.has_test and metrics.loc >= 900):
        return "deep"
    return "moderate"


def find_source_root(root: Path) -> Path:
    src = root / "src"
    return src if src.is_dir() else root


def walk_source_files(root: Path, include_tests: bool) -> list[Path]:
    src_root = find_source_root(root)
    ignore_patterns = load_conciseignore(root)
    results: list[Path] = []
    for path in src_root.rglob("*"):
        if not path.is_file() or path.suffix not in SOURCE_EXTS:
            continue
        if path.name.endswith(".d.ts"):
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not include_tests and is_test_file(path):
            continue
        rel = path.relative_to(root).as_posix()
        if is_ignored(rel, ignore_patterns):
            continue
        results.append(path)
    return results


def has_sibling_test(path: Path) -> bool:
    stem = path.name.rsplit(".", 1)[0] if path.suffix in {".ts", ".tsx", ".js", ".jsx"} else path.stem
    stem = path.stem
    for ext in SOURCE_EXTS:
        for marker in ("test", "spec"):
            candidate = path.with_name(f"{stem}.{marker}{ext}")
            if candidate.exists():
                return True
    test_dir = path.parent / "__tests__"
    if test_dir.is_dir():
        for ext in SOURCE_EXTS:
            if (test_dir / f"{stem}{ext}").exists():
                return True
    return False


def resolve_import(spec: str, from_file: Path, root: Path, alias: tuple[str, str] | None) -> Path | None:
    if spec.startswith("."):
        candidate = (from_file.parent / spec).resolve()
    elif alias and spec.startswith(alias[0]):
        rel = spec[len(alias[0]):]
        candidate = (root / alias[1] / rel).resolve()
    else:
        return None
    for ext in ("", ".ts", ".tsx", ".js", ".jsx"):
        p = candidate.parent / (candidate.name + ext) if ext else candidate
        if p.is_file():
            return p
    for ext in SOURCE_EXTS:
        p = candidate / f"index{ext}"
        if p.is_file():
            return p
    return None


def compute_fan_in(all_files: list[Path], root: Path) -> Counter:
    alias = load_tsconfig_alias(root)
    fan_in: Counter = Counter()
    for f in all_files:
        try:
            text = f.read_text(errors="replace")
        except OSError:
            continue
        for m in IMPORT_RE.finditer(text):
            spec = m.group(1) or m.group(2)
            if not spec:
                continue
            target = resolve_import(spec, f, root, alias)
            if target is not None:
                fan_in[target] += 1
    return fan_in


def compute_churn(root: Path) -> Counter:
    churn: Counter = Counter()
    try:
        out = subprocess.run(
            ["git", "log", "--name-only", "--pretty=format:", "--since=12.months"],
            cwd=root, capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return churn
    if out.returncode != 0:
        return churn
    for line in out.stdout.splitlines():
        line = line.strip()
        if line:
            churn[line] += 1
    return churn


def state_path(root: Path) -> Path:
    return root / ".realm" / "concise-state.json"


def ledger_path(root: Path) -> Path:
    return root / "docs" / "GOD_FILES.md"


def load_state(root: Path) -> dict:
    p = state_path(root)
    if not p.exists():
        return {"version": 1, "projectRoot": str(root), "minLoc": DEFAULT_MIN_LOC,
                 "lastScan": None, "files": {}, "refactored": []}
    return json.loads(p.read_text())


def save_state(root: Path, state: dict) -> None:
    p = state_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2, sort_keys=False) + "\n")


def cmd_scan(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    min_loc = args.min_loc
    state = load_state(root)
    state["minLoc"] = min_loc

    all_files = walk_source_files(root, include_tests=True)
    fan_in = compute_fan_in(all_files, root)
    churn = compute_churn(root)

    candidate_files = [f for f in all_files if args.include_tests or not is_test_file(f)]
    seen_rel: set[str] = set()
    now = now_iso()

    for f in candidate_files:
        loc = count_loc(f)
        if loc < min_loc:
            continue
        rel = f.relative_to(root).as_posix()
        seen_rel.add(rel)
        metrics = FileMetrics(
            loc=loc,
            exports=len(EXPORT_RE.findall(f.read_text(errors="replace"))),
            fan_in=fan_in.get(f, 0),
            has_test=has_sibling_test(f),
            churn=churn.get(rel, 0),
        )
        score = compute_score(metrics, min_loc)
        tier = compute_tier(metrics)

        existing = state["files"].get(rel)
        entry = {
            **asdict(metrics),
            "score": score,
            "tier": tier,
            "status": existing["status"] if existing else "candidate",
            "reason": existing.get("reason") if existing else None,
            "adr": existing.get("adr") if existing else None,
            "firstSeen": existing.get("firstSeen") if existing else now,
            "updated": now,
        }
        state["files"][rel] = entry

    stale = [rel for rel in state["files"] if rel not in seen_rel]
    for rel in stale:
        entry = state["files"].pop(rel)
        if entry["status"] in {"approved", "in-progress"}:
            state.setdefault("refactored", []).append({
                "path": rel, "date": now, "adr": entry.get("adr"),
                "newFiles": [], "locBefore": entry["loc"], "locAfter": None,
                "note": "auto-promoted: dropped below minLoc on rescan",
            })

    state["lastScan"] = now
    save_state(root, state)
    render_ledger(root, state)

    candidates = [(rel, e) for rel, e in state["files"].items() if e["status"] == "candidate"]
    candidates.sort(key=lambda kv: kv[1]["score"], reverse=True)
    print(f"scan:{root.name} files:{len(candidate_files)} candidates:{len(candidates)} "
          f"minLoc:{min_loc} state:{state_path(root).relative_to(root)}")
    for rel, e in candidates[:5]:
        print(f"  {e['score']:>3} {e['tier']:<11} loc:{e['loc']:<5} fanIn:{e['fan_in']:<3} "
              f"test:{'y' if e['has_test'] else 'n'} churn:{e['churn']:<3} {rel}")


def cmd_next(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    state = load_state(root)
    candidates = [(rel, e) for rel, e in state["files"].items() if e["status"] == "candidate"]
    candidates.sort(key=lambda kv: kv[1]["score"], reverse=True)
    if not candidates:
        print("next: no candidates. run scan.")
        return
    for rel, e in candidates[: args.n]:
        print(f"{e['score']:>3} {e['tier']:<11} loc:{e['loc']:<5} fanIn:{e['fan_in']:<3} "
              f"test:{'y' if e['has_test'] else 'n'} churn:{e['churn']:<3} {rel}")


def cmd_show(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    state = load_state(root)
    entry = state["files"].get(args.path)
    if entry is None:
        for h in state.get("refactored", []):
            if h["path"] == args.path:
                print(json.dumps(h, indent=2))
                return
        print(f"show: {args.path} not tracked.")
        sys.exit(1)
    print(json.dumps({args.path: entry}, indent=2))


def cmd_set_status(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    if args.status not in STATUSES:
        print(f"set-status: invalid status '{args.status}'. one of {sorted(STATUSES)}")
        sys.exit(1)
    if args.status == "ignored" and not args.reason:
        print("set-status: --reason required when status=ignored")
        sys.exit(1)
    state = load_state(root)
    entry = state["files"].get(args.path)
    if entry is None:
        print(f"set-status: {args.path} not tracked. run scan first.")
        sys.exit(1)
    entry["status"] = args.status
    if args.reason:
        entry["reason"] = args.reason
    if args.adr:
        entry["adr"] = args.adr
    entry["updated"] = now_iso()
    save_state(root, state)
    render_ledger(root, state)
    print(f"set-status: {args.path} -> {args.status}")


def cmd_complete(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    state = load_state(root)
    entry = state["files"].pop(args.path, None)
    if entry is None:
        print(f"complete: {args.path} not tracked.")
        sys.exit(1)
    loc_after = None
    target = root / args.path
    if target.exists():
        loc_after = count_loc(target)
    state.setdefault("refactored", []).append({
        "path": args.path,
        "date": now_iso(),
        "adr": args.adr or entry.get("adr"),
        "newFiles": args.new_files.split(",") if args.new_files else [],
        "locBefore": entry["loc"],
        "locAfter": loc_after,
    })
    save_state(root, state)
    render_ledger(root, state)
    print(f"complete: {args.path} moved to refactored history.")


def render_ledger(root: Path, state: dict) -> None:
    files = state["files"]
    by_status: dict[str, list[tuple[str, dict]]] = {}
    for rel, e in files.items():
        by_status.setdefault(e["status"], []).append((rel, e))
    for lst in by_status.values():
        lst.sort(key=lambda kv: kv[1]["score"], reverse=True)

    lines = [
        "<!-- generated by realm-concise — do not edit by hand -->",
        "# God Files",
        "",
        f"lastScan: {state.get('lastScan')}  minLoc: {state.get('minLoc')}",
        "",
        "## Candidates",
        "",
        "| score | tier | loc | fanIn | test | churn | file |",
        "|---|---|---|---|---|---|---|",
    ]
    for rel, e in by_status.get("candidate", []):
        lines.append(
            f"| {e['score']} | {e['tier']} | {e['loc']} | {e['fan_in']} | "
            f"{'y' if e['has_test'] else 'n'} | {e['churn']} | `{rel}` |"
        )

    lines += ["", "## Approved / In Progress", "", "| status | score | file | adr |", "|---|---|---|---|"]
    for status in ("approved", "in-progress"):
        for rel, e in by_status.get(status, []):
            lines.append(f"| {status} | {e['score']} | `{rel}` | {e.get('adr') or '-'} |")

    lines += ["", "## Refactored", "", "| date | file | loc before -> after | adr |", "|---|---|---|---|"]
    for h in sorted(state.get("refactored", []), key=lambda h: h["date"], reverse=True):
        lines.append(
            f"| {h['date'][:10]} | `{h['path']}` | {h['locBefore']} -> {h.get('locAfter') or '?'} | "
            f"{h.get('adr') or '-'} |"
        )

    lines += ["", "## Ignored", "", "| file | reason |", "|---|---|"]
    for rel, e in by_status.get("ignored", []):
        lines.append(f"| `{rel}` | {e.get('reason') or '-'} |")

    ledger_path(root).parent.mkdir(parents=True, exist_ok=True)
    ledger_path(root).write_text("\n".join(lines) + "\n")


def cmd_render(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    state = load_state(root)
    render_ledger(root, state)
    print(f"render: {ledger_path(root).relative_to(root)}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="concise.py")
    sub = p.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan")
    scan.add_argument("--root", required=True)
    scan.add_argument("--min-loc", type=int, default=DEFAULT_MIN_LOC)
    scan.add_argument("--include-tests", action="store_true")
    scan.set_defaults(func=cmd_scan)

    nxt = sub.add_parser("next")
    nxt.add_argument("--root", required=True)
    nxt.add_argument("-n", type=int, default=3)
    nxt.set_defaults(func=cmd_next)

    show = sub.add_parser("show")
    show.add_argument("--root", required=True)
    show.add_argument("path")
    show.set_defaults(func=cmd_show)

    ss = sub.add_parser("set-status")
    ss.add_argument("--root", required=True)
    ss.add_argument("path")
    ss.add_argument("--status", required=True)
    ss.add_argument("--reason")
    ss.add_argument("--adr")
    ss.set_defaults(func=cmd_set_status)

    comp = sub.add_parser("complete")
    comp.add_argument("--root", required=True)
    comp.add_argument("path")
    comp.add_argument("--new-files")
    comp.add_argument("--adr")
    comp.set_defaults(func=cmd_complete)

    rnd = sub.add_parser("render")
    rnd.add_argument("--root", required=True)
    rnd.set_defaults(func=cmd_render)

    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
