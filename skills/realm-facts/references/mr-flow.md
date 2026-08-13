# MR + Teams flow

Read by: `submit`, `review`.

## Branch and MR

Branch name: `fact/<id>`. Title: `[fact] <title> (<id>)`. Target: `main`.
Labels: `realm-facts`, `needs-review`. (Matches `mcp/gitlab/README.md`'s MR Conventions.)

## Ladder (first that's reachable wins)

### 1. GitLab MCP available

Use the tools documented at `mcp/gitlab/README.md`:

| Step | Tool |
|---|---|
| Open MR | `create_merge_request` |
| Check status | `get_merge_request` |
| Post review comment | `create_merge_request_note` |
| Approve | `approve_merge_request` |
| Merge | `merge_merge_request` |

MR body: rendered from the fact's `## Compressed` line, its `owners`/`reviewers`, and a link to
the fact file. Never call `merge_merge_request` without an `approve_merge_request` having
succeeded first.

### 2. GitLab MCP unavailable — manual fallback

Print the exact command and the MR title/body for the user to run, then wait for a reply:

```bash
cd <facts-repo-local-path>
git checkout -b fact/<id>
git add facts/<domain>/<id>/
git commit -m "fact: <title>"
git push -u origin fact/<id>
```

```
Open an MR: fact/<id> -> main
Title: [fact] <title> (<id>)
Body:
  <compressed line>
  Owners: <owners>  Reviewers: <reviewers>
  facts/<domain>/<id>/index.md

Paste the MR URL when ready:
```

Wait for reply. Store the pasted URL — nowhere else records it, so it's needed for `review`.

### 3. Never push straight to `main`

Neither path ever pushes or merges without an MR + explicit approval step. This is operating
rule 2 in the top-level `SKILL.md` — do not special-case it away for convenience.

## Teams notification

Check `REALM_TEAMS_WEBHOOK` is set and the `mcp/teams/teams-webhook-server.js` `post_message`
tool is reachable. If either is missing:

```
Teams notification skipped — set REALM_TEAMS_WEBHOOK
```

Continue anyway — a missing webhook is never a hard failure for `submit`/`review`.

| Event | `title` | `themeColor` |
|---|---|---|
| review-request (`submit`) | `New fact review: <title>` | `0076D7` (default) |
| approved (`review --approve`) | `Fact approved — team pull latest` | `0076D7` |
| changes-requested (`review --request-changes`) | `Changes requested: <title>` | `0076D7` |

`post_message` payload includes `text` (author, reviewers, MR link, compressed summary) and a
`facts[]` array with the one fact id involved.
