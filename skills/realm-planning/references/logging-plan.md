# Logging Plan Requirements

`code-architect` (Phase 2 Step 3) must produce this for every impl task. Existing logging framework if present; otherwise name the injection point (middleware/wrapper/decorator).

| Rule | Requirement |
|------|-------------|
| Trace | `trace`-level logs on entry/exit of critical functions and request handlers |
| Inputs | Log important non-PII inputs (IDs, flags, counts, enums — never email, name, token, card, address) |
| Outputs | Log important non-PII outputs (status, result type, counts, error codes — never raw user data) |
| Branch points | Log every decision branch in critical flows (path taken + why, one structured line) |

**Critical flows** = auth, payments, routing, entitlement, webhooks, anything mutating state or gating access.

Per task, name: log level, fields to emit, branch points, PII fields excluded. This is the same content that lands in each task's **Logging** field in `plan-template.md`.
