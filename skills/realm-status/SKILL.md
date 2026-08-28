---
name: realm-status
description: >
  Read-only status check for Realm. Reads .realm/realm-state.json and prints the vault path, project slug, and live vault node counts by type. No writes. Use to quickly assess what the vault knows vs what's pending.
---

# realm-status

Host invocation: Claude Code and Gemini use `/realm-status`; Codex uses `$realm-status`.

Inspect Realm state without writing.

## When to Use

| Trigger | Example |
|---|---|
| Check vault vs staged | "realm status", `/realm-status` |
| Verify init completed | After `/realm-forge` |
| Verify vault health | "what does realm know" |
| Orient at session start | "what does realm know?" |

## When NOT to Use

- Want to investigate code + vault → `/realm-fathom`
- Want to plan architectural changes → `/realm-planning`
- `realm-state.json` missing → will report; run `/realm-forge`

---

## Procedure

Handle all steps inline using Read and Bash. No agent spawn.

### Step 1 — Read state

Read `<projectRoot>/.realm/realm-state.json`.
If missing:
```
No realm state found.
Run /realm-forge to bootstrap.
```
STOP.

Extract: `vaultPath`, `projectSlug`, `projectDir`.

### Step 1.5 — Check orchestration lock

```bash
python3 "<realmOrchestrateSkillDir>/scripts/orchestrate.py" state --project-root .
```

(Resolve `realmOrchestrateSkillDir` the same way `realm-orchestrate/SKILL.md` does —
sibling skill directory, not a relative path.) If `ORCH_ACTIVE=true`, remember
`RUN_ID` and `WAVE` for the print in Step 3. If the orchestrate skill isn't
installed or the call errors, skip this step silently — orchestration status is
supplementary, not required for `/realm-status` to work.

### Step 2 — Count nodes by type

Read the live vault tree with one bounded command:
```bash
find <projectDir> -name "*.md" -not -path "*/_templates/*" | sort
```

Group results by leading path segment (`decisions/foo.md` → `decisions/`). Strip `.md`
suffix for `[[id]]` display. Use file mtime for date display.

Tag frequency (run once):
```bash
grep -rh "^  - " <projectDir> --include="*.md" 2>/dev/null | sort | uniq -c | sort -rn | head 20
```

### Step 3 — Print status (caveman-compressed)

```
realm:<projectSlug>
vault:<vaultPath>  proj:<projectDir>

⚡ ORCHESTRATION ACTIVE <RUN_ID> — wave <WAVE>   (only when ORCH_ACTIVE=true from Step 1.5)

NODES <total>
decisions/<N>:   [[id]] <date>  [[id2]] <date>
discoveries/<N>: [[id]] <date>
sessions/<N>:    <filename>

TAGS #<tag>:<N>  #<tag>:<N>  #<tag>:<N>  (top 10)

→ vault current. Run /realm-fathom to investigate code or /realm-planning to design.
```
