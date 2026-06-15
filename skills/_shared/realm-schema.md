# realm-state.json Schema

Location: `<project-root>/.realm/realm-state.json`

```json
{
  "vaultPath": "<absolute path to Obsidian vault root>",
  "projectSlug": "<kebab-case slug>",
  "projectDir": "<vaultPath>/projects/<projectSlug>",
  "manifest": {
    "lastRun": "<ISO 8601 or null>"
  },
  "pendingDrafts": [
    {
      "source": "plan | convey",
      "slug": "<category>/<slug> | null",
      "path": "<path to manifest-draft.md relative to projectRoot>",
      "created": "<ISO 8601>"
    }
  ],
  "nodeIndex": {
    "counts": { "<subdir>": "<N>" },
    "ids": { "<node-id>": "<subdir/filename.md>" },
    "updatedAt": "<ISO 8601>"
  },
  "docs": {
    "<relative-to-projectDir path>": {
      "status": "committed | planned | stale",
      "updated": "<ISO 8601 or null>"
    }
  }
}
```

**pendingDrafts entries:**
- `source: plan` — from `realm-plan finalize`. `slug` = `work/<category>/<slug>`. `path` = `work/<category>/<slug>/manifest-draft.md`.
- `source: convey` — from `realm-convey`. `slug` = null. `path` = `.realm/manifest-draft.md`.
- Managed exclusively by `manifest_write.py --push-draft` / `--remove-draft`. Never edit JSON directly.

**nodeIndex:** built by `manifest_write.py` on every vault commit. Use for status/recall counts and id→path resolution without live `find` scans.

**docs status:**
- `committed` — written by realm-manifest or detected as pre-existing on init.
- `planned` — staged in a pending draft; not yet in vault.
- `stale` — committed but codebase has diverged.

## Staging Dir Layout

```
<project-root>/.realm/
├── realm-state.json
├── manifest-draft.md        # written by realm-convey only
└── archive/
    └── <slug>-<timestamp>-draft.md

<vault>/projects/<slug>/work/<category>/<slug>/
├── _meta.md
├── <section>.md
└── manifest-draft.md        # written by realm-plan finalize
```

`.realm/` must be in `.gitignore`. realm-forge ensures this.

## Ordering Guards

realm-manifest checks at startup:
- No `realm-state.json` → `No realm state. Run /realm-forge first.`
- `pendingDrafts` empty → `No pending drafts. Run /realm-plan finalize or /realm-convey.`
- Draft file missing → `Draft file missing: <path>. Stage again.`

realm-plan checks at startup: no `realm-state.json` → STOP.
