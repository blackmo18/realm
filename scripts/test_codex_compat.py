#!/usr/bin/env python3
"""Regression checks for Realm's Codex skill and installation contract."""

import json
import os
import re
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_SKILLS = {
    "realm-concise",
    "realm-facts",
    "realm-fathom",
    "realm-forge",
    "realm-orchestrate",
    "realm-planning",
    "realm-recall",
    "realm-status",
}
AGENT_MODELS = {
    "realm-agent-architect.toml": ("gpt-5.6-sol", "max"),
    "realm-agent-code-architect.toml": ("gpt-5.6-sol", "max"),
    "realm-agent-plan-implementor.toml": ("gpt-5.6-terra", "high"),
    "realm-agent-planning.toml": ("gpt-5.6-sol", "max"),
    "realm-agent-fathom.toml": ("gpt-5.6-terra", "high"),
    "realm-agent-forge.toml": ("gpt-5.6-terra", "medium"),
    "realm-agent-concise.toml": ("gpt-5.6-luna", "low"),
}
LEGACY_AGENT_FILES = {
    "architect.toml",
    "code-architect.toml",
    "plan-implementor.toml",
}
CURSOR_AGENT_FILES = {
    "realm-agent-architect.md",
    "realm-agent-code-architect.md",
    "realm-agent-plan-implementor.md",
    "realm-agent-planning.md",
    "realm-agent-fathom.md",
    "realm-agent-forge.md",
    "realm-agent-concise.md",
}


def run_installer(*args, env=None):
    return subprocess.run(
        ["node", str(ROOT / "bin" / "install.mjs"), *args],
        cwd=str(ROOT),
        env=env,
        check=True,
        text=True,
        capture_output=True,
    )


class CodexCompatibilityTests(unittest.TestCase):
    def test_piped_bootstrap_uses_github_clone_not_current_checkout(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            mock_bin = root / "bin"
            log_dir = root / "log"
            mock_bin.mkdir()
            log_dir.mkdir()

            git_mock = mock_bin / "git"
            git_mock.write_text(
                """#!/bin/sh
set -eu
test "$1" = "clone"
test "$2" = "--depth"
test "$3" = "1"
mkdir -p "$5/bin"
: > "$5/bin/install.mjs"
printf '%s\\n' "$4" > "$REALM_TEST_LOG/git-url"
printf '%s\\n' "$5" > "$REALM_TEST_LOG/clone-dir"
""",
                encoding="utf-8",
            )
            node_mock = mock_bin / "node"
            node_mock.write_text(
                """#!/bin/sh
set -eu
printf '%s\\n' "$1" > "$REALM_TEST_LOG/node-script"
printf '%s\\n' "$@" > "$REALM_TEST_LOG/node-args"
""",
                encoding="utf-8",
            )
            git_mock.chmod(git_mock.stat().st_mode | stat.S_IXUSR)
            node_mock.chmod(node_mock.stat().st_mode | stat.S_IXUSR)

            env = os.environ.copy()
            env["PATH"] = f"{mock_bin}{os.pathsep}{env['PATH']}"
            env["REALM_TEST_LOG"] = str(log_dir)
            result = subprocess.run(
                ["bash", "-s", "--", "--agent", "codex"],
                cwd=str(ROOT),
                env=env,
                input=(ROOT / "install.sh").read_text(encoding="utf-8"),
                check=True,
                text=True,
                capture_output=True,
            )

            clone_dir = Path(
                (log_dir / "clone-dir").read_text(encoding="utf-8").strip()
            )
            node_script = Path(
                (log_dir / "node-script").read_text(encoding="utf-8").strip()
            )
            self.assertEqual(
                (log_dir / "git-url").read_text(encoding="utf-8").strip(),
                "https://github.com/blackmo18/realm.git",
            )
            self.assertEqual(node_script, clone_dir / "bin" / "install.mjs")
            self.assertNotEqual(node_script, ROOT / "bin" / "install.mjs")
            self.assertNotIn("BASH_SOURCE", result.stderr)

    def test_only_public_skills_are_discoverable(self):
        discovered = {
            path.parent.name
            for path in (ROOT / "skills").rglob("SKILL.md")
        }
        self.assertEqual(discovered, PUBLIC_SKILLS)

    def test_skill_frontmatter_and_openai_metadata(self):
        for name in sorted(PUBLIC_SKILLS):
            skill_dir = ROOT / "skills" / name
            content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
            match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            self.assertIsNotNone(match, name)
            frontmatter = match.group(1)
            self.assertRegex(frontmatter, rf"(?m)^name:\s*{re.escape(name)}\s*$")
            self.assertRegex(frontmatter, r"(?m)^description:\s*(>|\S)")
            keys = set(re.findall(r"(?m)^([a-zA-Z0-9_-]+):", frontmatter))
            self.assertEqual(keys, {"name", "description"}, name)
            self.assertRegex(name, r"^[a-z0-9-]{1,64}$")

            openai_yaml = skill_dir / "agents" / "openai.yaml"
            self.assertTrue(openai_yaml.is_file(), name)
            metadata = openai_yaml.read_text(encoding="utf-8")
            self.assertIn(f"${name}", metadata)
            self.assertRegex(metadata, r'(?m)^\s+short_description: "[^"\n]{25,64}"$')

    def test_skill_resources_are_host_neutral(self):
        offenders = []
        for path in (ROOT / "skills").rglob("*.md"):
            if ".claude/skills" in path.read_text(encoding="utf-8"):
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(offenders, [])

    def test_codex_agent_model_tiers(self):
        agent_dir = ROOT / ".codex" / "agents"
        actual = {path.name for path in agent_dir.glob("*.toml")}
        self.assertEqual(actual, set(AGENT_MODELS))
        for filename, (model, effort) in AGENT_MODELS.items():
            path = agent_dir / filename
            content = path.read_text(encoding="utf-8")
            self.assertIn(f'name = "{path.stem}"', content)
            self.assertIn(f'model = "{model}"', content)
            self.assertIn(f'model_reasoning_effort = "{effort}"', content)
            self.assertRegex(content, r'(?m)^developer_instructions = """')
            self.assertNotIn("/realm-", content)
            self.assertNotIn("skills/realm-", content)

    def test_shared_agents_use_realm_agent_namespace(self):
        for path in (ROOT / "agents").glob("*.md"):
            self.assertTrue(path.stem.startswith("realm-agent-"), path.name)
            content = path.read_text(encoding="utf-8")
            self.assertRegex(
                content,
                rf"(?m)^name:\s*{re.escape(path.stem)}\s*$",
                path.name,
            )

    def test_global_codex_install_respects_codex_home(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir) / "custom-codex"
            agents_dir = codex_home / "agents"
            stale_helper = (
                codex_home
                / "skills"
                / "realm-orchestrate"
                / "analyze"
                / "SKILL.md"
            )
            unrelated_skill = codex_home / "skills" / "user-owned-skill" / "SKILL.md"
            agents_dir.mkdir(parents=True)
            stale_helper.parent.mkdir(parents=True)
            stale_helper.write_text("stale", encoding="utf-8")
            unrelated_skill.parent.mkdir(parents=True)
            unrelated_skill.write_text("user-owned", encoding="utf-8")
            for filename in LEGACY_AGENT_FILES:
                (agents_dir / filename).write_text("legacy", encoding="utf-8")
            env = os.environ.copy()
            env["CODEX_HOME"] = str(codex_home)
            result = run_installer("--agent", "codex", env=env)
            self.assertIn("installed globally for Codex", result.stdout)
            for name in PUBLIC_SKILLS:
                self.assertTrue((codex_home / "skills" / name / "SKILL.md").is_file())
            for filename in AGENT_MODELS:
                self.assertTrue((codex_home / "agents" / filename).is_file())
            for filename in LEGACY_AGENT_FILES:
                self.assertFalse((codex_home / "agents" / filename).exists())
            self.assertFalse(stale_helper.exists())
            self.assertEqual(
                unrelated_skill.read_text(encoding="utf-8"),
                "user-owned",
            )

    def test_local_codex_install_uses_shared_skill_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir) / "project"
            project.mkdir()
            run_installer("--agent", "codex", "--local", str(project))
            for name in PUBLIC_SKILLS:
                self.assertTrue((project / ".agents" / "skills" / name / "SKILL.md").is_file())
            self.assertFalse((project / ".codex" / "skills").exists())
            for filename in AGENT_MODELS:
                self.assertTrue((project / ".codex" / "agents" / filename).is_file())

    def test_local_cursor_install_uses_portable_skills_and_native_agents(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir) / "project"
            project.mkdir()
            run_installer("--agent", "cursor", "--local", str(project))
            for name in PUBLIC_SKILLS:
                self.assertTrue(
                    (project / ".agents" / "skills" / name / "SKILL.md").is_file()
                )
            self.assertFalse((project / ".cursor" / "skills").exists())
            agent_dir = project / ".cursor" / "agents"
            self.assertEqual(
                {path.name for path in agent_dir.glob("*.md")},
                CURSOR_AGENT_FILES,
            )
            for path in agent_dir.glob("*.md"):
                content = path.read_text(encoding="utf-8")
                self.assertIn("model: inherit", content)
                self.assertNotRegex(content, r"(?m)^tools:")

    def test_forge_accepts_cursor_and_writes_portable_anchor(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = root / "project"
            vault = root / "vault"
            project.mkdir()
            subprocess.run(
                [
                    "python3",
                    str(ROOT / "skills" / "realm-forge" / "scripts" / "forge_init.py"),
                    "--project-root", str(project),
                    "--vault-path", str(vault),
                    "--project-slug", "sample",
                    "--host", "cursor",
                ],
                check=True,
                text=True,
                capture_output=True,
            )
            self.assertTrue((project / "AGENTS.md").is_file())

    def test_forge_migrates_retired_pipeline_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = root / "project"
            vault = root / "vault"
            realm_dir = project / ".realm"
            realm_dir.mkdir(parents=True)
            legacy_state = {
                "vaultPath": str(vault),
                "projectSlug": "sample",
                "projectDir": str(vault / "projects" / "sample"),
                "phase": {"lastRun": None, "draftReady": True},
                "manifest": {"lastRun": "2026-01-01T00:00:00Z"},
                "pendingDrafts": ["old-draft"],
                "nodeIndex": {"ids": {"old": "decisions/old.md"}},
                "customState": {"keep": True},
                "docs": {},
            }
            (realm_dir / "realm-state.json").write_text(
                json.dumps(legacy_state), encoding="utf-8"
            )

            subprocess.run(
                [
                    "python3",
                    str(ROOT / "skills" / "realm-forge" / "scripts" / "forge_init.py"),
                    "--project-root", str(project),
                    "--vault-path", str(vault),
                    "--project-slug", "sample",
                    "--host", "codex",
                ],
                check=True,
                text=True,
                capture_output=True,
            )
            state = json.loads((realm_dir / "realm-state.json").read_text(encoding="utf-8"))
            for key in ("phase", "manifest", "pendingDrafts", "nodeIndex"):
                self.assertNotIn(key, state)
            self.assertEqual(state["customState"], {"keep": True})


if __name__ == "__main__":
    unittest.main()
