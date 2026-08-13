# FACT_BUNDLE format

Read by: `ingest`. Produced by `facts.py bundle`.

## `--bundle impl` (default)

Minimal — for handing a fact to a coding agent that just needs the intent and its dependency
compresses.

```
FACT_BUNDLE:
  id: jwt-token-rotation
  compressed: JWT 15min expiry. Refresh via silent iframe.
  deps: [session-refresh-policy]
  repo_refs: [src/auth/token.ts]
  drift_policy: live code wins; facts = intent
```

`deps` is the fact's `depends_on` list. Pass `--deps` to expand each dependency's own
`compressed` line as a nested bullet instead of leaving it as a bare id list.
`repo_refs` is every `evidence` entry that does not start with `http` (i.e. a repo-relative
path, not a Confluence/external link).

## `--bundle context`

Adds `title`, `domain`, `tags`, `owners` above `deps` — for a reviewer or planning agent that
needs to know whose fact this is and where it sits, not just the compressed line.

## `--bundle full`

Everything `context` has, plus deps always expanded and the fact's full body (`## Context`,
`## Evidence`) appended as a literal block under `body: |`.

## `drift_policy`

Always the literal line `drift_policy: live code wins; facts = intent` — the fixed operating
rule from `docs/realm-facts-workflow.md`. Facts explain intent; when a fact and the live code
disagree on behavior, the code is authoritative and the disagreement should be flagged as
`FACT DRIFT` back to the fact's owner, not silently trusted.

## Paste target

The bundle is meant to be pasted directly into another agent's prompt or used as session
context — keep it exactly this shape, no extra prose wrapper.
