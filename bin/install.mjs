#!/usr/bin/env node
import {
  DEFAULT_REPO,
  DEFAULT_AGENT,
  SUPPORTED_AGENTS,
  detectRepoRoot,
  expandHome,
  defaultClaudePluginDir,
  fail
} from './utils.mjs';

import { installForGemini } from './gemini.mjs';
import { installForCodex } from './codex.mjs';
import { installForCursor } from './cursor.mjs';
import { installForClaude } from './claude.mjs';

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
        fail(`Unknown argument: ${arg}\nRun 'node bin/install.mjs --help' for usage.`);
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

function main() {
  const options = parseArgs(process.argv.slice(2));

  if (options.help) {
    // Moved printHelp out to avoid circular deps with utils or just print directly here
    process.stdout.write(`Realm installer

Usage:
  node bin/install.mjs [options]

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
  node bin/install.mjs
  node bin/install.mjs --dry-run
  node bin/install.mjs --agent gemini
  node bin/install.mjs --agent gemini --local
  node bin/install.mjs --agent gemini --local /path/to/project
  node bin/install.mjs --agent codex --local
  node bin/install.mjs --agent cursor --local
  node bin/install.mjs --agent claude --local
`);
    return;
  }

  const repoRoot = detectRepoRoot();
  if (!repoRoot) {
    fail('Unable to locate the Realm repo root from bin/install.mjs.');
  }

  if (options.agent === 'gemini') {
    installForGemini(options, repoRoot);
    return;
  }

  if (options.agent === 'codex') {
    installForCodex(options, repoRoot);
    return;
  }

  if (options.agent === 'cursor') {
    installForCursor(options, repoRoot);
    return;
  }

  if (options.agent === 'claude') {
    installForClaude(options, repoRoot);
    return;
  }
}

try {
  main();
} catch (err) {
  console.error(err);
  process.exit(1);
}
