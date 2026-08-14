# Plan Mode Contract

Governs both phases. Each phase enters the host's native planning mode, performs
read-only work, and presents the plan for approval before exiting. Phase 2's
approval is separate from Phase 1's and is not inherited.

## Entry

Enter native planning mode before context gathering or file selection for that
phase. Keep all read, investigation, and permitted delegation steps read-only.

**Fallback** — when native planning mode is unavailable, use a prose approval
gate. Do not start a downstream phase or write until the user explicitly approves.

## Write Boundary

Do not write anywhere in a phase until native plan approval (or prose-gate
approval) lands. This includes vault execution, ADR, and contract files.

## Triggers That Re-Check This

`write contract` and `write adr` can fire between phases. If planning mode is
still active, present the pending writes as the plan and exit only after approval.
Never write while the host still considers the phase read-only.
