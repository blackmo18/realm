import json
import subprocess
from pathlib import Path

import pytest

import concise


def _write(root: Path, rel: str, lines: int, *, extra: str = "") -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(f"const x{i} = {i};" for i in range(lines))
    p.write_text(f"export const marker = true;\n{body}\n{extra}\n")
    return p


@pytest.fixture
def project(tmp_path: Path) -> Path:
    root = tmp_path / "proj"
    (root / "src").mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)
    return root


def _commit(root: Path, msg: str = "c") -> None:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", msg], cwd=root, check=True)


class TestCountLoc:
    def test_counts_non_blank_non_comment_lines(self, tmp_path: Path) -> None:
        f = tmp_path / "a.ts"
        f.write_text("const a = 1;\n\n// comment\n/* block\nstill block */\nconst b = 2;\n")
        assert concise.count_loc(f) == 2

    def test_empty_file_is_zero(self, tmp_path: Path) -> None:
        f = tmp_path / "a.ts"
        f.write_text("")
        assert concise.count_loc(f) == 0

    def test_excludes_jsdoc_and_comment_only_lines(self, tmp_path: Path) -> None:
        f = tmp_path / "a.ts"
        f.write_text(
            "/**\n"
            " * Explains the public API.\n"
            " * @example callThing()\n"
            " */\n"
            "// Architectural rationale only.\n"
            "export function callThing() {}\n"
        )
        assert concise.count_loc(f) == 1

    def test_handles_block_comments_mixed_with_code(self, tmp_path: Path) -> None:
        f = tmp_path / "a.ts"
        f.write_text(
            "const a = 1; /* rationale starts\n"
            "and continues as documentation\n"
            "*/ const b = 2;\n"
            "/* inline docs */\n"
        )
        assert concise.count_loc(f) == 2

    def test_comment_markers_in_strings_are_code(self, tmp_path: Path) -> None:
        f = tmp_path / "a.ts"
        f.write_text('const url = "https://example.com/a/*b*/";\n')
        assert concise.count_loc(f) == 1

    def test_trailing_comments_do_not_add_loc(self, tmp_path: Path) -> None:
        f = tmp_path / "a.ts"
        f.write_text("const a = 1; // explanation\n// explanation only\n")
        assert concise.count_loc(f) == 1


class TestIsTestFile:
    def test_matches_dot_test(self) -> None:
        assert concise.is_test_file(Path("src/foo.test.ts"))

    def test_matches_dot_spec(self) -> None:
        assert concise.is_test_file(Path("src/foo.spec.tsx"))

    def test_matches_tests_dir(self) -> None:
        assert concise.is_test_file(Path("src/__tests__/foo.ts"))

    def test_non_test_file(self) -> None:
        assert not concise.is_test_file(Path("src/foo.ts"))


class TestHasSiblingTest:
    def test_finds_colocated_test(self, tmp_path: Path) -> None:
        (tmp_path / "foo.ts").write_text("export const a = 1;\n")
        (tmp_path / "foo.test.ts").write_text("test('x', () => {});\n")
        assert concise.has_sibling_test(tmp_path / "foo.ts")

    def test_finds_tests_dir_variant(self, tmp_path: Path) -> None:
        (tmp_path / "foo.ts").write_text("export const a = 1;\n")
        (tmp_path / "__tests__").mkdir()
        (tmp_path / "__tests__" / "foo.ts").write_text("test('x', () => {});\n")
        assert concise.has_sibling_test(tmp_path / "foo.ts")

    def test_no_test_found(self, tmp_path: Path) -> None:
        (tmp_path / "foo.ts").write_text("export const a = 1;\n")
        assert not concise.has_sibling_test(tmp_path / "foo.ts")


class TestScoreAndTier:
    def test_low_hanging_low_fanin_tested_small(self) -> None:
        m = concise.FileMetrics(loc=500, exports=1, fan_in=1, has_test=True, churn=2)
        assert concise.compute_tier(m) == "low-hanging"

    def test_deep_high_fanin(self) -> None:
        m = concise.FileMetrics(loc=500, exports=1, fan_in=10, has_test=True, churn=2)
        assert concise.compute_tier(m) == "deep"

    def test_deep_untested_huge(self) -> None:
        m = concise.FileMetrics(loc=1200, exports=1, fan_in=1, has_test=False, churn=2)
        assert concise.compute_tier(m) == "deep"

    def test_moderate_fallthrough(self) -> None:
        m = concise.FileMetrics(loc=500, exports=1, fan_in=5, has_test=True, churn=2)
        assert concise.compute_tier(m) == "moderate"

    def test_score_bounded_0_100(self) -> None:
        m = concise.FileMetrics(loc=5000, exports=10, fan_in=0, has_test=True, churn=50)
        score = concise.compute_score(m, min_loc=450)
        assert 0 <= score <= 100

    def test_score_penalizes_missing_test(self) -> None:
        base = concise.FileMetrics(loc=500, exports=1, fan_in=1, has_test=True, churn=0)
        no_test = concise.FileMetrics(loc=500, exports=1, fan_in=1, has_test=False, churn=0)
        assert concise.compute_score(base, 450) > concise.compute_score(no_test, 450)


class TestResolveImport:
    def test_relative_import_resolves(self, tmp_path: Path) -> None:
        (tmp_path / "a.ts").write_text("x")
        (tmp_path / "b.ts").write_text("x")
        target = concise.resolve_import("./a", tmp_path / "b.ts", tmp_path, None)
        assert target == tmp_path / "a.ts"

    def test_alias_import_resolves(self, tmp_path: Path) -> None:
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "lib.ts").write_text("x")
        (tmp_path / "src" / "user.ts").write_text("x")
        target = concise.resolve_import("@/lib", tmp_path / "src" / "user.ts", tmp_path, ("@/", "src/"))
        assert target == tmp_path / "src" / "lib.ts"

    def test_bare_specifier_without_alias_returns_none(self, tmp_path: Path) -> None:
        assert concise.resolve_import("react", tmp_path / "a.ts", tmp_path, None) is None


class TestWalkAndFanIn:
    def test_walk_skips_node_modules_and_tests(self, project: Path) -> None:
        _write(project, "src/keep.ts", 5)
        (project / "src" / "node_modules").mkdir(parents=True)
        (project / "src" / "node_modules" / "dep.ts").write_text("export const a=1;\n")
        _write(project, "src/keep.test.ts", 5)
        files = concise.walk_source_files(project, include_tests=False)
        rels = {f.relative_to(project).as_posix() for f in files}
        assert rels == {"src/keep.ts"}

    def test_fan_in_counts_importers(self, project: Path) -> None:
        target = _write(project, "src/util.ts", 5)
        _write(project, "src/a.ts", 3, extra='import { marker } from "./util";')
        _write(project, "src/b.ts", 3, extra='import { marker } from "./util";')
        all_files = concise.walk_source_files(project, include_tests=True)
        fan_in = concise.compute_fan_in(all_files, project)
        assert fan_in[target] == 2


class TestScanLifecycle:
    def test_scan_finds_candidates_over_threshold(self, project: Path) -> None:
        _write(project, "src/big.ts", 500)
        _write(project, "src/small.ts", 50)
        _commit(project)
        concise.main(["scan", "--root", str(project), "--min-loc", "450"])
        state = concise.load_state(project)
        assert "src/big.ts" in state["files"]
        assert "src/small.ts" not in state["files"]

    def test_scan_excludes_test_files_by_default(self, project: Path) -> None:
        _write(project, "src/big.test.ts", 500)
        _commit(project)
        concise.main(["scan", "--root", str(project), "--min-loc", "450"])
        state = concise.load_state(project)
        assert state["files"] == {}

    def test_rescan_preserves_status(self, project: Path) -> None:
        _write(project, "src/big.ts", 500)
        _commit(project)
        concise.main(["scan", "--root", str(project), "--min-loc", "450"])
        concise.main(["set-status", "--root", str(project), "src/big.ts", "--status", "approved"])
        concise.main(["scan", "--root", str(project), "--min-loc", "450"])
        state = concise.load_state(project)
        assert state["files"]["src/big.ts"]["status"] == "approved"

    def test_file_dropping_below_threshold_while_approved_auto_promotes(self, project: Path) -> None:
        f = _write(project, "src/big.ts", 500)
        _commit(project)
        concise.main(["scan", "--root", str(project), "--min-loc", "450"])
        concise.main(["set-status", "--root", str(project), "src/big.ts", "--status", "approved"])
        f.write_text("export const a = 1;\n")
        concise.main(["scan", "--root", str(project), "--min-loc", "450"])
        state = concise.load_state(project)
        assert "src/big.ts" not in state["files"]
        paths = [h["path"] for h in state["refactored"]]
        assert "src/big.ts" in paths

    def test_ledger_renders_all_sections(self, project: Path) -> None:
        _write(project, "src/big.ts", 500)
        _commit(project)
        concise.main(["scan", "--root", str(project), "--min-loc", "450"])
        ledger = (project / "docs" / "GOD_FILES.md").read_text()
        for heading in ("## Candidates", "## Approved / In Progress", "## Refactored", "## Ignored"):
            assert heading in ledger


class TestSetStatus:
    def test_rejects_invalid_status(self, project: Path, capsys: pytest.CaptureFixture) -> None:
        _write(project, "src/big.ts", 500)
        _commit(project)
        concise.main(["scan", "--root", str(project), "--min-loc", "450"])
        with pytest.raises(SystemExit):
            concise.main(["set-status", "--root", str(project), "src/big.ts", "--status", "bogus"])

    def test_ignored_requires_reason(self, project: Path) -> None:
        _write(project, "src/big.ts", 500)
        _commit(project)
        concise.main(["scan", "--root", str(project), "--min-loc", "450"])
        with pytest.raises(SystemExit):
            concise.main(["set-status", "--root", str(project), "src/big.ts", "--status", "ignored"])

    def test_untracked_path_errors(self, project: Path) -> None:
        with pytest.raises(SystemExit):
            concise.main(["set-status", "--root", str(project), "src/nope.ts", "--status", "approved"])


class TestComplete:
    def test_complete_moves_to_refactored_history(self, project: Path) -> None:
        _write(project, "src/big.ts", 500)
        _commit(project)
        concise.main(["scan", "--root", str(project), "--min-loc", "450"])
        concise.main(["complete", "--root", str(project), "src/big.ts", "--adr", "ADR-001-split"])
        state = concise.load_state(project)
        assert "src/big.ts" not in state["files"]
        assert state["refactored"][0]["path"] == "src/big.ts"
        assert state["refactored"][0]["adr"] == "ADR-001-split"

    def test_complete_untracked_errors(self, project: Path) -> None:
        with pytest.raises(SystemExit):
            concise.main(["complete", "--root", str(project), "src/nope.ts"])


class TestNext:
    def test_next_orders_by_score_desc(self, project: Path) -> None:
        _write(project, "src/lo.ts", 460)
        _write(project, "src/hi.ts", 2000)
        _commit(project)
        concise.main(["scan", "--root", str(project), "--min-loc", "450"])
        out = json.loads(json.dumps(concise.load_state(project)))
        candidates = sorted(out["files"].items(), key=lambda kv: kv[1]["score"], reverse=True)
        assert candidates[0][0] == "src/hi.ts"
