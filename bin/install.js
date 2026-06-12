#!/usr/bin/env node
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const childProcess = require('child_process');

const DEFAULT_REPO = 'blackmo18/realm';
const DEFAULT_AGENT = 'codex';
const SKILLS_CLI_AGENTS = new Set(['codex', 'cursor', 'gemini']);
const SUPPORTED_AGENTS = new Set(['claude', ...SKILLS_CLI_AGENTS]);
const INSTALL_EXCLUDES = new Set([
  '.git',
  '.gitignore',
  '.DS_Store',
  '.realm',
  'node_modules',
]);

function main() {
  const options = parseArgs(process.argv.slice(2));

  if (options.help) {
    printHelp();
    return;
  }

  const repoRoot = detectRepoRoot();
  if (!repoRoot) {
    fail('Unable to locate the Realm repo root from bin/install.js.');
  }

  if (SKILLS_CLI_AGENTS.has(options.agent)) {
    installForSkillsCli(options);
    return;
  }

  installForClaude(options, repoRoot);
}

function parseArgs(argv) {
  const options = {
    agent: DEFAULT_AGENT,
    dryRun: false,
    force: false,
    help: false,
    pluginDir: defaultClaudePluginDir(),
    repo: DEFAULT_REPO,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];

    switch (arg) {
      case '--dry-run':
        options.dryRun = true;
        break;
      case '--force':
        options.force = true;
        break;
      case '--help':
      case '-h':
        options.help = true;
        break;
      case '--agent':
        options.agent = requireValue(argv, ++index, '--agent');
        break;
      case '--repo':
        options.repo = requireValue(argv, ++index, '--repo');
        break;
      case '--plugin-dir':
        options.pluginDir = expandHome(requireValue(argv, ++index, '--plugin-dir'));
        break;
      default:
        fail(`Unknown argument: ${arg}\nRun 'node bin/install.js --help' for usage.`);
    }
  }

  if (!SUPPORTED_AGENTS.has(options.agent)) {
    fail(`Unsupported agent: ${options.agent}\nSupported agents: claude, cursor, codex, gemini`);
  }

  return options;
}

function requireValue(argv, index, flag) {
  const value = argv[index];
  if (!value || value.startsWith('--')) {
    fail(`Missing value for ${flag}`);
  }
  return value;
}

function printHelp() {
  process.stdout.write(`Realm installer

Usage:
  node bin/install.js [options]

Options:
  --agent <agent>          Install target: claude, cursor, codex, gemini. Default: codex
  --repo <owner/repo>      Repo slug used for Skills CLI installs. Default: ${DEFAULT_REPO}
  --plugin-dir <path>      Claude plugin destination. Default: ${defaultClaudePluginDir()}
  --dry-run                Print planned actions without changing anything
  --force                  Overwrite existing Claude install
  -h, --help               Show this help

Examples:
  node bin/install.js
  node bin/install.js --dry-run
  node bin/install.js --agent cursor
  node bin/install.js --agent gemini
  node bin/install.js --agent claude
  node bin/install.js --agent claude --plugin-dir ~/.claude/plugins/marketplaces/realm
`);
}

function detectRepoRoot() {
  const root = path.resolve(__dirname, '..');
  const requiredPaths = [
    'README.md',
    'INSTALL.md',
    'skills',
    'agents',
    'bin/install.js',
  ];

  return requiredPaths.every((relativePath) => fs.existsSync(path.join(root, relativePath)))
    ? root
    : null;
}

function installForSkillsCli(options) {
  if (!hasCommand('npx')) {
    fail(`npx is required to install Realm for ${agentLabel(options.agent)}. Install Node.js first.`);
  }

  const command = ['npx', 'skills', 'add', options.repo, '-a', options.agent];
  if (options.force) {
    warn('--force is only used by the Claude Code local plugin installer; ignoring it for Skills CLI install.');
  }

  info(`Realm install target: ${options.repo}`);
  info(`Agent: ${options.agent}`);
  info(`Command: ${command.join(' ')}`);

  if (options.dryRun) {
    success('Dry run complete.');
    return;
  }

  const result = childProcess.spawnSync(command[0], command.slice(1), {
    stdio: 'inherit',
  });

  if (result.status !== 0) {
    fail(`${agentLabel(options.agent)} install failed with exit code ${result.status ?? 'unknown'}.`);
  }

  process.stdout.write('\n');
  success(`Realm is installed for ${agentLabel(options.agent)}.`);
  process.stdout.write(
    'Next steps:\n' +
    `1. Restart ${agentLabel(options.agent)} or open a new session so the new skills are loaded cleanly.\n` +
    '2. In your project, run /realm-forge to bootstrap the local Realm state.\n' +
    '3. Then run /realm-phase and /realm-manifest for the first vault sync.\n'
  );
}

function installForClaude(options, repoRoot) {
  const pluginDir = options.pluginDir;
  const agentsDir = path.join(defaultClaudeBaseDir(), 'agents');
  const cavemanPath = path.join(defaultClaudeMarketplaceDir(), 'caveman');
  const pluginExists = fs.existsSync(pluginDir);

  info(`Realm source: ${repoRoot}`);
  info(`Claude plugin dir: ${pluginDir}`);
  info(`Claude agents dir: ${agentsDir}`);

  if (options.dryRun) {
    process.stdout.write('Planned actions:\n');
    process.stdout.write(`- Copy repo into ${pluginDir}${pluginExists ? ' (already exists)' : ''}\n`);
    process.stdout.write(`- Copy agent markdown files into ${agentsDir}\n`);
    if (pluginExists && !options.force) {
      process.stdout.write('- Refuse overwrite unless you rerun with --force\n');
    }
    if (!fs.existsSync(cavemanPath)) {
      process.stdout.write(`- Warn that caveman is not present at ${cavemanPath}\n`);
    }
    process.stdout.write('- Remind you to run /plugin marketplace add inside Claude Code\n');
    success('Dry run complete.');
    return;
  }

  if (pluginExists && !options.force) {
    fail(
      `Claude plugin destination already exists: ${pluginDir}\n` +
      'Use --force to replace it, or choose a different --plugin-dir.'
    );
  }

  ensureDir(path.dirname(pluginDir));
  if (pluginExists) {
    fs.rmSync(pluginDir, { recursive: true, force: true });
  }
  copyRealmRepo(repoRoot, pluginDir);

  ensureDir(agentsDir);
  copyAgentFiles(path.join(repoRoot, 'agents'), agentsDir);

  process.stdout.write('\n');
  success('Realm files copied for Claude Code.');
  process.stdout.write(`Plugin path: ${pluginDir}\n`);

  if (!fs.existsSync(cavemanPath)) {
    warn(`caveman dependency not found at ${cavemanPath}`);
    process.stdout.write('Install caveman first if you have not already.\n');
  }

  process.stdout.write(
    '\nNext steps inside Claude Code:\n' +
    `1. Run /plugin marketplace add ${pluginDir}\n` +
    '2. Restart Claude Code so the refreshed skills are loaded.\n' +
    '3. In your project, run /realm-forge to bootstrap local Realm state.\n'
  );
}

function copyRealmRepo(sourceDir, destinationDir) {
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

function copyAgentFiles(sourceDir, destinationDir) {
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
}

function ensureDir(targetDir) {
  fs.mkdirSync(targetDir, { recursive: true });
}

function hasCommand(command) {
  const probe = process.platform === 'win32' ? 'where' : 'which';
  const result = childProcess.spawnSync(probe, [command], { stdio: 'ignore' });
  return result.status === 0;
}

function expandHome(targetPath) {
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

function defaultClaudeBaseDir() {
  return path.join(os.homedir(), '.claude');
}

function defaultClaudeMarketplaceDir() {
  return path.join(defaultClaudeBaseDir(), 'plugins', 'marketplaces');
}

function defaultClaudePluginDir() {
  return path.join(defaultClaudeMarketplaceDir(), 'realm');
}

function agentLabel(agent) {
  const labels = {
    claude: 'Claude Code',
    cursor: 'Cursor',
    codex: 'Codex',
    gemini: 'Gemini',
  };
  return labels[agent] || agent;
}

function info(message) {
  process.stdout.write(`${message}\n`);
}

function success(message) {
  process.stdout.write(`${message}\n`);
}

function warn(message) {
  process.stderr.write(`Warning: ${message}\n`);
}

function fail(message) {
  process.stderr.write(`${message}\n`);
  process.exit(1);
}

main();
