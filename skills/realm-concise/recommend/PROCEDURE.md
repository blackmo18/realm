---
name: realm-concise-recommend
description: >
  The one semantic step in realm-concise. Reads a single candidate file,
  checks graphify for callers/neighbors, checks reuse-existing-utils.md for
  duplicate logic, and proposes decomposition seams tagged effort + blast
  radius. Never writes code, never changes state, never implies approval.
---

# realm-concise — recommend

Triggered by: `/realm-concise recommend <file>`.

This is the only realm-concise flow that reads source. Every other flow is a script call plus formatting.

## Procedure

Follow `../references/recommend-rubric.md` exactly:

1. `python3 "<realmConciseSkillDir>/scripts/concise.py" show --root <projectDir> <file>` for metrics (loc, fanIn, hasTest, churn, score, tier).
2. `graphify explain "<file>"` for callers/neighbors — mandatory before any raw read per this workspace's graphify-first rule.
3. Read the file in full.
4. Check the repository's applicable host guidance (`AGENTS.md`, `CLAUDE.md`, or host rules) before proposing any new utility — never recreate an existing domain utility.
5. Emit the seam list (`extract-to-existing-util` / `extract-to-new-module` / `split-component` / `move-to-repository`) + verdict, in the rubric's output shape.

## Boundaries

- Never calls `set-status`. Never calls `/realm-planning`. Only proposes.
- `tier: deep` → say so plainly, name what would de-risk it (add a test, reduce fan-in) rather than producing a seam list that hides the risk.
- Seam list stays to what's visible in the file — no speculation about code not read.
- Ends with `-> /realm-concise approve <file>` as a suggestion, never an implicit approval.
