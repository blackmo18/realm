---
name: realm-facts:forge
description: >
  Connect this repo to a central facts repo. Interactively resolves the facts-repo URL and
  local clone path, then delegates all mechanical work — layout bootstrap, factsRepo pointer
  write, initial index — to scripts/facts.py. The only interactive fact subskill besides `new`.
---

# realm-facts — forge

Triggered by: `/realm-facts forge`, "connect facts", first `/realm-facts` invocation with no `factsRepo` in `realm-state.json`.

## Step 1 — Check existing connection

```bash
python3 .claude/skills/realm-facts/scripts/facts.py state --project-root .
```

If `FACTS_CONNECTED=true`: print the existing `FACTS_URL`/`FACTS_LOCAL_PATH` and ask
"Already connected. Reconnect anyway?" — **wait for reply**. `no`/empty → STOP. `yes` → continue.

## Step 2 — Resolve facts-repo URL and local clone path (interactive)

1. Check args. If a URL was provided (`/realm-facts forge --facts-url ...`), use it.
2. No arg: ask the user for the central facts repo, e.g.
   `git@gitlab.example.com:org/realm-facts.git`. **Wait for reply before proceeding.**
3. Ask for (or accept a provided) local clone path. If not given, default to
   `../realm-facts` relative to the project root and confirm with the user.
4. Print `Facts repo: <url>  Local: <local-path>` and proceed.

## Step 3 — Ensure local clone exists

If `<local-path>` is not a git repo (no `.git`): run `git clone <url> <local-path>`.
If it exists already: run `git -C <local-path> fetch` to confirm reachability — do not pull or
merge here, that's `sync`'s job.

## Step 4 — Bootstrap layout (idempotent)

```bash
python3 .claude/skills/realm-facts/scripts/facts.py init --facts-root <local-path>
```

Safe to re-run against an existing facts repo — never overwrites a fact file, only ensures
`facts/`, `decisions/`, `references/`, `.realm/` exist and regenerates the index.

## Step 5 — Write the factsRepo pointer

```bash
python3 .claude/skills/realm-facts/scripts/facts.py connect \
  --project-root . --facts-url <url> --local-path <local-path> --branch main
```

## Step 6 — Print summary

```
realm-facts:forge complete

  facts repo: <url>
  local:      <local-path>
  facts:      <N> across <D> domains

→ /realm-facts new <domain> <id> | /realm-facts recall <query>
```
