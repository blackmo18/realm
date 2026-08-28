#!/usr/bin/env python3
"""Run-record owner for realm-orchestrate.

All mechanical work lives here: run-directory allocation, run.json /
index.md / wave-<n>.md rendering, bundle and wave status transitions, the
one-active-run lock (.realm/orchestrate-state.json), the resume anchor, and
abort. The SKILL.md layer never hand-edits run.json, index.md, a wave
summary, or the lock file -- it only calls this CLI and reads its stdout.

realm-state.json (vaultPath / projectDir) is read-only here -- this script
never writes to it. The lock lives in its own state file, mirroring
realm-concise's concise-state.json, because realm-state.json has been
actively shrunk upstream (forge_init.py purges unrecognized keys on every
re-run) and is not a safe place to park run-lifecycle data.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SLUG_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
RUN_DIR_RE = re.compile(r"^ADR-(\d+)-")
PLAN_INDEX_RE = re.compile(r"^(\d+)-")
BUNDLE_STATUSES = {"PENDING", "IN_PROGRESS", "DONE", "PARTIAL", "BLOCKED", "ABORTED"}
WAVE_STATUSES = {"PENDING", "IN_PROGRESS", "DONE"}
RUN_STATUSES = {"IN_PROGRESS", "COMPLETE", "ABORTED"}
ORCH_STATE_VERSION = 1


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    tmp.replace(path)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content)
    tmp.replace(path)


def split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def die(message: str, code: int = 1) -> None:
    print(message, file=sys.stderr)
    sys.exit(code)


# ---------------------------------------------------------------------------
# realm-state.json (read-only)
# ---------------------------------------------------------------------------

def load_realm_state(project_root: Path) -> dict:
    state_path = project_root / ".realm" / "realm-state.json"
    if not state_path.exists():
        die("No realm state found. Run /realm-forge to bootstrap.")
    return json.loads(state_path.read_text())


def project_dir_for(project_root: Path) -> Path:
    state = load_realm_state(project_root)
    if state.get("projectDir"):
        return Path(state["projectDir"])
    vault_path = state.get("vaultPath")
    project_slug = state.get("projectSlug")
    if not vault_path or not project_slug:
        die("realm-state.json missing vaultPath/projectSlug/projectDir.")
    return Path(vault_path) / "projects" / project_slug


def execution_root(project_dir: Path) -> Path:
    return project_dir / "orchestration"


def resolve_index(plan_path: str, exec_root: Path) -> int:
    """Reuse the source plan's own NNN prefix (execution/003-exct-foo.md ->
    3) so the orchestration run stays numbered with its plan/ADR/execution
    trio. Freeform plans with no numeric prefix (plan-index.md, a typed-out
    task list) fall back to the next free index in exec_root."""
    m = PLAN_INDEX_RE.match(Path(plan_path).name)
    if m:
        return int(m.group(1))
    existing_indices = [0]
    if exec_root.is_dir():
        for child in exec_root.iterdir():
            if child.is_dir():
                rm = RUN_DIR_RE.match(child.name)
                if rm:
                    existing_indices.append(int(rm.group(1)))
    return max(existing_indices) + 1


# ---------------------------------------------------------------------------
# orchestrate-state.json (the lock)
# ---------------------------------------------------------------------------

def orch_state_path(project_root: Path) -> Path:
    return project_root / ".realm" / "orchestrate-state.json"


def load_orch_state(project_root: Path) -> dict:
    path = orch_state_path(project_root)
    if not path.exists():
        return {"version": ORCH_STATE_VERSION, "activeRun": None, "history": []}
    return json.loads(path.read_text())


def save_orch_state(project_root: Path, state: dict) -> None:
    write_json(orch_state_path(project_root), state)


# ---------------------------------------------------------------------------
# run.json
# ---------------------------------------------------------------------------

def run_json_path(run_dir: Path) -> Path:
    return run_dir / "run.json"


def load_run(run_dir: Path) -> dict:
    path = run_json_path(run_dir)
    if not path.exists():
        die(f"run.json not found at {path}")
    return json.loads(path.read_text())


def save_run(run_dir: Path, run: dict) -> None:
    run["updatedAt"] = now_iso()
    write_json(run_json_path(run_dir), run)
    write_text(run_dir / "index.md", render_index_md(run))


def find_bundle(run: dict, bundle_id: str) -> dict:
    for bundle in run["bundles"]:
        if bundle["id"] == bundle_id:
            return bundle
    die(f"bundle not found in run: {bundle_id}")


def find_wave(run: dict, wave_num: int) -> dict:
    for wave in run["waves"]:
        if wave["wave"] == wave_num:
            return wave
    die(f"wave not found in run: {wave_num}")


def next_pending_wave(run: dict) -> int | None:
    for wave in run["waves"]:
        if wave["status"] != "DONE":
            return wave["wave"]
    return None


def all_waves_done(run: dict) -> bool:
    return all(w["status"] == "DONE" for w in run["waves"])


def active_run_dir(project_root: Path) -> Path:
    orch_state = load_orch_state(project_root)
    active = orch_state.get("activeRun")
    if not active:
        die("No active orchestration.")
    return Path(active["runDir"])


# ---------------------------------------------------------------------------
# Rendering (script-owned; never hand-authored by the LLM layer)
# ---------------------------------------------------------------------------

def render_index_md(run: dict) -> str:
    lines = [
        f"# {run['runId']}",
        "",
        f"- **plan**: {run['planPath']}",
        f"- **status**: {run['status']}",
        f"- **started**: {run['startedAt']}",
        f"- **updated**: {run['updatedAt']}",
        f"- **ended**: {run.get('endedAt') or '-'}",
        f"- **current wave**: {run.get('currentWave') if run.get('currentWave') is not None else '-'}",
        "",
        "## Waves",
        "",
        "| wave | status | bundles | summary |",
        "|------|--------|---------|---------|",
    ]
    for wave in run["waves"]:
        bundle_list = ", ".join(wave["bundles"])
        summary = f"[[{wave['summaryFile']}]]" if wave.get("summaryFile") else "-"
        lines.append(f"| {wave['wave']} | {wave['status']} | {bundle_list} | {summary} |")

    lines += ["", "## Bundles", "", "| bundle | wave | class | attempt | status | plan | review | files |",
              "|--------|------|-------|---------|--------|------|--------|-------|"]
    for bundle in run["bundles"]:
        files = ", ".join(bundle.get("filesChanged") or bundle.get("files") or [])
        lines.append(
            f"| {bundle['id']} | {bundle['wave']} | {bundle['class']} | {bundle['attempt']} | "
            f"{bundle['status']} | {bundle.get('planCheck') or '-'} | {bundle.get('review') or '-'} | {files} |"
        )

    blocked = [b for b in run["bundles"] if b["status"] == "BLOCKED" and b.get("blockerNeeds")]
    if blocked:
        lines += ["", "## Blockers", ""]
        for b in blocked:
            lines.append(f"- **{b['id']}**: {b['blockerNeeds']}")

    if run["status"] == "ABORTED":
        lines += ["", "## Aborted", "", f"Run aborted at {run.get('endedAt')}. "
                  "Working tree untouched -- files listed above are no longer tracked by orchestration."]

    lines.append("")
    return "\n".join(lines)


def render_wave_md(run: dict, wave_num: int, note: str) -> str:
    wave = find_wave(run, wave_num)
    bundles = [b for b in run["bundles"] if b["id"] in wave["bundles"]]
    lines = [f"# {run['runId']} -- Wave {wave_num}", "", f"- **status**: {wave['status']}",
              f"- **ended**: {wave.get('endedAt') or '-'}", ""]
    if note:
        lines += ["## Notes", "", note, ""]
    lines += ["## Bundles", "", "| bundle | class | attempt | status | plan | review | files changed | exports |",
              "|--------|-------|---------|--------|------|--------|----------------|---------|"]
    for b in bundles:
        files = ", ".join(b.get("filesChanged") or [])
        exports = "; ".join(b.get("exports") or []) or "none"
        lines.append(
            f"| {b['id']} | {b['class']} | {b['attempt']} | {b['status']} | "
            f"{b.get('planCheck') or '-'} | {b.get('review') or '-'} | {files} | {exports} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_resume_anchor(run: dict, run_dir: Path | None = None) -> str:
    def fmt(bundles: list[dict]) -> str:
        return ",".join(f"{b['id']}:{b['status']}" for b in bundles) or "none"

    current_wave = run.get("currentWave")
    finished = [b for b in run["bundles"] if b["status"] == "DONE"]
    current = [b for b in run["bundles"] if b["wave"] == current_wave] if current_wave is not None else []
    next_wave = None
    for wave in run["waves"]:
        if current_wave is not None and wave["wave"] > current_wave and wave["status"] != "DONE":
            next_wave = wave["wave"]
            break
    next_bundles = [b["id"] for b in run["bundles"] if b["wave"] == next_wave] if next_wave is not None else []

    lines = [
        "RESUME_ANCHOR",
        f"RUN_ID={run['runId']}",
        f"RUN_DIR={run_dir}" if run_dir is not None else "RUN_DIR=",
        f"PLAN={run['planPath']}",
        f"STATUS={run['status']}",
        f"ALL_DONE={'true' if all_waves_done(run) else 'false'}",
        f"FINISHED={fmt(finished)}",
        f"CURRENT_WAVE={current_wave if current_wave is not None else 'none'}",
        f"CURRENT={fmt(current)}",
        f"NEXT_WAVE={next_wave if next_wave is not None else 'none'}",
        f"NEXT={','.join(next_bundles) or 'none'}",
        f"UPDATED={run['updatedAt']}",
    ]
    return "\n".join(lines)


def render_status(run: dict, run_dir: Path) -> str:
    lines = [
        f"RUN_ID={run['runId']}",
        f"RUN_DIR={run_dir}",
        f"PLAN={run['planPath']}",
        f"STATUS={run['status']}",
        f"CURRENT_WAVE={run.get('currentWave') if run.get('currentWave') is not None else 'none'}",
        f"STARTED={run['startedAt']}",
        f"UPDATED={run['updatedAt']}",
        "",
        "WAVES",
    ]
    for wave in run["waves"]:
        lines.append(f"  {wave['wave']}: {wave['status']} [{', '.join(wave['bundles'])}]")
    lines += ["", "BUNDLES"]
    for b in run["bundles"]:
        lines.append(
            f"  {b['id']} wave:{b['wave']} class:{b['class']} attempt:{b['attempt']} "
            f"status:{b['status']} plan:{b.get('planCheck') or '-'} review:{b.get('review') or '-'}"
        )
    blocked = [b for b in run["bundles"] if b["status"] == "BLOCKED"]
    if blocked:
        lines += ["", "BLOCKERS"]
        for b in blocked:
            lines.append(f"  {b['id']}: {b.get('blockerNeeds') or 'unspecified'}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_state(args: argparse.Namespace) -> None:
    project_root = Path(args.project_root).resolve()
    orch_state = load_orch_state(project_root)
    active = orch_state.get("activeRun")
    if not active:
        print("ORCH_ACTIVE=false")
        return

    run_dir = Path(active["runDir"])
    run = load_run(run_dir)
    print("ORCH_ACTIVE=true")
    print(f"RUN_ID={run['runId']}")
    print(f"RUN_DIR={run_dir}")
    print(f"PLAN={run['planPath']}")
    print(f"WAVE={run.get('currentWave') if run.get('currentWave') is not None else 'none'}")
    print(f"STATUS={run['status']}")
    print(f"ALL_DONE={'true' if all_waves_done(run) else 'false'}")
    print(f"UPDATED={run['updatedAt']}")


def cmd_start(args: argparse.Namespace) -> None:
    project_root = Path(args.project_root).resolve()
    orch_state = load_orch_state(project_root)
    if orch_state.get("activeRun"):
        run_dir = Path(orch_state["activeRun"]["runDir"])
        run = load_run(run_dir)
        if all_waves_done(run):
            print(
                f"ORCHESTRATION ACTIVE -- {run['runId']} has ALL WAVES DONE but was never "
                "finished (run `finish` to release the lock, or `abort` to drop it), then start again.",
                file=sys.stderr,
            )
        else:
            print("ORCHESTRATION ACTIVE -- cannot start a new run.", file=sys.stderr)
        print(render_resume_anchor(run, run_dir), file=sys.stderr)
        sys.exit(2)

    if not SLUG_RE.match(args.plan_slug):
        die(f"start: plan-slug '{args.plan_slug}' not kebab-case")

    project_dir = project_dir_for(project_root)
    exec_root = execution_root(project_dir)
    exec_root.mkdir(parents=True, exist_ok=True)

    index = resolve_index(args.plan, exec_root)
    run_id = f"ADR-{index:03d}-task-orchestration"
    run_dir = exec_root / run_id
    if run_dir.exists():
        die(
            f"start: run dir already exists for index {index:03d} ({run_dir}). "
            "A prior orchestration run already used this plan's index -- "
            "resume or abort it, or confirm the --plan path is correct."
        )

    bundles_raw = json.loads(Path(args.bundles_file).read_text())
    if not bundles_raw:
        die("start: bundles-file has no bundles")

    now = now_iso()
    bundles = []
    wave_numbers: dict[int, list[str]] = {}
    for b in bundles_raw:
        if "id" not in b or "wave" not in b:
            die(f"start: bundle missing 'id' or 'wave': {b}")
        bundles.append({
            "id": b["id"],
            "name": b.get("name", ""),
            "wave": b["wave"],
            "class": b.get("class", "COMPLEX"),
            "model": b.get("model", "inherit"),
            "tasks": b.get("tasks", []),
            "files": b.get("files", []),
            "dependsOn": b.get("dependsOn", []),
            "attempt": 0,
            "status": "PENDING",
            "planCheck": None,
            "review": None,
            "filesChanged": [],
            "exports": [],
            "blockerNeeds": None,
            "updatedAt": now,
        })
        wave_numbers.setdefault(b["wave"], []).append(b["id"])

    waves = [
        {"wave": w, "status": "PENDING", "bundles": ids, "summaryFile": None, "endedAt": None}
        for w, ids in sorted(wave_numbers.items())
    ]

    run = {
        "runId": run_id,
        "index": index,
        "planPath": args.plan,
        "planSlug": args.plan_slug,
        "projectSlug": project_dir.name,
        "status": "IN_PROGRESS",
        "startedAt": now,
        "updatedAt": now,
        "endedAt": None,
        "currentWave": waves[0]["wave"] if waves else None,
        "waves": waves,
        "bundles": bundles,
    }

    run_dir.mkdir(parents=True, exist_ok=False)
    write_json(run_json_path(run_dir), run)
    write_text(run_dir / "index.md", render_index_md(run))

    orch_state["activeRun"] = {
        "runId": run_id, "runDir": str(run_dir), "planPath": args.plan, "startedAt": now,
    }
    save_orch_state(project_root, orch_state)

    print(f"start: {run_id} created at {run_dir}")
    print(f"waves: {len(waves)}  bundles: {len(bundles)}")


def cmd_wave_start(args: argparse.Namespace) -> None:
    project_root = Path(args.project_root).resolve()
    run_dir = active_run_dir(project_root)
    run = load_run(run_dir)
    wave = find_wave(run, args.wave)
    wave["status"] = "IN_PROGRESS"
    run["currentWave"] = args.wave
    save_run(run_dir, run)
    print(f"wave-start: wave {args.wave} IN_PROGRESS")


def cmd_bundle_status(args: argparse.Namespace) -> None:
    if args.status not in BUNDLE_STATUSES:
        die(f"bundle-status: invalid status '{args.status}'. one of {sorted(BUNDLE_STATUSES)}")

    project_root = Path(args.project_root).resolve()
    run_dir = active_run_dir(project_root)
    run = load_run(run_dir)
    bundle = find_bundle(run, args.bundle)

    bundle["status"] = args.status
    bundle["attempt"] = args.attempt
    if args.plan_check is not None:
        bundle["planCheck"] = args.plan_check
    if args.review is not None:
        bundle["review"] = args.review
    if args.files is not None:
        bundle["filesChanged"] = split_csv(args.files)
    if args.exports_file:
        exports_text = Path(args.exports_file).read_text().strip()
        bundle["exports"] = [line.strip("- ").strip() for line in exports_text.splitlines() if line.strip()]
    if args.blocker is not None:
        bundle["blockerNeeds"] = args.blocker or None
    bundle["updatedAt"] = now_iso()

    save_run(run_dir, run)
    print(f"bundle-status: {args.bundle} -> {args.status} (attempt {args.attempt})")


def cmd_wave_done(args: argparse.Namespace) -> None:
    project_root = Path(args.project_root).resolve()
    run_dir = active_run_dir(project_root)
    run = load_run(run_dir)
    wave = find_wave(run, args.wave)
    bundles = [b for b in run["bundles"] if b["id"] in wave["bundles"]]

    not_done = [b["id"] for b in bundles if b["status"] != "DONE"]
    if not_done:
        die(f"wave-done: wave {args.wave} has unfinished bundles: {', '.join(not_done)}")

    wave["status"] = "DONE"
    wave["endedAt"] = now_iso()
    wave_summary_name = f"wave-{args.wave}.md"
    wave["summaryFile"] = wave_summary_name

    write_text(run_dir / wave_summary_name, render_wave_md(run, args.wave, args.note or ""))

    run["currentWave"] = next_pending_wave(run)
    save_run(run_dir, run)
    print(f"wave-done: wave {args.wave} DONE -> {wave_summary_name}")


def cmd_resume(args: argparse.Namespace) -> None:
    project_root = Path(args.project_root).resolve()
    run_dir = active_run_dir(project_root)
    run = load_run(run_dir)
    print(render_resume_anchor(run, run_dir))


def cmd_status(args: argparse.Namespace) -> None:
    project_root = Path(args.project_root).resolve()
    run_dir = active_run_dir(project_root)
    run = load_run(run_dir)
    print(render_status(run, run_dir))


def cmd_finish(args: argparse.Namespace) -> None:
    project_root = Path(args.project_root).resolve()
    orch_state = load_orch_state(project_root)
    active = orch_state.get("activeRun")
    if not active:
        die("No active orchestration.")
    run_dir = Path(active["runDir"])
    run = load_run(run_dir)

    not_done = [w["wave"] for w in run["waves"] if w["status"] != "DONE"]
    if not_done:
        die(f"finish: waves not done: {not_done}. Use resume to continue or abort to drop the run.")

    run["status"] = "COMPLETE"
    run["endedAt"] = now_iso()
    save_run(run_dir, run)

    orch_state["history"].append({
        "runId": run["runId"], "runDir": str(run_dir), "status": "COMPLETE", "endedAt": run["endedAt"],
    })
    orch_state["activeRun"] = None
    save_orch_state(project_root, orch_state)
    print(f"finish: {run['runId']} COMPLETE")


def cmd_abort(args: argparse.Namespace) -> None:
    project_root = Path(args.project_root).resolve()
    orch_state = load_orch_state(project_root)
    active = orch_state.get("activeRun")
    if not active:
        die("No active orchestration.")
    run_dir = Path(active["runDir"])
    run = load_run(run_dir)

    if args.confirm != run["runId"]:
        die(f"abort: confirmation '{args.confirm}' does not match active run '{run['runId']}'")

    run["status"] = "ABORTED"
    run["endedAt"] = now_iso()
    save_run(run_dir, run)

    orch_state["history"].append({
        "runId": run["runId"], "runDir": str(run_dir), "status": "ABORTED", "endedAt": run["endedAt"],
    })
    orch_state["activeRun"] = None
    save_orch_state(project_root, orch_state)

    touched = sorted({f for b in run["bundles"] for f in (b.get("filesChanged") or [])})
    print(f"abort: {run['runId']} ABORTED. Lock released. Working tree untouched (no git commands run).")
    if touched:
        print("Files no longer tracked by orchestration:")
        for f in touched:
            print(f"  - {f}")


def cmd_render(args: argparse.Namespace) -> None:
    project_root = Path(args.project_root).resolve()
    run_dir = active_run_dir(project_root)
    run = load_run(run_dir)
    write_text(run_dir / "index.md", render_index_md(run))
    print(f"render: {run_dir / 'index.md'}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="orchestrate.py")
    sub = p.add_subparsers(dest="command", required=True)

    st = sub.add_parser("state")
    st.add_argument("--project-root", required=True)
    st.set_defaults(func=cmd_state)

    start = sub.add_parser("start")
    start.add_argument("--project-root", required=True)
    start.add_argument("--plan", required=True)
    start.add_argument("--plan-slug", required=True)
    start.add_argument("--bundles-file", required=True)
    start.set_defaults(func=cmd_start)

    ws = sub.add_parser("wave-start")
    ws.add_argument("--project-root", required=True)
    ws.add_argument("--wave", required=True, type=int)
    ws.set_defaults(func=cmd_wave_start)

    bs = sub.add_parser("bundle-status")
    bs.add_argument("--project-root", required=True)
    bs.add_argument("--bundle", required=True)
    bs.add_argument("--status", required=True)
    bs.add_argument("--attempt", required=True, type=int)
    bs.add_argument("--plan-check", choices=("pass", "fail"))
    bs.add_argument("--review", choices=("CLEAN", "SHOULD_FIX", "BLOCKING"))
    bs.add_argument("--files", help="comma-separated")
    bs.add_argument("--exports-file", help="file with one export per line")
    bs.add_argument("--blocker", help="BLOCKER_NEEDS text, or empty string to clear")
    bs.set_defaults(func=cmd_bundle_status)

    wd = sub.add_parser("wave-done")
    wd.add_argument("--project-root", required=True)
    wd.add_argument("--wave", required=True, type=int)
    wd.add_argument("--note", help="optional human summary prose for wave-<n>.md")
    wd.set_defaults(func=cmd_wave_done)

    rs = sub.add_parser("resume")
    rs.add_argument("--project-root", required=True)
    rs.set_defaults(func=cmd_resume)

    stt = sub.add_parser("status")
    stt.add_argument("--project-root", required=True)
    stt.set_defaults(func=cmd_status)

    fin = sub.add_parser("finish")
    fin.add_argument("--project-root", required=True)
    fin.set_defaults(func=cmd_finish)

    ab = sub.add_parser("abort")
    ab.add_argument("--project-root", required=True)
    ab.add_argument("--confirm", required=True)
    ab.set_defaults(func=cmd_abort)

    rd = sub.add_parser("render")
    rd.add_argument("--project-root", required=True)
    rd.set_defaults(func=cmd_render)

    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
