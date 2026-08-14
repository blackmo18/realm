# Recommend rubric — the one semantic step

Loaded only for `/realm-concise recommend <file>`. Every other subcommand is a script call plus formatting — this is the sole place an LLM reads and judges source code.

## Inputs (gather in this order, cheapest first)

1. `concise.py show <file>` — loc, fanIn, hasTest, churn, score, tier. One small stdout.
2. `graphify explain "<file>"` — callers, neighbors, community. Mandatory before any raw read per this workspace's CLAUDE.md.
3. Read the target file in full.
4. Duplicate check — before proposing any new utility, inspect the repository's applicable host guidance (`AGENTS.md`, `CLAUDE.md`, or host rules) and search the domain's existing utility home:

   | Concern in the file | Check first |
   |---|---|
   | formatting money | `src/lib/currency.ts` |
   | slugs | `src/lib/slugify.ts` |
   | HTML sanitizing | `src/lib/sanitize-html.ts` |
   | logging / console.* | `src/lib/logger.ts` |
   | rate limiting | `src/lib/rate-limit.ts` |
   | auth/session/cookie | `src/lib/auth/` |
   | raw DB queries | `src/lib/db/` |
   | Hostinger HTTP calls | `src/lib/hostinger/fetch.ts` |
   | commerce/product logic | `src/lib/commerce/`, `src/lib/products.ts` |
   | metadata/SEO | `src/lib/metadata.ts`, `src/lib/structured-data.ts` |
   | email | `src/lib/email/` |
   | React state/behavior | `src/hooks/` |

   Anything matching a row is a **reuse**, not an extraction target. Never recommend recreating `formatCurrency`, `slugify`, sanitize-html, the logger, the rate limiter, or the Hostinger fetch wrapper.

## Seam types (pick one or more per file)

- **extract-to-existing-util** — a block duplicates logic that already lives in `src/lib/`. Cite the existing file path.
- **extract-to-new-module** — cohesive logic with no existing home; give it a `src/lib/<domain>/` or `src/hooks/use-<name>.ts` destination per `reuse-existing-utils.md`'s decision tree.
- **split-component** — a `.tsx` file mixing 2+ unrelated concerns (e.g. a form and a data table in one component); propose the split boundary by JSX region, not by line count.
- **move-to-repository** — raw queries or fetch calls embedded in a component/route instead of `src/lib/db/` or `src/lib/hostinger/fetch.ts`.

Tag each seam with `effort: low|medium|high` (roughly: lines touched, files created) and `blastRadius` = the file's `fanIn` from step 1 (shared across all seams in one file).

## Output shape

```
recommend:<file> score:<N> tier:<t>

seams:
1. [split-component] <region> -> <new file>          effort:low  blast:<fanIn>
2. [extract-to-existing-util] <block> -> <existing path>   effort:low  blast:<fanIn>
...

reuse hits: <existing util path>, <existing util path>   (0 if none)
verdict: <low-hanging | needs more design | not worth it yet> — <one line why>

-> /realm-concise approve <file>   (only if user wants to proceed)
```

## Boundaries

- This subcommand never writes code, never calls `/realm-planning`, never changes `status`. It only proposes.
- If the file's tier is `deep`, say so plainly and note what would need to change (get a test, reduce fan-in) before it's a safe candidate — don't produce a seam list that pretends the risk isn't there.
- Keep the seam list to what's actually visible in the file. Don't speculate about code you haven't read.
