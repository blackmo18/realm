import fs from 'fs';
import path from 'path';
import childProcess from 'child_process';
import {
  ensureDir,
  info,
  warn,
  fail,
  success,
  defaultCursorAgentsDir,
  hasCommand,
  agentLabel,
  skillCommand,
  copyAgentFiles,
  copySkillsDir,
} from './utils.mjs';

export function installForCursor(options, repoRoot) {
  if (options.isLocal) {
    installLocalForCursor(options, repoRoot);
    return;
  }

  const command = ['npx', 'skills', 'add', options.repo, '-a', options.agent];
  if (options.force) {
    warn('--force is only used by the Claude Code local plugin installer; ignoring it for Skills CLI install.');
  }

  info(`Realm install target: ${options.repo}`);
  info(`Agent: ${options.agent}`);
  info(`Command: ${command.join(' ')}`);
  info(`Cursor agents dir: ${defaultCursorAgentsDir()}`);

  if (options.dryRun) {
    process.stdout.write('Planned Cursor native agent install:\n');
    process.stdout.write(`- Copy .cursor/agents/*.md into ${defaultCursorAgentsDir()}\n`);
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

  installCursorAgents(repoRoot);

  process.stdout.write('\n');
  success(`Realm is installed globally for ${agentLabel(options.agent)}.`);
  process.stdout.write(
    'Next steps:\n' +
    `1. Restart ${agentLabel(options.agent)} or open a new session so the new skills are loaded cleanly.\n` +
    `2. In your project, run ${skillCommand(options.agent, 'realm-forge')} to bootstrap the local Realm state.\n` +
    `3. Query with ${skillCommand(options.agent, 'realm-recall')} or investigate with ${skillCommand(options.agent, 'realm-fathom')}.\n`
  );
}

function installLocalForCursor(options, repoRoot) {
  const targetDir = path.resolve(options.targetDir || process.cwd());
  const skillsSrc = path.join(repoRoot, 'skills');
  
  info(`Realm local install target: ${targetDir}`);
  info(`Agent: cursor`);

  const targetSkillsDir = path.join(targetDir, '.agents', 'skills');
  const agentsSrc = path.join(repoRoot, '.cursor', 'agents');
  const targetAgentsDir = path.join(targetDir, '.cursor', 'agents');
  
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
  success(`Realm is installed locally for Cursor in ${targetDir}.`);
  process.stdout.write(
    'Next steps:\n' +
    `1. Open ${targetDir} in Cursor.\n` +
    `2. Run /realm-forge to bootstrap local Realm vault state for this project.\n` +
    `3. Query with /realm-recall or investigate with /realm-fathom.\n`
  );
}

export function installCursorAgents(repoRoot) {
  const sourceDir = path.join(repoRoot, '.cursor', 'agents');
  const destinationDir = defaultCursorAgentsDir();

  if (!fs.existsSync(sourceDir)) {
    warn(`Cursor native agents not found at ${sourceDir}`);
    warn('Realm skills were installed, but Cursor subagent definitions were not copied.');
    return;
  }

  ensureDir(destinationDir);
  copyAgentFiles(sourceDir, destinationDir);
  for (const entry of fs.readdirSync(sourceDir, { withFileTypes: true })) {
    if (entry.isFile() && path.extname(entry.name) === '.md') {
      info(`Installed Cursor agent: ${path.join(destinationDir, entry.name)}`);
    }
  }
}
