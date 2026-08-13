# Scoring — formula and tiers

Loaded by SKILL.md only when explaining a score to the user. All values are computed in `scripts/concise.py`; nothing here is re-derived by an LLM.

## Formula

```
size      = min(loc / minLoc, 3.0) / 3.0        # 0..1, caps at 3x threshold
isolation = 1 / (1 + fanIn)                     # low fan-in -> safe to move
safety    = 1.0 if hasTest else 0.4
heat      = min(churn / 20, 1.0)                # commits touching file, last 12mo

score = round(100 * (0.40*size + 0.25*isolation + 0.20*safety + 0.15*heat))
```

Weights, in order of intent:

- **size (0.40)** — the primary signal. It's a god-file scan; bigger files score higher.
- **isolation (0.25)** — few importers means a refactor's blast radius is small. This is the main input to "least impact."
- **safety (0.20)** — a co-located test means regressions get caught. No test lowers the score's confidence, not the file's size problem.
- **heat (0.15)** — actively-changed files are worth prioritizing (a refactor pays off sooner) but this is the weakest signal, easiest to be noisy.

## Tiers

```
low-hanging:  fanIn <= 2  and hasTest  and loc < 900
deep:         fanIn >= 8  or (not hasTest and loc >= 900)
moderate:     everything else
```

`low-hanging` is the direct answer to "which file can be cleaned up with least impact" — small blast radius, safety net present, not enormous. `deep` files need `/realm-concise recommend <file>` before anyone should approve them; high fan-in or an untested giant is exactly where an unplanned refactor breaks something invisible.

## Reading churn without git history

`compute_churn` runs one `git log --name-only --since=12.months` and counts path occurrences. If the directory isn't a git repo, or the command fails, churn is `0` for every file — `heat` drops out of the score silently rather than erroring. A fresh clone or a project without git history still gets usable size/isolation/safety scores.
