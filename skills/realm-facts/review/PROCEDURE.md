---
name: realm-facts-review
description: >
  Reviewer workflow for a fact MR — the one place this skill does real LLM judgment (is the
  Compressed summary agent-useful, is evidence sufficient). Everything else — mr-ready
  revalidation, MR approve/comment, status transition, reindex, Teams notify — is scripted.
---

# realm-facts — review

Triggered by: `/realm-facts review <id>`, `/realm-facts review <id> --approve`, `/realm-facts review <id> --request-changes "<reason>"`.

## Step 0 — Guard

```bash
python3 "<realmFactsSkillDir>/scripts/facts.py" state --project-root .
```

`FACTS_CONNECTED=false` → `No facts repo connected. Run /realm-facts forge first.` STOP.

## Step 1 — Load the fact and re-check mr-ready

```bash
python3 "<realmFactsSkillDir>/scripts/facts.py" validate --facts-root <local-path> --fact <id> --mr-ready
```

Non-zero exit → this shouldn't happen post-`submit`, but if it does, surface the errors and stop
short of approving — request changes instead (Step 2b).

## Step 2 — Reviewer checklist (the judgment step)

Read the fact file. Judge:

- [ ] Schema valid (Step 1 already confirmed this mechanically)
- [ ] `## Compressed` is agent-useful — specific enough that a coding agent with zero other
      context could act on it. Vague summaries ("uses JWT") fail this even if they pass length
      validation.
- [ ] Evidence links are present and plausible (a Confluence URL, not a placeholder)
- [ ] No duplicate id (Step 1 already confirmed this mechanically)
- [ ] `related`/`depends_on`/`supersedes` links make sense given the fact's content

**No `--approve`/`--request-changes` flag given:** print the checklist findings and ask the user
which way to go. **Wait for reply.**

### 2a — Approve

```bash
python3 "<realmFactsSkillDir>/scripts/facts.py" set-status --facts-root <local-path> --fact <id> --status active
python3 "<realmFactsSkillDir>/scripts/facts.py" index --facts-root <local-path>
```

Then follow `../references/mr-flow.md` to `approve_merge_request` + `merge_merge_request` (or
the manual fallback), and post the `approved` Teams notification.

### 2b — Request changes

Do not change the fact's status (stays `review`). Follow `../references/mr-flow.md` to post an
MR comment (`create_merge_request_note` or manual) with the specific reason, and post the
`changes-requested` Teams notification naming the author.

## Step 3 — Print summary

```
realm-facts:review complete

  <id>  status: <active | review (changes requested)>
  <MR merged | MR comment posted>
  Teams: <notified | skipped>

→ /realm-facts sync  (team members pull latest)
```
