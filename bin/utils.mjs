import fs from 'fs';
import os from 'os';
import path from 'path';
import childProcess from 'child_process';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export const DEFAULT_REPO = 'blackmo18/realm';
export const DEFAULT_AGENT = 'codex';
export const SKILLS_CLI_AGENTS = new Set(['cursor', 'gemini']);
export const SUPPORTED_AGENTS = new Set(['claude', 'codex', ...SKILLS_CLI_AGENTS]);

export const INSTALL_EXCLUDES = new Set([
  '.git',
  '.gitignore',
  '.DS_Store',
  '.realm',
  'node_modules',
]);

export const LEGACY_SHARED_AGENT_FILES = [
  'architect.md',
  'code-architect.md',
  'plan-implementor.md',
];
export const LEGACY_CODEX_AGENT_FILES = [
  'architect.toml',
  'code-architect.toml',
  'plan-implementor.toml',
];
export const LEGACY_CURSOR_AGENT_FILES = LEGACY_SHARED_AGENT_FILES;

export function detectRepoRoot() {
  const root = path.resolve(__dirname, '..');
  const requiredPaths = [
    'README.md',
    'INSTALL.md',
    'skills',
    'agents',
    'bin/install.mjs',
  ];

  return requiredPaths.every((relativePath) => fs.existsSync(path.join(root, relativePath)))
    ? root
    : null;
}

export function copySkillsDir(sourceDir, destinationDir) {
  ensureDir(destinationDir);
  for (const entry of fs.readdirSync(sourceDir, { withFileTypes: true })) {
    if (INSTALL_EXCLUDES.has(entry.name)) {
      continue;
    }
    const srcPath = path.join(sourceDir, entry.name);
    const dstPath = path.join(destinationDir, entry.name);

    if (entry.isDirectory()) {
      if (fs.existsSync(dstPath)) {
        fs.rmSync(dstPath, { recursive: true, force: true });
      }
      copyDirectoryRecursive(srcPath, dstPath);
    } else if (entry.isFile()) {
      fs.copyFileSync(srcPath, dstPath);
    }
  }
}

export function copyDirectoryRecursive(src, dst) {
  ensureDir(dst);
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    if (INSTALL_EXCLUDES.has(entry.name)) {
      continue;
    }
    const srcPath = path.join(src, entry.name);
    const dstPath = path.join(dst, entry.name);

    if (entry.isDirectory()) {
      copyDirectoryRecursive(srcPath, dstPath);
    } else if (entry.isFile()) {
      fs.copyFileSync(srcPath, dstPath);
    }
  }
}

export function ensureDir(targetDir) {
  fs.mkdirSync(targetDir, { recursive: true });
}

export function hasCommand(command) {
  const probe = process.platform === 'win32' ? 'where' : 'which';
  const result = childProcess.spawnSync(probe, [command], { stdio: 'ignore' });
  return result.status === 0;
}

export function expandHome(targetPath) {
  if (!targetPath) {
    return targetPath;
  }

  if (targetPath === '~') {
    return os.homedir();
  }

  if (targetPath.startsWith('~/')) {
    return path.join(os.homedir(), targetPath.slice(2));
  }

  return targetPath;
}

export function removeLegacyAgentFiles(destinationDir, filenames) {
  for (const filename of filenames) {
    const legacyPath = path.join(destinationDir, filename);
    if (!fs.existsSync(legacyPath)) {
      continue;
    }
    fs.rmSync(legacyPath, { force: true });
    info(`Removed legacy agent: ${legacyPath}`);
  }
}

export function copyAgentFiles(sourceDir, destinationDir) {
  if (!fs.existsSync(sourceDir)) {
    return;
  }

  for (const entry of fs.readdirSync(sourceDir, { withFileTypes: true })) {
    if (!entry.isFile() || path.extname(entry.name) !== '.md') {
      continue;
    }

    fs.copyFileSync(
      path.join(sourceDir, entry.name),
      path.join(destinationDir, entry.name)
    );
  }

  removeLegacyAgentFiles(destinationDir, LEGACY_SHARED_AGENT_FILES);
}

export function copyRealmRepo(sourceDir, destinationDir) {
  ensureDir(destinationDir);

  for (const entry of fs.readdirSync(sourceDir, { withFileTypes: true })) {
    if (INSTALL_EXCLUDES.has(entry.name)) {
      continue;
    }

    const sourcePath = path.join(sourceDir, entry.name);
    const destinationPath = path.join(destinationDir, entry.name);

    if (entry.isDirectory()) {
      copyRealmRepo(sourcePath, destinationPath);
      continue;
    }

    if (entry.isFile()) {
      ensureDir(path.dirname(destinationPath));
      fs.copyFileSync(sourcePath, destinationPath);
    }
  }
}

export function defaultClaudeBaseDir() {
  return path.join(os.homedir(), '.claude');
}

export function defaultClaudeMarketplaceDir() {
  return path.join(defaultClaudeBaseDir(), 'plugins', 'marketplaces');
}

export function defaultClaudePluginDir() {
  return path.join(defaultClaudeMarketplaceDir(), 'realm');
}

export function defaultCodexAgentsDir() {
  return path.join(defaultCodexBaseDir(), 'agents');
}

export function defaultCodexSkillsDir() {
  return path.join(defaultCodexBaseDir(), 'skills');
}

export function defaultCodexBaseDir() {
  return process.env.CODEX_HOME
    ? path.resolve(expandHome(process.env.CODEX_HOME))
    : path.join(os.homedir(), '.codex');
}

export function defaultGeminiAgentsDir() {
  return path.join(os.homedir(), '.gemini', 'agents');
}

export function defaultCursorAgentsDir() {
  return path.join(os.homedir(), '.cursor', 'agents');
}

export function agentLabel(agent) {
  const labels = {
    claude: 'Claude Code',
    cursor: 'Cursor',
    codex: 'Codex',
    gemini: 'Gemini',
  };
  return labels[agent] || agent;
}

export function skillCommand(agent, skillName) {
  return `${agent === 'codex' ? '$' : '/'}${skillName}`;
}

export function info(message) {
  process.stdout.write(`${message}\n`);
}

export function success(message) {
  process.stdout.write(`${message}\n`);
}

export function warn(message) {
  process.stderr.write(`Warning: ${message}\n`);
}

export function fail(message) {
  process.stderr.write(`${message}\n`);
  process.exit(1);
}
