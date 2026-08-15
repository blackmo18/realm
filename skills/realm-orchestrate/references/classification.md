# Bundle Classification — MECHANICAL / COMPLEX

## Signals

| Signal | Classification |
|--------|----------------|
| Creates only new files — no edits to existing files | MECHANICAL |
| Fully specified in `PLAN_SLICE` (no inference or contract derivation needed) | MECHANICAL |
| No integration into existing routes, middleware, or services | MECHANICAL |
| No atomic transactions spanning multiple files/systems | MECHANICAL |
| No auth, payments, or PII code | MECHANICAL |
| Edits existing files | COMPLEX |
| Integrates into existing route, middleware, or service | COMPLEX |
| Atomic transaction (multi-table, DB + external service) | COMPLEX |
| Output contract must be inferred (upstream bundle output unclear) | COMPLEX |
| Auth / payments / PII code | COMPLEX |
| Modifying a test suite with non-trivial fixture setup | COMPLEX |

One COMPLEX signal → COMPLEX. All-MECHANICAL → MECHANICAL.

Store per bundle: `B1:MECHANICAL B2:COMPLEX …` (part of the WAVE LEDGER, see
`references/contracts.md` §5).

## Model routing

| Spawn | `model` param | When |
|-------|---------------|------|
| `realm-agent-plan-implementor` (MECHANICAL, attempt 1) | `"claude-haiku-4-5-20251001"` | Additive/new files, fully spec'd, no integration |
| `realm-agent-plan-implementor` (MECHANICAL, attempt 2 — retry) | omit (inherit) | Escalation exception — see `../dispatch/PROCEDURE.md` |
| `realm-agent-plan-implementor` (COMPLEX, any attempt) | omit (inherit) | Edits existing code, integration, transactions, auth |
| `cavecrew-builder` | omit (inherit) | Always inherit — already cheap |
| `cavecrew-reviewer` | frontmatter pins `model: haiku` | Frontmatter overrides Task inheritance — this is intended, not a bug |
| `cavecrew-investigator` | omit (inherit) | Always inherit |

User override from P3 confirmation takes precedence over this table. No self-escalation
beyond this table's stated exception (attempt-2 MECHANICAL retry).
