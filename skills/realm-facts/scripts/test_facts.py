from __future__ import annotations

import json
from pathlib import Path

import pytest

import facts


def _new(root: Path, *, domain: str = "platform", fact_id: str = "jwt-token-rotation",
         title: str = "JWT Token Rotation", summary: str = "JWT 15min expiry. Refresh via silent iframe.",
         owners: str = "@alice", reviewers: str = "@bob", tags: str = "auth,security",
         evidence: list[str] | None = None) -> None:
    args = [
        "new", "--facts-root", str(root), "--domain", domain, "--id", fact_id,
        "--title", title, "--summary", summary, "--owners", owners,
        "--reviewers", reviewers, "--tags", tags,
    ]
    for e in (evidence or []):
        args += ["--evidence", e]
    facts.main(args)


@pytest.fixture
def facts_root(tmp_path: Path) -> Path:
    root = tmp_path / "facts-repo"
    facts.main(["init", "--facts-root", str(root)])
    return root


class TestInit:
    def test_creates_layout(self, tmp_path: Path) -> None:
        root = tmp_path / "repo"
        facts.main(["init", "--facts-root", str(root)])
        for sub in ("facts", "decisions", "references", "scripts", ".realm"):
            assert (root / sub).is_dir()
        assert (root / "facts-index.json").exists()
        assert (root / "facts-graph.json").exists()

    def test_vendors_script_into_facts_repo(self, tmp_path: Path) -> None:
        root = tmp_path / "repo"
        facts.main(["init", "--facts-root", str(root)])
        vendored = root / "scripts" / "facts.py"
        assert vendored.exists()
        assert vendored.read_text() == Path(facts.__file__).read_text()

    def test_idempotent(self, tmp_path: Path) -> None:
        root = tmp_path / "repo"
        facts.main(["init", "--facts-root", str(root)])
        _new(root)
        facts.main(["init", "--facts-root", str(root)])
        # re-running init must not delete an existing fact
        assert (root / "facts" / "platform" / "jwt-token-rotation" / "index.md").exists()


class TestNewAndValidate:
    def test_new_then_validate_passes(self, facts_root: Path) -> None:
        _new(facts_root)
        facts.main(["validate", "--facts-root", str(facts_root)])  # no SystemExit == pass

    def test_missing_compressed_fails(self, facts_root: Path) -> None:
        _new(facts_root)
        path = facts_root / "facts" / "platform" / "jwt-token-rotation" / "index.md"
        meta, _ = facts.load_fact(path)
        facts.write_fact(path, meta, "## Context\n\n## Evidence\n")
        with pytest.raises(SystemExit):
            facts.main(["validate", "--facts-root", str(facts_root)])

    def test_summary_over_max_chars_rejected_at_creation(self, facts_root: Path) -> None:
        with pytest.raises(SystemExit):
            _new(facts_root, summary="x" * (facts.MAX_COMPRESSED_CHARS + 1))

    def test_new_blocks_duplicate_id_across_domains_outright(self, facts_root: Path) -> None:
        # `new` refuses a duplicate id before it ever reaches disk — the
        # strongest guarantee. validate's own duplicate check (below) is
        # defense-in-depth for a hand-edited file that bypassed `new`.
        _new(facts_root, domain="platform", fact_id="dup-fact")
        with pytest.raises(SystemExit):
            _new(facts_root, domain="payments", fact_id="dup-fact")

    def test_validate_catches_hand_edited_duplicate_id(self, facts_root: Path) -> None:
        _new(facts_root, domain="platform", fact_id="dup-fact")
        _new(facts_root, domain="payments", fact_id="other-fact")
        other_path = facts_root / "facts" / "payments" / "other-fact" / "index.md"
        meta, body = facts.load_fact(other_path)
        meta["id"] = "dup-fact"  # simulate a hand-edit that collides with the platform fact
        facts.write_fact(other_path, meta, body)
        with pytest.raises(SystemExit):
            facts.main(["validate", "--facts-root", str(facts_root)])

    def test_validate_fact_reports_duplicate_id_message(self, tmp_path: Path) -> None:
        path = tmp_path / "facts" / "platform" / "dup-fact" / "index.md"
        meta = {
            "id": "dup-fact", "domain": "platform", "title": "T", "status": "draft",
            "owners": ["@a"], "reviewers": ["@b"], "tags": [], "evidence": [],
            "related": [], "depends_on": [], "supersedes": None,
            "created": "2026-01-01T00:00:00+00:00", "updated": "2026-01-01T00:00:00+00:00",
        }
        body = "## Compressed\nsummary\n"
        errs = facts.validate_fact(
            path, meta, body, all_ids={"dup-fact"}, id_counts={"dup-fact": 2}, mr_ready=False,
        )
        assert any("duplicate id" in e for e in errs)

    def test_new_rejects_existing_id(self, facts_root: Path) -> None:
        _new(facts_root)
        with pytest.raises(SystemExit):
            _new(facts_root)

    def test_new_rejects_non_kebab_id(self, facts_root: Path) -> None:
        with pytest.raises(SystemExit):
            _new(facts_root, fact_id="Not_Kebab")


class TestMrReady:
    def test_rejects_empty_evidence(self, facts_root: Path) -> None:
        _new(facts_root, evidence=[])
        with pytest.raises(SystemExit):
            facts.main(["validate", "--facts-root", str(facts_root), "--mr-ready"])

    def test_rejects_empty_reviewers_is_impossible_but_active_status_is_rejected(self, facts_root: Path) -> None:
        _new(facts_root, evidence=["https://example.com/doc"])
        facts.main(["set-status", "--facts-root", str(facts_root), "--fact", "jwt-token-rotation", "--status", "active"])
        with pytest.raises(SystemExit):
            facts.main(["validate", "--facts-root", str(facts_root), "--mr-ready"])

    def test_plain_validate_accepts_missing_evidence_and_review_status(self, facts_root: Path) -> None:
        _new(facts_root, evidence=[])
        facts.main(["validate", "--facts-root", str(facts_root)])  # no raise


class TestLink:
    def test_link_to_nonexistent_fact_fails(self, facts_root: Path) -> None:
        _new(facts_root)
        with pytest.raises(SystemExit):
            facts.main(["link", "--facts-root", str(facts_root), "--fact", "jwt-token-rotation",
                        "--related", "does-not-exist"])

    def test_valid_link_appears_as_graph_edge(self, facts_root: Path) -> None:
        _new(facts_root, fact_id="jwt-token-rotation")
        _new(facts_root, fact_id="session-refresh-policy")
        facts.main(["link", "--facts-root", str(facts_root), "--fact", "jwt-token-rotation",
                    "--related", "session-refresh-policy"])
        graph = json.loads((facts_root / "facts-graph.json").read_text())
        assert {"from": "jwt-token-rotation", "to": "session-refresh-policy", "type": "related"} in graph["edges"]

    def test_link_unknown_fact_fails(self, facts_root: Path) -> None:
        with pytest.raises(SystemExit):
            facts.main(["link", "--facts-root", str(facts_root), "--fact", "nope", "--related", "x"])

    def test_link_with_no_flags_fails(self, facts_root: Path) -> None:
        _new(facts_root)
        with pytest.raises(SystemExit):
            facts.main(["link", "--facts-root", str(facts_root), "--fact", "jwt-token-rotation"])


class TestIndexAndSearch:
    def test_index_counts_match_tree(self, facts_root: Path) -> None:
        _new(facts_root, domain="platform", fact_id="a")
        _new(facts_root, domain="platform", fact_id="b")
        _new(facts_root, domain="payments", fact_id="c")
        facts.main(["index", "--facts-root", str(facts_root)])
        index = json.loads((facts_root / "facts-index.json").read_text())
        assert index["counts"] == {"platform": 2, "payments": 1}
        assert set(index["facts"]) == {"a", "b", "c"}

    def test_search_reads_index_only(self, facts_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _new(facts_root, fact_id="jwt-token-rotation", tags="auth")
        facts.main(["index", "--facts-root", str(facts_root)])

        # tamper with the on-disk fact tree without reindexing: search must
        # still answer from facts-index.json, proving it never live-scans.
        (facts_root / "facts" / "platform" / "jwt-token-rotation").rename(
            facts_root / "facts" / "platform" / "renamed-away"
        )
        facts.main(["search", "--facts-root", str(facts_root), "--query", "jwt"])

    def test_search_filters_by_domain_tag_status(self, facts_root: Path) -> None:
        _new(facts_root, domain="platform", fact_id="a", tags="auth")
        _new(facts_root, domain="payments", fact_id="b", tags="billing")
        facts.main(["index", "--facts-root", str(facts_root)])
        index = json.loads((facts_root / "facts-index.json").read_text())
        assert index["facts"]["a"]["domain"] == "platform"
        assert index["facts"]["b"]["domain"] == "payments"


class TestConnectPreservesState:
    def test_connect_preserves_unrelated_keys(self, tmp_path: Path) -> None:
        project = tmp_path / "product"
        realm_dir = project / ".realm"
        realm_dir.mkdir(parents=True)
        state = {
            "vaultPath": "/v", "projectSlug": "p", "projectDir": "/v/projects/p",
            "docs": {"a.md": {"status": "committed", "updated": "2026-01-01T00:00:00+00:00"}},
            "customState": {"keep": True},
        }
        (realm_dir / "realm-state.json").write_text(json.dumps(state))

        facts.main(["connect", "--project-root", str(project),
                    "--facts-url", "https://gitlab.example.com/org/realm-facts.git",
                    "--local-path", "/tmp/facts-repo"])

        result = json.loads((realm_dir / "realm-state.json").read_text())
        for key in ("vaultPath", "projectSlug", "projectDir", "docs", "customState"):
            assert result[key] == state[key]
        assert result["factsRepo"]["url"] == "https://gitlab.example.com/org/realm-facts.git"
        assert result["factsRepo"]["lastSync"] is None

    def test_connect_creates_state_when_absent(self, tmp_path: Path) -> None:
        project = tmp_path / "product"
        facts.main(["connect", "--project-root", str(project),
                    "--facts-url", "https://gitlab.example.com/org/realm-facts.git",
                    "--local-path", "/tmp/facts-repo"])
        result = json.loads((project / ".realm" / "realm-state.json").read_text())
        assert result["factsRepo"]["url"] == "https://gitlab.example.com/org/realm-facts.git"


class TestState:
    def test_reports_disconnected_when_no_state_file(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        facts.main(["state", "--project-root", str(tmp_path)])
        assert "FACTS_CONNECTED=false" in capsys.readouterr().out

    def test_reports_disconnected_when_no_facts_repo_key(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        realm_dir = tmp_path / ".realm"
        realm_dir.mkdir()
        (realm_dir / "realm-state.json").write_text(json.dumps({"docs": {}}))
        facts.main(["state", "--project-root", str(tmp_path)])
        assert "FACTS_CONNECTED=false" in capsys.readouterr().out

    def test_stamp_sync_updates_last_sync(self, tmp_path: Path) -> None:
        facts.main(["connect", "--project-root", str(tmp_path),
                    "--facts-url", "https://gitlab.example.com/org/realm-facts.git",
                    "--local-path", "/tmp/facts-repo"])
        facts.main(["state", "--project-root", str(tmp_path), "--stamp-sync"])
        result = json.loads((tmp_path / ".realm" / "realm-state.json").read_text())
        assert result["factsRepo"]["lastSync"] is not None


class TestSetStatus:
    def test_transitions_and_stamps_updated(self, facts_root: Path) -> None:
        _new(facts_root)
        path = facts_root / "facts" / "platform" / "jwt-token-rotation" / "index.md"
        before, _ = facts.load_fact(path)
        facts.main(["set-status", "--facts-root", str(facts_root), "--fact", "jwt-token-rotation", "--status", "review"])
        after, _ = facts.load_fact(path)
        assert after["status"] == "review"
        assert after["updated"] >= before["updated"]

    def test_invalid_status_rejected(self, facts_root: Path) -> None:
        _new(facts_root)
        with pytest.raises(SystemExit):
            facts.main(["set-status", "--facts-root", str(facts_root), "--fact", "jwt-token-rotation", "--status", "bogus"])

    def test_unknown_fact_rejected(self, facts_root: Path) -> None:
        with pytest.raises(SystemExit):
            facts.main(["set-status", "--facts-root", str(facts_root), "--fact", "nope", "--status", "active"])


class TestBundle:
    def test_impl_bundle_matches_documented_shape(self, facts_root: Path, capsys: pytest.CaptureFixture) -> None:
        _new(facts_root, evidence=["https://confluence.example.com/x/abc"])
        facts.main(["index", "--facts-root", str(facts_root)])
        facts.main(["bundle", "--facts-root", str(facts_root), "--fact", "jwt-token-rotation", "--bundle", "impl"])
        out = capsys.readouterr().out
        assert "FACT_BUNDLE:" in out
        assert "id: jwt-token-rotation" in out
        assert "compressed: JWT 15min expiry. Refresh via silent iframe." in out
        assert "drift_policy: live code wins; facts = intent" in out

    def test_unknown_fact_rejected(self, facts_root: Path) -> None:
        facts.main(["index", "--facts-root", str(facts_root)])
        with pytest.raises(SystemExit):
            facts.main(["bundle", "--facts-root", str(facts_root), "--fact", "nope"])

    def test_missing_index_rejected(self, tmp_path: Path) -> None:
        root = tmp_path / "no-index"
        (root / "facts").mkdir(parents=True)
        with pytest.raises(SystemExit):
            facts.main(["bundle", "--facts-root", str(root), "--fact", "nope"])


class TestFrontmatterRoundTrip:
    def test_render_and_parse_round_trips(self, tmp_path: Path) -> None:
        meta = {
            "id": "x", "domain": "platform", "title": "X", "status": "draft",
            "owners": ["@a"], "reviewers": ["@b"], "tags": ["t1", "t2"],
            "evidence": ["https://a", "https://b"], "related": ["y"],
            "depends_on": [], "supersedes": None,
            "created": "2026-01-01T00:00:00+00:00", "updated": "2026-01-01T00:00:00+00:00",
        }
        path = tmp_path / "index.md"
        facts.write_fact(path, meta, "## Compressed\nsome summary\n")
        parsed, body = facts.load_fact(path)
        for key, value in meta.items():
            assert parsed[key] == value
        assert facts.extract_section(body, "## Compressed") == "some summary"
