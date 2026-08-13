# Investigator Rules — all modes

`cavecrew-investigator` is a fallback, never a default spawn. Default path is `graphify explain` / `graphify affected` / `graphify path` (graph present) — see `anchor-resolution.md` for the per-anchor-kind table.

## Trigger Conditions (any one fires the spawn)

- a named anchor resolves to no graph node
- `Start:` seeds still drift after the one vocab retry (mode-detection drift guard)
- the question is about **behavior/logic**, not structure — graphify carries structure only, not runtime flow
- graph is stale (graph precondition check) AND the topic touches recently-changed files
- graph absent (legacy path) — investigator is the only path, use pre-graphify budgets

## Read Budgets (file Reads only — grep/glob unlimited)

| Mode | Budget when triggered |
|---|---|
| enhancement | 6 (or 15 if graph absent — legacy budget) |
| anchored-new | 8 (or 20 if graph absent) |
| greenfield | 4 (or 8 if graph absent) |

Read slices, not whole files.

## Escape Hatch

Budget hit + concrete evidence more relevant files exist → return named unread candidates + why each matters, ask to extend. Never silently stop or exceed.

## Output

Compressed `file:line` table.

## Spawn Prompt Must Include

1. The already-resolved graphify anchor table so the agent does not rediscover.
2. The graphify-first rule verbatim (`.claude/settings.json` PreToolUse hook mandates graphify before grep/read for every tool call, including subagents).
3. Static instructions first, per-run variables (mode, seeds, budget) on the last lines — preserves prompt cache across spawns.
