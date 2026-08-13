---
name: realm-concise:lifecycle
description: >
  Gated status transitions for realm-concise candidates — approve, plan,
  done, ignore. Every transition requires the user to explicitly name the
  file and the action in the same turn; nothing here infers approval from
  enthusiasm or from a prior recommend/plan completing.
---

# realm-concise — lifecycle

Triggered by: `/realm-concise approve <file>`, `/realm-concise plan <file>`, `/realm-concise done <file> [--adr X]`, `/realm-concise ignore <file> --reason "..."`.

## Gate keeping (hard rule, applies to every command below)

`approve`, `plan`, and `done` all require the user to have just said, in this turn, something that names the file and clearly means "do this one" — not agreement with a `recommend` verdict in the abstract, not "looks good"/"sounds right"/"sure". If that's missing, ask them to say the command explicitly rather than proceeding.

## `approve <file>`

```bash
python3 ../scripts/concise.py set-status --root <projectDir> <file> --status approved
```

## `plan <file>`

**Gate:** `python3 ../scripts/concise.py show --root <projectDir> <file>`. If `status` is not `approved`, refuse:

```
plan: <file> is status:<current>, not approved.
run /realm-concise approve <file> first, or /realm-concise recommend <file> if not yet reviewed.
```

If approved:

1. `set-status --root <projectDir> <file> --status in-progress`
2. Hand off to `/realm-planning` with the file path and the `recommend` seam list (if produced this session) as topic context — Phase 1 direction, user approves, Phase 2 code-level plan.
3. **Stop.** Print where the plan landed (`planning/<NNN>-plan-<slug>.md` / `execution/<NNN>-exct-<slug>.md`) and wait. Implementation is not an automatic continuation of Phase 2 returning — it's the user's next explicit ask.

## `done <file> [--adr X]`

Only on explicit user confirmation the refactor landed — never inferred from a plan completing:

```bash
python3 ../scripts/concise.py complete --root <projectDir> <file> [--new-files a,b] [--adr ADR-0NN-slug]
```

Then offer — don't auto-run — `write adr` via `/realm-planning` so the rationale lands in the vault. If taken and an ADR gets written but wasn't passed to `complete` already, feed the id back:

```bash
python3 ../scripts/concise.py set-status --root <projectDir> <file> --status refactored --adr ADR-0NN-slug
```

## `ignore <file> --reason "..."`

```bash
python3 ../scripts/concise.py set-status --root <projectDir> <file> --status ignored --reason "<reason>"
```

Script refuses without `--reason` — don't strip it even if the user's reason is short.
