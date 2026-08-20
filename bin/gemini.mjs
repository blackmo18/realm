import fs from 'fs';
import path from 'path';
import os from 'os';
import {
  ensureDir,
  info,
  warn,
  success,
  defaultGeminiAgentsDir,
  copySkillsDir,
  removeLegacyAgentFiles,
  LEGACY_SHARED_AGENT_FILES,
} from './utils.mjs';

export function installForGemini(options, repoRoot) {
  const isLocal = options.isLocal;
  const targetDir = path.resolve(options.targetDir || process.cwd());
  
  const targetPluginDir = isLocal 
    ? path.join(targetDir, '.agents', 'plugins', 'realm')
    : path.join(os.homedir(), '.gemini', 'config', 'plugins', 'realm');
    
  const targetAgentsDir = isLocal
    ? path.join(targetDir, '.gemini', 'agents')
    : defaultGeminiAgentsDir();
    
  const skillsSrc = path.join(repoRoot, 'skills');
  const pluginJsonSrc = path.join(repoRoot, '.gemini-plugin', 'plugin.json');

  info(`Realm install source: ${repoRoot}`);
  info('Agent: gemini');
  info(`Gemini plugin dir: ${targetPluginDir}`);
  info(`Gemini agents dir: ${targetAgentsDir}`);

  if (options.dryRun) {
    process.stdout.write(`Planned Gemini ${isLocal ? 'local' : 'global'} install:\n`);
    process.stdout.write(`- Create plugin bundle at ${targetPluginDir}\n`);
    process.stdout.write(`- Copy .gemini-plugin/plugin.json -> ${targetPluginDir}/plugin.json\n`);
    process.stdout.write(`- Copy skills/* -> ${targetPluginDir}/skills/\n`);
    process.stdout.write(`- Copy agents/*.md -> ${targetAgentsDir}/\n`);
    success('Dry run complete.');
    return;
  }

  // 1. Build the Gemini Plugin Bundle
  ensureDir(targetPluginDir);
  if (fs.existsSync(pluginJsonSrc)) {
    fs.copyFileSync(pluginJsonSrc, path.join(targetPluginDir, 'plugin.json'));
  } else {
    warn(`Could not find ${pluginJsonSrc}. The plugin bundle may be missing its manifest.`);
  }

  const targetSkillsDir = path.join(targetPluginDir, 'skills');
  ensureDir(targetSkillsDir);
  copySkillsDir(skillsSrc, targetSkillsDir);
  info(`Installed Gemini Plugin bundle to ${targetPluginDir}`);

  // 2. Install Native Gemini Agents
  installGeminiAgents(repoRoot, targetAgentsDir);

  process.stdout.write('\n');
  success(`Realm is installed ${isLocal ? `locally in ${targetDir}` : 'globally'} as a Gemini Plugin.`);
  process.stdout.write(
    'Next steps:\n' +
    '1. Open a new Gemini session or reload your workspace.\n' +
    '2. Run /realm-forge to bootstrap the local Realm state.\n' +
    '3. Query with /realm-recall or investigate with /realm-fathom.\n'
  );
}

export function installGeminiAgents(repoRoot, destinationDir) {
  const sourceDir = path.join(repoRoot, 'agents');

  if (!fs.existsSync(sourceDir)) {
    warn(`Gemini native agents not found at ${sourceDir}`);
    warn('Realm plugin was installed, but Gemini subagent definitions were not copied.');
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
