# Plan Mode Contract

Governs both phases. Each phase runs its own `EnterPlanMode` → work → `ExitPlanMode` cycle — Phase 2's approval is separate from Phase 1's, not inherited.

## Entry

Call `EnterPlanMode` before any context gathering or file selection for that phase. All read/investigate/spawn steps inside the phase run read-only under it.

**Fallback** — `EnterPlanMode` unavailable (non-interactive harness): prose gate instead. No downstream phase, no writes, until the user types explicit approval text.

## Write Boundary

No `Write` tool call anywhere in a phase until that phase's `ExitPlanMode` (or prose-gate approval) lands. This includes vault writes (`execution/<NNN>-exct-<slug>.md`, `write adr` files, contract files) — all of them wait for approval, none happen speculatively during exploration.

## Triggers That Re-Check This

`write contract` and `write adr` can fire mid-phase (e.g. right after Phase 1 approval, before Phase 2 starts). If plan mode is still active when one of these triggers: call `ExitPlanMode` first with the pending write(s) as the plan, proceed only after approval. Never attempt `Write` inside plan mode regardless of which trigger caused it.
