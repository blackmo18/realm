import fs from 'fs';
import path from 'path';
import {
  ensureDir,
  info,
  warn,
  fail,
  success,
  defaultClaudeBaseDir,
  defaultClaudeMarketplaceDir,
  copyRealmRepo,
  copyAgentFiles,
  copySkillsDir,
} from './utils.mjs';

export function installForClaude(options, repoRoot) {
  if (options.isLocal) {
    installLocalForClaude(options, repoRoot);
    return;
  }

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

function installLocalForClaude(options, repoRoot) {
  const targetDir = path.resolve(options.targetDir || process.cwd());
  const skillsSrc = path.join(repoRoot, 'skills');
  
  info(`Realm local install target: ${targetDir}`);
  info(`Agent: claude`);

  const targetSkillsDir = path.join(targetDir, '.claude', 'skills');
  const agentsSrc = path.join(repoRoot, 'agents');
  const targetAgentsDir = path.join(targetDir, '.claude', 'agents');
  
  if (options.dryRun) {
    process.stdout.write('Planned Local Actions:\n');
    process.stdout.write(`- Copy skills (${skillsSrc}) -> ${targetSkillsDir}\n`);
    if (fs.existsSync(agentsSrc)) {
      process.stdout.write(`- Copy agent definitions (${agentsSrc}/*.md) -> ${targetAgentsDir}\n`);
    }
    success('Dry run complete.');
    return;
  }

  ensureDir(targetSkillsDir);
  copySkillsDir(skillsSrc, targetSkillsDir);
  info(`Installed skills to ${targetSkillsDir}`);

  if (fs.existsSync(agentsSrc)) {
    ensureDir(targetAgentsDir);
    copyAgentFiles(agentsSrc, targetAgentsDir);
    for (const entry of fs.readdirSync(agentsSrc, { withFileTypes: true })) {
      if (entry.isFile() && path.extname(entry.name) === '.md') {
        info(`Installed agent: ${path.join(targetAgentsDir, entry.name)}`);
      }
    }
  }

  process.stdout.write('\n');
  success(`Realm is installed locally for Claude Code in ${targetDir}.`);
  process.stdout.write(
    'Next steps:\n' +
    `1. Open ${targetDir} in Claude Code.\n` +
    `2. Run /realm-forge to bootstrap local Realm vault state for this project.\n` +
    `3. Query with /realm-recall or investigate with /realm-fathom.\n`
  );
}
