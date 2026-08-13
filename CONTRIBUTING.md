# Contributing to Realm

## Uploading & Publishing to Claude Plugins

To upload, publish, or update Realm on the Claude Code plugin marketplace:

### 1. Structure Requirements

Claude Code plugins require a `.claude-plugin/` metadata folder with two key JSON files:
- `.claude-plugin/plugin.json`: Defines the plugin name, version, description, and author.
- `.claude-plugin/marketplace.json`: Defines the plugin marketplace entry, repository URL, commit SHA, and category.

### 2. Update Manifest Files

Before publishing a release:

1. Bump the version in `.claude-plugin/plugin.json`:
   ```json
   {
     "name": "realm",
     "description": "Obsidian project-knowledge & decision memory pipeline...",
     "version": "0.1.6",
     "author": { ... }
   }
   ```

2. Get your latest git commit SHA and update `.claude-plugin/marketplace.json`:
   ```bash
   git rev-parse HEAD
   ```
   Update `plugins[0].source.sha` in `.claude-plugin/marketplace.json`:
   ```json
   {
     "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
     "name": "realm",
     "description": "Obsidian project-knowledge & decision memory pipeline...",
     "plugins": [
       {
         "name": "realm",
         "source": {
           "source": "url",
           "url": "https://github.com/blackmo18/realm.git",
           "sha": "<YOUR_COMMIT_SHA>"
         }
       }
     ]
   }
   ```

### 3. Push to GitHub

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore(release): update plugin manifest and commit SHA"
git push origin main
```

### 4. Register / Add Plugin in Claude Code

Users or team members can now install the plugin directly via GitHub URL or local marketplace path:

```bash
# From GitHub repository:
/plugin marketplace add blackmo18/realm

# Or from local clone:
/plugin marketplace add ~/.claude/plugins/marketplaces/realm
```
