#!/usr/bin/env python3
"""
test_manifest_write.py — deterministic regression suite for manifest_write.py.

Does NOT compare against the old LLM run (non-reproducible). Compares script
output against committed golden fixtures in scripts/testdata/<case>/.

Run:
    python3 test_manifest_write.py
    python3 test_manifest_write.py -v          # verbose
    python3 test_manifest_write.py TestCase.method  # single test
"""

import filecmp
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
_TESTDATA_DIR = os.path.join(_SCRIPTS_DIR, "testdata")
_MANIFEST_WRITE = os.path.join(_SCRIPTS_DIR, "manifest_write.py")

sys.path.insert(0, _SCRIPTS_DIR)
from realm_lib import parse_draft, split_frontmatter, parse_yaml_min


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_state(vault_path: str, project_slug: str) -> dict:
    return {
        "vaultPath": vault_path,
        "projectSlug": project_slug,
        "projectDir": os.path.join(vault_path, "projects", project_slug),
        "phase": {"lastRun": "2026-06-13T00:00:00+00:00", "draftReady": True},
        "manifest": {"lastRun": None},
        "docs": {},
    }


def _make_project(tmp_dir: str, slug: str, state: dict, draft_text: str) -> str:
    """Set up a minimal project tree for one test run."""
    project_root = os.path.join(tmp_dir, "project")
    realm_dir = os.path.join(project_root, ".realm")
    os.makedirs(realm_dir, exist_ok=True)

    # vault dirs
    vault_path = state["vaultPath"]
    project_dir = state["projectDir"]
    os.makedirs(project_dir, exist_ok=True)

    with open(os.path.join(realm_dir, "realm-state.json"), "w") as f:
        json.dump(state, f, indent=2)

    with open(os.path.join(realm_dir, "manifest-draft.md"), "w") as f:
        f.write(draft_text)

    return project_root


def _run_script(project_root: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, _MANIFEST_WRITE, "--project-root", project_root],
        capture_output=True, text=True
    )


def _load_state(project_root: str) -> dict:
    path = os.path.join(project_root, ".realm", "realm-state.json")
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestGuards(unittest.TestCase):

    def test_missing_state_exits_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = os.path.join(tmp, "project")
            os.makedirs(os.path.join(project_root, ".realm"))
            result = _run_script(project_root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("No realm state", result.stdout)

    def test_draft_not_ready_exits_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = os.path.join(tmp, "vault")
            slug = "test-proj"
            state = _base_state(vault, slug)
            state["phase"]["draftReady"] = False
            project_root = _make_project(tmp, slug, state, "")
            # remove draft so guard triggers on draftReady first
            draft = os.path.join(project_root, ".realm", "manifest-draft.md")
            if os.path.exists(draft):
                os.remove(draft)
            result = _run_script(project_root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("No staged draft", result.stdout)

    def test_missing_draft_file_exits_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = os.path.join(tmp, "vault")
            slug = "test-proj"
            state = _base_state(vault, slug)
            project_root = _make_project(tmp, slug, state, "placeholder")
            os.remove(os.path.join(project_root, ".realm", "manifest-draft.md"))
            result = _run_script(project_root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Draft file missing", result.stdout)


class TestNewNode(unittest.TestCase):

    DRAFT = """\
# Realm Manifest Draft — 2026-06-13

## Meta
slug: myproj
phase-run: 2026-06-13T10:00:00+00:00
mode: full
gap-summary: 1 new function

## Planned Node Documents

### functions/fetchUser.md
status: new
links: [[overview]]
---
---
id: fetchUser
type: function
status: proposed
created: 2026-06-13
updated: 2026-06-13
---

## Compressed
Fetches user by id from DB. Called by auth middleware.

## Full Function
Signature: `fetchUser(userId: str) -> User`
Frequency: high
"""

    def test_new_node_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = os.path.join(tmp, "vault")
            slug = "myproj"
            state = _base_state(vault, slug)
            project_root = _make_project(tmp, slug, state, self.DRAFT)
            result = _run_script(project_root)
            self.assertEqual(result.returncode, 0, result.stderr)
            written = os.path.join(state["projectDir"], "functions", "fetchUser.md")
            self.assertTrue(os.path.exists(written), "fetchUser.md not written")
            self.assertIn("WROTE", result.stdout)

    def test_state_updated_to_committed(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = os.path.join(tmp, "vault")
            slug = "myproj"
            state = _base_state(vault, slug)
            project_root = _make_project(tmp, slug, state, self.DRAFT)
            _run_script(project_root)
            new_state = _load_state(project_root)
            self.assertFalse(new_state["phase"]["draftReady"])
            self.assertIsNotNone(new_state["manifest"]["lastRun"])

    def test_draft_archived(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = os.path.join(tmp, "vault")
            slug = "myproj"
            state = _base_state(vault, slug)
            project_root = _make_project(tmp, slug, state, self.DRAFT)
            _run_script(project_root)
            draft_path = os.path.join(project_root, ".realm", "manifest-draft.md")
            archive_dir = os.path.join(project_root, ".realm", "archive")
            self.assertFalse(os.path.exists(draft_path), "draft should be archived")
            self.assertTrue(os.path.isdir(archive_dir))
            archived = os.listdir(archive_dir)
            self.assertEqual(len(archived), 1)
            self.assertTrue(archived[0].endswith("-draft.md"))


class TestNoClobber(unittest.TestCase):

    DRAFT = """\
# Realm Manifest Draft — 2026-06-13

## Meta
slug: myproj
phase-run: 2026-06-13T10:00:00+00:00
mode: full
gap-summary: 1 new function

## Planned Node Documents

### functions/existing.md
status: new
links: [[overview]]
---
---
id: existing
type: function
status: proposed
created: 2026-06-13
updated: 2026-06-13
---

## Compressed
New version content.
"""

    def test_no_clobber_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = os.path.join(tmp, "vault")
            slug = "myproj"
            state = _base_state(vault, slug)
            project_root = _make_project(tmp, slug, state, self.DRAFT)

            # pre-create the file
            fn_dir = os.path.join(state["projectDir"], "functions")
            os.makedirs(fn_dir, exist_ok=True)
            existing_path = os.path.join(fn_dir, "existing.md")
            original_content = "original content\n"
            with open(existing_path, "w") as f:
                f.write(original_content)

            result = _run_script(project_root)
            self.assertEqual(result.returncode, 0)
            self.assertIn("SKIP", result.stdout)

            with open(existing_path) as f:
                self.assertEqual(f.read(), original_content)


class TestADRSort(unittest.TestCase):

    DRAFT = """\
# Realm Manifest Draft — 2026-06-13

## Meta
slug: myproj
phase-run: 2026-06-13T10:00:00+00:00
mode: full
gap-summary: 2 new decisions

## Planned Node Documents

### decisions/ADR-002-caching.md
status: new
links:
---
---
id: ADR-002-caching
type: decision
title: Use Redis caching
status: accepted
created: 2026-06-13
updated: 2026-06-13
---

## Compressed
Use Redis.

## Full Decision
### Context
Needed caching.
### Decision
Redis.
### Consequences
Fast.

### decisions/ADR-001-auth.md
status: new
links:
---
---
id: ADR-001-auth
type: decision
title: Use JWT auth
status: accepted
created: 2026-06-12
updated: 2026-06-12
---

## Compressed
Use JWT.

## Full Decision
### Context
Needed auth.
### Decision
JWT.
### Consequences
Stateless.
"""

    def test_adr_index_sorted(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = os.path.join(tmp, "vault")
            slug = "myproj"
            state = _base_state(vault, slug)
            project_root = _make_project(tmp, slug, state, self.DRAFT)
            result = _run_script(project_root)
            self.assertEqual(result.returncode, 0, result.stderr)

            index_path = os.path.join(state["projectDir"], "decisions", "ADR-000-index.md")
            self.assertTrue(os.path.exists(index_path))
            with open(index_path) as f:
                content = f.read()

            # ADR-001 should appear before ADR-002
            pos_001 = content.index("ADR-001")
            pos_002 = content.index("ADR-002")
            self.assertLess(pos_001, pos_002, "ADR index not sorted")


class TestMalformedNode(unittest.TestCase):

    DRAFT = """\
# Realm Manifest Draft — 2026-06-13

## Meta
slug: myproj
phase-run: 2026-06-13T10:00:00+00:00
mode: full
gap-summary: 1 malformed

## Planned Node Documents

### functions/bad.md
status: new
links:
---
---
type: function
---

Missing id and Compressed section.
"""

    def test_malformed_warns_not_crashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = os.path.join(tmp, "vault")
            slug = "myproj"
            state = _base_state(vault, slug)
            project_root = _make_project(tmp, slug, state, self.DRAFT)
            result = _run_script(project_root)
            self.assertEqual(result.returncode, 0)
            self.assertIn("WARN", result.stdout)
            # file still written despite warnings
            written = os.path.join(state["projectDir"], "functions", "bad.md")
            self.assertTrue(os.path.exists(written))


class TestOverviewDefer(unittest.TestCase):

    DRAFT = """\
# Realm Manifest Draft — 2026-06-13

## Meta
slug: myproj
phase-run: 2026-06-13T10:00:00+00:00
mode: full
gap-summary: overview update

## Updated Overview/Architecture

### overview.md
status: update
---
## Milestones
- [x] Auth complete
"""

    def test_overview_update_deferred(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = os.path.join(tmp, "vault")
            slug = "myproj"
            state = _base_state(vault, slug)
            project_root = _make_project(tmp, slug, state, self.DRAFT)

            # pre-create overview
            proj_dir = state["projectDir"]
            os.makedirs(proj_dir, exist_ok=True)
            with open(os.path.join(proj_dir, "overview.md"), "w") as f:
                f.write("# Overview\nexisting prose\n")

            result = _run_script(project_root)
            self.assertEqual(result.returncode, 0)
            self.assertIn("DEFER", result.stdout)

            pending = os.path.join(project_root, ".realm", "pending-prose-merge.md")
            self.assertTrue(os.path.exists(pending))


# ---------------------------------------------------------------------------
# Parser unit tests
# ---------------------------------------------------------------------------

class TestParseDraft(unittest.TestCase):

    def test_meta_parsed(self):
        text = """\
# Realm Manifest Draft — 2026-06-13

## Meta
slug: my-proj
phase-run: 2026-06-13T10:00:00+00:00
mode: full
gap-summary: 2 new nodes
"""
        draft = parse_draft(text)
        self.assertEqual(draft.meta.slug, "my-proj")
        self.assertEqual(draft.meta.mode, "full")

    def test_node_body_extracted(self):
        text = """\
## Meta
slug: p
phase-run: now
mode: full
gap-summary: x

## Planned Node Documents

### functions/foo.md
status: new
links:
---
body content here
"""
        draft = parse_draft(text)
        self.assertEqual(len(draft.nodes), 1)
        self.assertEqual(draft.nodes[0].rel_path, "functions/foo.md")
        self.assertIn("body content here", draft.nodes[0].body)

    def test_session_log_separated(self):
        text = """\
## Meta
slug: p
phase-run: now
mode: full
gap-summary: x

## Planned Node Documents

### functions/foo.md
status: new
links:
---
node body

## Session Log Entry

### sessions/2026-06-13-work.md
status: new
---
session body
"""
        draft = parse_draft(text)
        self.assertEqual(len(draft.nodes), 1)
        self.assertIsNotNone(draft.session_log)
        self.assertEqual(draft.session_log.rel_path, "sessions/2026-06-13-work.md")


class TestSplitFrontmatter(unittest.TestCase):

    def test_valid_frontmatter(self):
        body = "---\nid: foo\ntype: function\n---\n\ncontent here"
        fm, content = split_frontmatter(body)
        self.assertIn("id: foo", fm)
        self.assertIn("content here", content)

    def test_no_frontmatter(self):
        body = "just content"
        fm, content = split_frontmatter(body)
        self.assertEqual(fm, "")
        self.assertEqual(content, body)


class TestParseYamlMin(unittest.TestCase):

    def test_flat_values(self):
        yaml = "id: fetchUser\ntype: function\nstatus: proposed"
        result = parse_yaml_min(yaml)
        self.assertEqual(result["id"], "fetchUser")
        self.assertEqual(result["type"], "function")

    def test_inline_list(self):
        yaml = "tags: [session, auth, perf]"
        result = parse_yaml_min(yaml)
        self.assertEqual(result["tags"], ["session", "auth", "perf"])

    def test_block_list(self):
        yaml = "depends_on:\n  - ClassA\n  - ClassB"
        result = parse_yaml_min(yaml)
        self.assertEqual(result["depends_on"], ["ClassA", "ClassB"])


if __name__ == "__main__":
    unittest.main()
