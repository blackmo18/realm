import fs from 'fs';
import path from 'path';
import os from 'os';
import {
  ensureDir,
  info,
  warn,
  success,
  defaultCodexAgentsDir,
  defaultCodexSkillsDir,
  copySkillsDir,
  removeLegacyAgentFiles,
  LEGACY_CODEX_AGENT_FILES,
} from './utils.mjs';

const CODEX_MODEL_BY_SHARED_MODEL = {
  opus: 'gpt-5.6-sol',
  sonnet: 'gpt-5.6-terra',
  haiku: 'gpt-5.6-luna',
};

export function installForCodex(options, repoRoot) {
  if (options.isLocal) {
    installLocalForCodex(options, repoRoot);
    return;
  }

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
  installCodexAgents(repoRoot, agentsDir);

  process.stdout.write('\n');
  success('Realm is installed globally for Codex.');
  process.stdout.write(
    'Next steps:\n' +
    '1. Restart Codex or open a new session so the new skills are loaded cleanly.\n' +
    '2. In your project, run $realm-forge to bootstrap the local Realm state.\n' +
    '3. Query with $realm-recall or investigate with $realm-fathom.\n'
  );
}

function installLocalForCodex(options, repoRoot) {
  const targetDir = path.resolve(options.targetDir || process.cwd());
  const skillsSrc = path.join(repoRoot, 'skills');
  
  info(`Realm local install target: ${targetDir}`);
  info(`Agent: codex`);

  const targetSkillsDir = path.join(targetDir, '.agents', 'skills');
  const agentsSrc = path.join(repoRoot, '.codex', 'agents');
  const targetAgentsDir = path.join(targetDir, '.codex', 'agents');
  
  const legacySkillsDir = path.join(targetDir, '.codex', 'skills');
  if (fs.existsSync(legacySkillsDir)) {
    warn(`Legacy Codex skill directory detected: ${legacySkillsDir}`);
    warn('Realm now uses .agents/skills for project-scoped Codex skills; remove old Realm copies after verifying this install.');
  }

  if (options.dryRun) {
    process.stdout.write('Planned Local Actions:\n');
    process.stdout.write(`- Copy skills (${skillsSrc}) -> ${targetSkillsDir}\n`);
    if (fs.existsSync(agentsSrc)) {
      process.stdout.write(`- Copy agent definitions (${agentsSrc}/*.toml) -> ${targetAgentsDir}\n`);
    }
    success('Dry run complete.');
    return;
  }

  ensureDir(targetSkillsDir);
  copySkillsDir(skillsSrc, targetSkillsDir);
  info(`Installed skills to ${targetSkillsDir}`);

  if (fs.existsSync(agentsSrc)) {
    installCodexAgents(repoRoot, targetAgentsDir, 'Installed agent');
  }

  process.stdout.write('\n');
  success(`Realm is installed locally for Codex in ${targetDir}.`);
  process.stdout.write(
    'Next steps:\n' +
    `1. Open ${targetDir} in Codex.\n` +
    `2. Run $realm-forge to bootstrap local Realm vault state for this project.\n` +
    `3. Query with $realm-recall or investigate with $realm-fathom.\n`
  );
}

export function installCodexAgents(
  repoRoot,
  agentsDir = defaultCodexAgentsDir(),
  label = 'Installed Codex agent'
) {
  const sourceDir = path.join(repoRoot, '.codex', 'agents');
  const destinationDir = agentsDir;

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

    writeCodexAgent(
      path.join(sourceDir, entry.name),
      path.join(repoRoot, 'agents', `${path.basename(entry.name, '.toml')}.md`),
      path.join(destinationDir, entry.name)
    );
    info(`${label}: ${path.join(destinationDir, entry.name)}`);
  }

  removeLegacyAgentFiles(destinationDir, LEGACY_CODEX_AGENT_FILES);
}

function writeCodexAgent(templatePath, sharedAgentPath, destinationPath) {
  const sharedAgent = fs.readFileSync(sharedAgentPath, 'utf8');
  const sourceModel = sharedAgent.match(/^model:\s*(opus|sonnet|haiku)\s*$/m)?.[1];
  const codexModel = CODEX_MODEL_BY_SHARED_MODEL[sourceModel];

  if (!codexModel) {
    throw new Error(
      `Cannot map the model for ${path.basename(sharedAgentPath)} to a Codex equivalent.`
    );
  }

  const template = fs.readFileSync(templatePath, 'utf8');
  if (!/^model = "[^"]+"$/m.test(template)) {
    throw new Error(`Missing Codex model field in ${path.basename(templatePath)}.`);
  }
  const adapted = template.replace(
    /^model = "[^"]+"$/m,
    `model = "${codexModel}"`
  );

  fs.writeFileSync(destinationPath, adapted);
}
