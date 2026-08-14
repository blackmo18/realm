# Canvas Lazy-Load (source_plan)

> Loaded only from realm-recall Step 4.5, only when a loaded ADR node has a `source_plan`
> frontmatter field and canvas expansion isn't suppressed.

When an ADR was promoted from a `realm-plan` canvas, its `source_plan` field points to the
canvas dir. realm-recall intent-maps the query to exactly one canvas section and reads only
that file. Cost: ADR compressed (~20t) + one section (~80–150t).

| Query words | Section loaded | Extra tokens |
|---|---|---|
| plan / steps / tasks / phases / build / implement | `plan.md` | ~100t |
| design / architecture / how / approach / structure | `design.md` | ~100t |
| research / why / evidence / tradeoffs / source / learned | `research.md` | ~120t |
| scaffold / blueprint / interface / methods / class / file | `scaffold.md` | ~100t |
| summary / what is / overview / which / what | `_meta.md` section headers only | ~15t |
| rejected / alternatives / why decided / constraint / chose | ADR body (already loaded) | 0t |

```bash
/realm-recall "what is the plan for auth refactor"
→ ADR-auth-refactor (compressed) + work/plans/auth-refactor/plan.md

/realm-recall "what design did we choose for auth"
→ ADR-auth-refactor (compressed) + work/plans/auth-refactor/design.md

/realm-recall "which research drove the auth decision"
→ ADR-auth-refactor (compressed) + work/plans/auth-refactor/research.md

/realm-recall "why did we reject X for auth"
→ ADR-auth-refactor body only — rejected_alternatives already there, 0 extra read

/realm-recall "summarize the auth refactor work"
→ ADR-auth-refactor (compressed) + _meta.md headers only

/realm-recall "auth" --no-canvas
→ ADR only, no canvas expansion (suppress source_plan follow)
```

No canvas follow when: ADR has no `source_plan`,
`--no-canvas` flag passed, `--trace` flag passed, or intent maps to ADR body (rejected/constraints).

## Step 4.5 — Canvas expansion procedure

Skip entirely if: `--trace` flag, `--no-canvas` flag, or no ADR nodes loaded.

For each ADR node loaded that has a `source_plan` field in frontmatter:

**4.5a — Classify query intent:**

Tokenize query (lowercase, split on spaces). Match first winning rule:

| Rule | Trigger words | Target file |
|---|---|---|
| `plan` | plan, steps, tasks, phases, build, implement, roadmap, milestones | `plan.md` |
| `design` | design, architecture, how, approach, structure, pattern, system | `design.md` |
| `research` | research, why, evidence, tradeoffs, tradeoff, source, learned, studied, found | `research.md` |
| `scaffold` | scaffold, blueprint, interface, methods, class, file, module, boundary | `scaffold.md` |
| `meta` | summary, summarize, overview, which, what, list | `_meta.md` |
| `adr-only` | rejected, alternatives, chose, chose, constraint, consequence, decided | — (no read) |

If no rule matches: default to `meta` (read `_meta.md` headers only).

**4.5b — Resolve canvas path:**

```
canvas_dir = <projectDir>/<source_plan>
section_path = <canvas_dir>/<target_file>
```

If `section_path` does not exist: skip canvas expansion for this node, note in output:
`canvas section not found: <section_path>`

**4.5c — Read section:**

For `_meta.md` target: read headers only (lines starting with `#` or `|`). ~15 tokens.
For all other targets: read full file content. ~80–150 tokens.

Attach section content to the node's output under `## Canvas: <section>`.

**4.5d — Token note:**

Append to Step 6 footer:
`canvas: +<N>t (<section> from <source_plan>)`
