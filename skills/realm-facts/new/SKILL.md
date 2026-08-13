---
name: realm-facts:new
description: >
  Interactively author a new fact. Interviews the user for the compressed summary, evidence,
  owners, reviewers, and tags, then hands the write, validation, and reindex to scripts/facts.py.
  Never writes the fact file by hand — the interview only fills in CLI flags.
---

# realm-facts — new

Triggered by: `/realm-facts new <domain> <id>`, "create a fact", "document X".

## Step 0 — Guard

```bash
python3 .claude/skills/realm-facts/scripts/facts.py state --project-root .
```

`FACTS_CONNECTED=false` → `No facts repo connected. Run /realm-facts forge first.` STOP.

## Step 1 — Resolve domain and id

From args: `/realm-facts new <domain> <id>`. If either is missing, ask for it — domain and id
must both be kebab-case (`jwt-token-rotation`, not `JWT_Token_Rotation`).

## Step 2 — Interview (interactive, wait for each reply)

Load `../references/fact-schema.md` for the field contract before asking.

1. **Title** — human-readable, e.g. "JWT Token Rotation".
2. **Compressed summary** — 1-2 sentences, ≤400 chars, must stand alone for another agent with
   zero other context. If the user's first draft is vague ("uses JWT"), push back once for
   something concrete ("JWT 15min expiry. Refresh via silent iframe.").
3. **Evidence** — Confluence links, repo paths, ADR refs. Accept zero or more; zero is allowed
   at `draft` but will block `submit` later (`--mr-ready` requires non-empty evidence).
4. **Owners** — at least one `@handle`, required.
5. **Reviewers** — one or more `@handle`; may be empty for now, required before `submit`.
6. **Tags** — comma-separated, optional.

## Step 3 — Write, validate, index (mechanical)

```bash
python3 .claude/skills/realm-facts/scripts/facts.py new \
  --facts-root <local-path> --domain <domain> --id <id> \
  --title "<title>" --summary "<compressed>" \
  --owners "<owner1,owner2>" --reviewers "<reviewer1,reviewer2>" --tags "<tag1,tag2>" \
  --evidence "<url1>" --evidence "<url2>"
```

`new` already validates the summary length and rejects a duplicate id at write time — no
separate `validate` call needed here, but run it anyway if the interview allowed evidence/owners
edge cases you're unsure about:

```bash
python3 .claude/skills/realm-facts/scripts/facts.py validate --facts-root <local-path> --fact <id>
```

Non-zero exit → surface the `<path>:<field>: <problem>` lines verbatim and ask the user to fix
that one field; do not retry blindly.

## Step 4 — Print summary

```
realm-facts:new complete

  facts/<domain>/<id>/index.md  (status: draft)
  <compressed line>

→ /realm-facts link <id> --related <other-id> | /realm-facts submit <id>
```
