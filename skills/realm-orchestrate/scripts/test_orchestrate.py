from __future__ import annotations

import json
from pathlib import Path

import pytest

import orchestrate


def _setup_project(tmp_path: Path) -> Path:
    """Create a project root with a minimal realm-state.json pointing at a vault."""
    project_root = tmp_path / "project"
    vault = tmp_path / "vault"
    project_dir = vault / "projects" / "demo"
    project_dir.mkdir(parents=True)
    (project_root / ".realm").mkdir(parents=True)
    state = {"vaultPath": str(vault), "projectSlug": "demo", "projectDir": str(project_dir)}
    (project_root / ".realm" / "realm-state.json").write_text(json.dumps(state, indent=2) + "\n")
    return project_root


def _bundles_file(tmp_path: Path, bundles: list[dict], name: str = "bundles.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(bundles))
    return path


def _default_bundles() -> list[dict]:
    return [
        {"id": "B1", "wave": 1, "class": "MECHANICAL", "tasks": ["T1"], "files": ["a.ts"]},
        {"id": "B2", "wave": 1, "class": "COMPLEX", "tasks": ["T2"], "files": ["b.ts"]},
        {"id": "B3", "wave": 2, "class": "COMPLEX", "tasks": ["T3"], "files": ["c.ts"], "dependsOn": ["B1"]},
    ]


def _start(project_root: Path, tmp_path: Path, bundles: list[dict] | None = None,
           plan: str = "plan-index.md", plan_slug: str = "plan-index") -> None:
    bf = _bundles_file(tmp_path, bundles or _default_bundles())
    orchestrate.main([
        "start", "--project-root", str(project_root),
        "--plan", plan, "--plan-slug", plan_slug, "--bundles-file", str(bf),
    ])


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    return _setup_project(tmp_path)


class TestState:
    def test_inactive_when_no_run(self, project_root: Path, capsys: pytest.CaptureFixture) -> None:
        orchestrate.main(["state", "--project-root", str(project_root)])
        out = capsys.readouterr().out
        assert "ORCH_ACTIVE=false" in out

    def test_active_after_start(self, project_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        _start(project_root, tmp_path)
        capsys.readouterr()
        orchestrate.main(["state", "--project-root", str(project_root)])
        out = capsys.readouterr().out
        assert "ORCH_ACTIVE=true" in out
        assert "RUN_ID=ADR-001-plan-index" in out


class TestStart:
    def test_creates_run_dir_and_files(self, project_root: Path, tmp_path: Path) -> None:
        _start(project_root, tmp_path)
        run_dir = tmp_path / "vault" / "projects" / "demo" / "orchestration" / "execution" / "ADR-001-plan-index"
        assert (run_dir / "run.json").exists()
        assert (run_dir / "index.md").exists()
        run = json.loads((run_dir / "run.json").read_text())
        assert run["runId"] == "ADR-001-plan-index"
        assert run["status"] == "IN_PROGRESS"
        assert len(run["bundles"]) == 3
        assert len(run["waves"]) == 2

    def test_sets_lock(self, project_root: Path, tmp_path: Path) -> None:
        _start(project_root, tmp_path)
        orch_state = json.loads((project_root / ".realm" / "orchestrate-state.json").read_text())
        assert orch_state["activeRun"]["runId"] == "ADR-001-plan-index"

    def test_second_start_blocked(self, project_root: Path, tmp_path: Path) -> None:
        _start(project_root, tmp_path)
        with pytest.raises(SystemExit) as exc:
            _start(project_root, tmp_path, plan="other.md", plan_slug="other")
        assert exc.value.code == 2

    def test_index_allocation_ignores_decisions_dir(self, project_root: Path, tmp_path: Path) -> None:
        # A decisions/ADR-007-* dir must not influence orchestration numbering.
        project_dir = tmp_path / "vault" / "projects" / "demo"
        (project_dir / "decisions" / "ADR-007-unrelated").mkdir(parents=True)
        _start(project_root, tmp_path)
        run_dir = project_dir / "orchestration" / "execution" / "ADR-001-plan-index"
        assert run_dir.exists()

    def test_second_run_after_finish_gets_next_index(self, project_root: Path, tmp_path: Path) -> None:
        _start(project_root, tmp_path, bundles=[{"id": "B1", "wave": 1, "class": "MECHANICAL"}])
        orchestrate.main(["bundle-status", "--project-root", str(project_root),
                           "--bundle", "B1", "--status", "DONE", "--attempt", "1"])
        orchestrate.main(["wave-done", "--project-root", str(project_root), "--wave", "1"])
        orchestrate.main(["finish", "--project-root", str(project_root)])

        _start(project_root, tmp_path, plan="plan2.md", plan_slug="plan2",
               bundles=[{"id": "B1", "wave": 1, "class": "MECHANICAL"}])
        run_dir = (tmp_path / "vault" / "projects" / "demo" / "orchestration" / "execution"
                   / "ADR-002-plan2")
        assert run_dir.exists()


class TestBundleAndWaveLifecycle:
    def test_bundle_status_updates_run(self, project_root: Path, tmp_path: Path) -> None:
        _start(project_root, tmp_path)
        orchestrate.main(["wave-start", "--project-root", str(project_root), "--wave", "1"])
        orchestrate.main([
            "bundle-status", "--project-root", str(project_root), "--bundle", "B1",
            "--status", "DONE", "--attempt", "1", "--plan-check", "pass", "--review", "CLEAN",
            "--files", "a.ts,a.test.ts",
        ])
        run_dir = tmp_path / "vault" / "projects" / "demo" / "orchestration" / "execution" / "ADR-001-plan-index"
        run = json.loads((run_dir / "run.json").read_text())
        b1 = next(b for b in run["bundles"] if b["id"] == "B1")
        assert b1["status"] == "DONE"
        assert b1["attempt"] == 1
        assert b1["planCheck"] == "pass"
        assert b1["review"] == "CLEAN"
        assert b1["filesChanged"] == ["a.ts", "a.test.ts"]

    def test_wave_done_requires_all_bundles_done(self, project_root: Path, tmp_path: Path) -> None:
        _start(project_root, tmp_path)
        orchestrate.main(["bundle-status", "--project-root", str(project_root),
                           "--bundle", "B1", "--status", "DONE", "--attempt", "1"])
        with pytest.raises(SystemExit):
            orchestrate.main(["wave-done", "--project-root", str(project_root), "--wave", "1"])

    def test_wave_done_writes_summary_and_advances(self, project_root: Path, tmp_path: Path) -> None:
        _start(project_root, tmp_path)
        for bid in ("B1", "B2"):
            orchestrate.main(["bundle-status", "--project-root", str(project_root),
                               "--bundle", bid, "--status", "DONE", "--attempt", "1",
                               "--plan-check", "pass", "--review", "CLEAN"])
        orchestrate.main(["wave-done", "--project-root", str(project_root), "--wave", "1", "--note", "shipped B1/B2"])

        run_dir = tmp_path / "vault" / "projects" / "demo" / "orchestration" / "execution" / "ADR-001-plan-index"
        assert (run_dir / "wave-1.md").exists()
        content = (run_dir / "wave-1.md").read_text()
        assert "shipped B1/B2" in content
        run = json.loads((run_dir / "run.json").read_text())
        assert run["currentWave"] == 2


class TestAllDoneUnfinished:
    """A run whose waves are all DONE but `finish` was never called."""

    def _complete_all_waves(self, project_root: Path, tmp_path: Path) -> None:
        _start(project_root, tmp_path, bundles=[{"id": "B1", "wave": 1, "class": "MECHANICAL"}])
        orchestrate.main(["bundle-status", "--project-root", str(project_root),
                           "--bundle", "B1", "--status", "DONE", "--attempt", "1"])
        orchestrate.main(["wave-done", "--project-root", str(project_root), "--wave", "1"])

    def test_state_reports_all_done(self, project_root: Path, tmp_path: Path,
                                     capsys: pytest.CaptureFixture) -> None:
        self._complete_all_waves(project_root, tmp_path)
        capsys.readouterr()
        orchestrate.main(["state", "--project-root", str(project_root)])
        out = capsys.readouterr().out
        assert "ALL_DONE=true" in out
        assert "STATUS=IN_PROGRESS" in out  # finish was never called

    def test_second_start_names_all_done_explicitly(self, project_root: Path, tmp_path: Path,
                                                       capsys: pytest.CaptureFixture) -> None:
        self._complete_all_waves(project_root, tmp_path)
        with pytest.raises(SystemExit) as exc:
            _start(project_root, tmp_path, plan="other.md", plan_slug="other")
        assert exc.value.code == 2
        err = capsys.readouterr().err
        assert "ALL WAVES DONE" in err
        assert "ALL_DONE=true" in err

    def test_resume_anchor_reports_all_done(self, project_root: Path, tmp_path: Path,
                                             capsys: pytest.CaptureFixture) -> None:
        self._complete_all_waves(project_root, tmp_path)
        capsys.readouterr()
        orchestrate.main(["resume", "--project-root", str(project_root)])
        out = capsys.readouterr().out
        assert "ALL_DONE=true" in out
        assert "CURRENT=none" in out
        assert "NEXT=none" in out


class TestResume:
    def test_resume_reports_in_progress_not_done(self, project_root: Path, tmp_path: Path,
                                                    capsys: pytest.CaptureFixture) -> None:
        _start(project_root, tmp_path)
        orchestrate.main(["wave-start", "--project-root", str(project_root), "--wave", "1"])
        orchestrate.main(["bundle-status", "--project-root", str(project_root),
                           "--bundle", "B1", "--status", "IN_PROGRESS", "--attempt", "1"])
        capsys.readouterr()
        orchestrate.main(["resume", "--project-root", str(project_root)])
        out = capsys.readouterr().out
        assert "B1:IN_PROGRESS" in out
        assert "B1:DONE" not in out
        run_dir = tmp_path / "vault" / "projects" / "demo" / "orchestration" / "execution" / "ADR-001-plan-index"
        assert f"RUN_DIR={run_dir}" in out

    def test_resume_without_active_run_fails(self, project_root: Path) -> None:
        with pytest.raises(SystemExit):
            orchestrate.main(["resume", "--project-root", str(project_root)])


class TestAbort:
    def test_wrong_confirm_refused(self, project_root: Path, tmp_path: Path) -> None:
        _start(project_root, tmp_path)
        with pytest.raises(SystemExit):
            orchestrate.main(["abort", "--project-root", str(project_root), "--confirm", "WRONG-ID"])

    def test_correct_confirm_releases_lock_and_touches_nothing_else(
        self, project_root: Path, tmp_path: Path,
    ) -> None:
        _start(project_root, tmp_path)
        orchestrate.main(["bundle-status", "--project-root", str(project_root),
                           "--bundle", "B1", "--status", "PARTIAL", "--attempt", "1",
                           "--files", "a.ts"])

        realm_state_before = (project_root / ".realm" / "realm-state.json").read_text()

        orchestrate.main(["abort", "--project-root", str(project_root), "--confirm", "ADR-001-plan-index"])

        orch_state = json.loads((project_root / ".realm" / "orchestrate-state.json").read_text())
        assert orch_state["activeRun"] is None
        assert orch_state["history"][-1]["status"] == "ABORTED"
        assert orch_state["history"][-1]["runDir"] == str(
            tmp_path / "vault" / "projects" / "demo" / "orchestration" / "execution" / "ADR-001-plan-index"
        )

        realm_state_after = (project_root / ".realm" / "realm-state.json").read_text()
        assert realm_state_before == realm_state_after

        run_dir = tmp_path / "vault" / "projects" / "demo" / "orchestration" / "execution" / "ADR-001-plan-index"
        run = json.loads((run_dir / "run.json").read_text())
        assert run["status"] == "ABORTED"

        with pytest.raises(SystemExit):
            orchestrate.main(["resume", "--project-root", str(project_root)])


class TestFinish:
    def test_finish_requires_all_waves_done(self, project_root: Path, tmp_path: Path) -> None:
        _start(project_root, tmp_path)
        with pytest.raises(SystemExit):
            orchestrate.main(["finish", "--project-root", str(project_root)])

    def test_finish_sets_complete_and_releases_lock(self, project_root: Path, tmp_path: Path) -> None:
        _start(project_root, tmp_path, bundles=[{"id": "B1", "wave": 1, "class": "MECHANICAL"}])
        orchestrate.main(["bundle-status", "--project-root", str(project_root),
                           "--bundle", "B1", "--status", "DONE", "--attempt", "1"])
        orchestrate.main(["wave-done", "--project-root", str(project_root), "--wave", "1"])
        orchestrate.main(["finish", "--project-root", str(project_root)])

        orch_state = json.loads((project_root / ".realm" / "orchestrate-state.json").read_text())
        assert orch_state["activeRun"] is None

        run_dir = tmp_path / "vault" / "projects" / "demo" / "orchestration" / "execution" / "ADR-001-plan-index"
        run = json.loads((run_dir / "run.json").read_text())
        assert run["status"] == "COMPLETE"
        assert orch_state["history"][-1]["runDir"] == str(run_dir)


class TestRender:
    def test_render_is_idempotent(self, project_root: Path, tmp_path: Path) -> None:
        _start(project_root, tmp_path)
        run_dir = tmp_path / "vault" / "projects" / "demo" / "orchestration" / "execution" / "ADR-001-plan-index"
        first = (run_dir / "index.md").read_text()
        orchestrate.main(["render", "--project-root", str(project_root)])
        second = (run_dir / "index.md").read_text()
        assert first == second
