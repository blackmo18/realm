#!/usr/bin/env python3
"""Regression checks for Realm's Codex skill and installation contract."""

import json
import os
import re
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
    "realm-planning",
    "realm-recall",
    "realm-status",
}
AGENT_MODELS = {
    "architect.toml": ("gpt-5.6-sol", "max"),
    "code-architect.toml": ("gpt-5.6-sol", "max"),
    "realm-agent-planning.toml": ("gpt-5.6-sol", "max"),
    "realm-agent-fathom.toml": ("gpt-5.6-terra", "high"),
    "realm-agent-forge.toml": ("gpt-5.6-terra", "medium"),
    "realm-agent-concise.toml": ("gpt-5.6-luna", "low"),
}


def run_installer(*args, env=None):
    return subprocess.run(
        ["node", str(ROOT / "bin" / "install.js"), *args],
        cwd=str(ROOT),
        env=env,
        check=True,
        text=True,
        capture_output=True,
    )


class CodexCompatibilityTests(unittest.TestCase):
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
            content = (agent_dir / filename).read_text(encoding="utf-8")
            self.assertIn(f'model = "{model}"', content)
            self.assertIn(f'model_reasoning_effort = "{effort}"', content)
            self.assertRegex(content, r'(?m)^developer_instructions = """')
            self.assertNotIn("/realm-", content)
            self.assertNotIn("skills/realm-", content)

    def test_global_codex_install_respects_codex_home(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir) / "custom-codex"
            env = os.environ.copy()
            env["CODEX_HOME"] = str(codex_home)
            result = run_installer("--agent", "codex", env=env)
            self.assertIn("installed globally for Codex", result.stdout)
            for name in PUBLIC_SKILLS:
                self.assertTrue((codex_home / "skills" / name / "SKILL.md").is_file())
            for filename in AGENT_MODELS:
                self.assertTrue((codex_home / "agents" / filename).is_file())

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
