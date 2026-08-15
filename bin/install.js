#!/usr/bin/env node
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const childProcess = require('child_process');

const DEFAULT_REPO = 'blackmo18/realm';
const DEFAULT_AGENT = 'codex';
const SKILLS_CLI_AGENTS = new Set(['cursor', 'gemini']);
const SUPPORTED_AGENTS = new Set(['claude', 'codex', ...SKILLS_CLI_AGENTS]);
const INSTALL_EXCLUDES = new Set([
  '.git',
  '.gitignore',
  '.DS_Store',
  '.realm',
  'node_modules',
]);
const LEGACY_SHARED_AGENT_FILES = [
  'architect.md',
  'code-architect.md',
  'plan-implementor.md',
];
const LEGACY_CODEX_AGENT_FILES = [
  'architect.toml',
  'code-architect.toml',
  'plan-implementor.toml',
];

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

  if (options.isLocal) {
    installLocal(options, repoRoot);
    return;
  }

  if (options.agent === 'codex') {
    installForCodex(options, repoRoot);
    return;
  }

  if (SKILLS_CLI_AGENTS.has(options.agent)) {
    installForSkillsCli(options, repoRoot);
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
    isLocal: false,
    targetDir: null,
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
      case '--local':
      case '-l': {
        options.isLocal = true;
        const nextArg = argv[index + 1];
        if (nextArg && !nextArg.startsWith('-')) {
          options.targetDir = expandHome(nextArg);
          index += 1;
        } else {
          options.targetDir = process.cwd();
        }
        break;
      }
      case '--target-dir':
      case '--project-dir':
        options.isLocal = true;
        options.targetDir = expandHome(requireValue(argv, ++index, arg));
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
  --local [dir], -l [dir]  Install locally into a project workspace (defaults to current directory)
  --target-dir <dir>       Explicit project destination directory for local installation
  --repo <owner/repo>      Repo slug used by remote and Skills CLI installs. Default: ${DEFAULT_REPO}
  --plugin-dir <path>      Claude plugin destination. Default: ${defaultClaudePluginDir()}
  --dry-run                Print planned actions without changing anything
  --force                  Overwrite existing files in local or Claude install
  -h, --help               Show this help

Examples:
  node bin/install.js
  node bin/install.js --dry-run
  node bin/install.js --agent gemini
  node bin/install.js --agent gemini --local
  node bin/install.js --agent gemini --local /path/to/project
  node bin/install.js --agent codex --local
  node bin/install.js --agent cursor --local
  node bin/install.js --agent claude --local
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

function installLocal(options, repoRoot) {
  const targetDir = path.resolve(options.targetDir || process.cwd());
  const agent = options.agent;
  const skillsSrc = path.join(repoRoot, 'skills');

  info(`Realm local install target: ${targetDir}`);
  info(`Agent: ${agent}`);

  const plannedActions = [];

  // Determine destinations
  let targetSkillsDirs = [];
  let agentsSrc = null;
  let targetAgentsDir = null;
  let agentExt = 'md';

  if (agent === 'gemini') {
    targetSkillsDirs.push(path.join(targetDir, '.agents', 'skills'));
    agentsSrc = path.join(repoRoot, 'agents');
    targetAgentsDir = path.join(targetDir, '.gemini', 'agents');
    agentExt = '.md';
  } else if (agent === 'codex') {
    targetSkillsDirs.push(path.join(targetDir, '.agents', 'skills'));
    agentsSrc = path.join(repoRoot, '.codex', 'agents');
    targetAgentsDir = path.join(targetDir, '.codex', 'agents');
    agentExt = '.toml';
    const legacySkillsDir = path.join(targetDir, '.codex', 'skills');
    if (fs.existsSync(legacySkillsDir)) {
      warn(`Legacy Codex skill directory detected: ${legacySkillsDir}`);
      warn('Realm now uses .agents/skills for project-scoped Codex skills; remove old Realm copies after verifying this install.');
    }
  } else if (agent === 'cursor') {
    targetSkillsDirs.push(path.join(targetDir, '.cursor', 'skills'));
    targetSkillsDirs.push(path.join(targetDir, '.agents', 'skills'));
  } else if (agent === 'claude') {
    targetSkillsDirs.push(path.join(targetDir, '.claude', 'skills'));
    agentsSrc = path.join(repoRoot, 'agents');
    targetAgentsDir = path.join(targetDir, '.claude', 'agents');
    agentExt = '.md';
  }

  for (const sDir of targetSkillsDirs) {
    plannedActions.push(`- Copy skills (${skillsSrc}) -> ${sDir}`);
  }
  if (agentsSrc && targetAgentsDir && fs.existsSync(agentsSrc)) {
    plannedActions.push(`- Copy agent definitions (${agentsSrc}/*${agentExt}) -> ${targetAgentsDir}`);
  }

  if (options.dryRun) {
    process.stdout.write('Planned Local Actions:\n');
    for (const action of plannedActions) {
      process.stdout.write(`${action}\n`);
    }
    success('Dry run complete.');
    return;
  }

  // Execute copy
  for (const sDir of targetSkillsDirs) {
    ensureDir(sDir);
    copySkillsDir(skillsSrc, sDir);
    info(`Installed skills to ${sDir}`);
  }

  if (agentsSrc && targetAgentsDir && fs.existsSync(agentsSrc)) {
    ensureDir(targetAgentsDir);
    for (const entry of fs.readdirSync(agentsSrc, { withFileTypes: true })) {
      if (entry.isFile() && entry.name.endsWith(agentExt)) {
        const sourcePath = path.join(agentsSrc, entry.name);
        const targetPath = path.join(targetAgentsDir, entry.name);
        if (agent === 'gemini') {
          writeGeminiAgent(sourcePath, targetPath);
        } else {
          fs.copyFileSync(sourcePath, targetPath);
        }
        info(`Installed agent: ${path.join(targetAgentsDir, entry.name)}`);
      }
    }
    removeLegacyAgentFiles(
      targetAgentsDir,
      agentExt === '.toml' ? LEGACY_CODEX_AGENT_FILES : LEGACY_SHARED_AGENT_FILES
    );
  }

  process.stdout.write('\n');
  success(`Realm is installed locally for ${agentLabel(agent)} in ${targetDir}.`);
  process.stdout.write(
    'Next steps:\n' +
    `1. Open ${targetDir} in ${agentLabel(agent)}.\n` +
    `2. Run ${skillCommand(agent, 'realm-forge')} to bootstrap local Realm vault state for this project.\n` +
    `3. Query with ${skillCommand(agent, 'realm-recall')} or investigate with ${skillCommand(agent, 'realm-fathom')}.\n`
  );
}

function copySkillsDir(sourceDir, destinationDir) {
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

function copyDirectoryRecursive(src, dst) {
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

function installForCodex(options, repoRoot) {
  const skillsSrc = path.join(repoRoot, 'skills');
  const skillsDir = defaultCodexSkillsDir();
  const agentsDir = defaultCodexAgentsDir();

  info(`Realm install source: ${repoRoot}`);
  info('Agent: codex');
  info(`Codex skills dir: ${skillsDir}`);
  info(`Codex agents dir: ${agentsDir}`);

  const legacySkillsDir = path.join(os.homedir(), '.agents', 'skills');
  if (fs.existsSync(legacySkillsDir)) {
    warn(`Legacy Skills CLI directory detected: ${legacySkillsDir}`);
    warn('If it contains old Realm copies, remove them after confirming the native Codex install.');
  }

  if (options.dryRun) {
    process.stdout.write('Planned Codex native install:\n');
    process.stdout.write(`- Copy skills/* into ${skillsDir}\n`);
    process.stdout.write(`- Copy .codex/agents/*.toml into ${agentsDir}\n`);
    success('Dry run complete.');
    return;
  }

  ensureDir(skillsDir);
  copySkillsDir(skillsSrc, skillsDir);
  info(`Installed Realm skills to ${skillsDir}`);
  installCodexAgents(repoRoot);

  process.stdout.write('\n');
  success('Realm is installed globally for Codex.');
  process.stdout.write(
    'Next steps:\n' +
    '1. Restart Codex or open a new session so the new skills are loaded cleanly.\n' +
    '2. In your project, run $realm-forge to bootstrap the local Realm state.\n' +
    '3. Query with $realm-recall or investigate with $realm-fathom.\n'
  );
}

function installForSkillsCli(options, repoRoot) {
  const command = ['npx', 'skills', 'add', options.repo, '-a', options.agent];
  if (options.force) {
    warn('--force is only used by the Claude Code local plugin installer; ignoring it for Skills CLI install.');
  }

  info(`Realm install target: ${options.repo}`);
  info(`Agent: ${options.agent}`);
  info(`Command: ${command.join(' ')}`);
  if (options.agent === 'codex') {
    info(`Codex agents dir: ${defaultCodexAgentsDir()}`);
  } else if (options.agent === 'gemini') {
    info(`Gemini agents dir: ${defaultGeminiAgentsDir()}`);
  }

  if (options.dryRun) {
    if (options.agent === 'codex') {
      process.stdout.write('Planned Codex native agent install:\n');
      process.stdout.write(`- Copy .codex/agents/*.toml into ${defaultCodexAgentsDir()}\n`);
    } else if (options.agent === 'gemini') {
      process.stdout.write('Planned Gemini native agent install:\n');
      process.stdout.write(`- Copy agents/*.md into ${defaultGeminiAgentsDir()}\n`);
    }
    success('Dry run complete.');
    return;
  }

  if (!hasCommand('npx')) {
    fail(`npx is required to install Realm for ${agentLabel(options.agent)}. Install Node.js first.`);
  }

  const result = childProcess.spawnSync(command[0], command.slice(1), {
    stdio: 'inherit',
  });

  if (result.status !== 0) {
    fail(`${agentLabel(options.agent)} install failed with exit code ${result.status ?? 'unknown'}.`);
  }

  if (options.agent === 'codex') {
    installCodexAgents(repoRoot);
  } else if (options.agent === 'gemini') {
    installGeminiAgents(repoRoot);
  }

  process.stdout.write('\n');
  success(`Realm is installed globally for ${agentLabel(options.agent)}.`);
  process.stdout.write(
    'Next steps:\n' +
    `1. Restart ${agentLabel(options.agent)} or open a new session so the new skills are loaded cleanly.\n` +
    `2. In your project, run ${skillCommand(options.agent, 'realm-forge')} to bootstrap the local Realm state.\n` +
    `3. Query with ${skillCommand(options.agent, 'realm-recall')} or investigate with ${skillCommand(options.agent, 'realm-fathom')}.\n`
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

  removeLegacyAgentFiles(destinationDir, LEGACY_SHARED_AGENT_FILES);
}

function installCodexAgents(repoRoot) {
  const sourceDir = path.join(repoRoot, '.codex', 'agents');
  const destinationDir = defaultCodexAgentsDir();

  if (!fs.existsSync(sourceDir)) {
    warn(`Codex native agents not found at ${sourceDir}`);
    warn('Realm skills were installed, but Codex subagent definitions were not copied.');
    return;
  }

  ensureDir(destinationDir);

  for (const entry of fs.readdirSync(sourceDir, { withFileTypes: true })) {
    if (!entry.isFile() || path.extname(entry.name) !== '.toml') {
      continue;
    }

    fs.copyFileSync(
      path.join(sourceDir, entry.name),
      path.join(destinationDir, entry.name)
    );
    info(`Installed Codex agent: ${path.join(destinationDir, entry.name)}`);
  }

  removeLegacyAgentFiles(destinationDir, LEGACY_CODEX_AGENT_FILES);
}

function installGeminiAgents(repoRoot) {
  const sourceDir = path.join(repoRoot, 'agents');
  const destinationDir = defaultGeminiAgentsDir();

  if (!fs.existsSync(sourceDir)) {
    warn(`Gemini native agents not found at ${sourceDir}`);
    warn('Realm skills were installed, but Gemini subagent definitions were not copied.');
    return;
  }

  ensureDir(destinationDir);

  for (const entry of fs.readdirSync(sourceDir, { withFileTypes: true })) {
    if (!entry.isFile() || path.extname(entry.name) !== '.md') {
      continue;
    }

    writeGeminiAgent(
      path.join(sourceDir, entry.name),
      path.join(destinationDir, entry.name)
    );
    info(`Installed Gemini agent: ${path.join(destinationDir, entry.name)}`);
  }

  removeLegacyAgentFiles(destinationDir, LEGACY_SHARED_AGENT_FILES);
}

function removeLegacyAgentFiles(destinationDir, filenames) {
  for (const filename of filenames) {
    const legacyPath = path.join(destinationDir, filename);
    if (!fs.existsSync(legacyPath)) {
      continue;
    }
    fs.rmSync(legacyPath, { force: true });
    info(`Removed legacy agent: ${legacyPath}`);
  }
}

function writeGeminiAgent(sourcePath, destinationPath) {
  const modelMap = {
    opus: 'gemini-3.1-pro-preview',
    sonnet: 'gemini-3.1-pro-preview',
    haiku: 'gemini-3.6-flash',
  };
  const source = fs.readFileSync(sourcePath, 'utf8');
  const adapted = source.replace(/^tools:\s*\[[^\n]*\]\s*\n/m, '').replace(
    /^model:\s*(opus|sonnet|haiku)\s*$/m,
    (_match, tier) => `model: ${modelMap[tier]}`
  );
  fs.writeFileSync(destinationPath, adapted);
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

function defaultCodexAgentsDir() {
  return path.join(defaultCodexBaseDir(), 'agents');
}

function defaultCodexSkillsDir() {
  return path.join(defaultCodexBaseDir(), 'skills');
}

function defaultCodexBaseDir() {
  return process.env.CODEX_HOME
    ? path.resolve(expandHome(process.env.CODEX_HOME))
    : path.join(os.homedir(), '.codex');
}

function defaultGeminiAgentsDir() {
  return path.join(os.homedir(), '.gemini', 'agents');
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

function skillCommand(agent, skillName) {
  return `${agent === 'codex' ? '$' : '/'}${skillName}`;
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
