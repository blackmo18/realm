# Contract Delta Gate

Phase 1 Step 7, only reached when Phase 1 touched an anchor that could be API-surface. Anchor touched ≠ trigger — gate is an explicit determination: is the change **response/request-shape affecting**?

This is the single source of truth for the whole contract pipeline (this gate, `write contract`, Phase 2's Contract Gate step) — decide once here, everything downstream trusts it without re-deriving.

| Affecting → fires Contract Delta | Not affecting → no Contract Delta |
|---|---|
| new endpoint/rpc/route/field returning data | internal refactor, shape unchanged |
| response field added/removed/renamed/retyped | perf/caching/logging-only change |
| request field added/removed/renamed/retyped | auth change not touching body/error shape |
| error/status shape changed | comment/formatting-only proto/schema edit |
| endpoint/field removed or deprecated | test-only change |

Ambiguous → default **not affecting** (false negative just delays to a later `write contract`; false positive churns a needless file).

Yes → add `## Contract Delta` to the Phase 1 plan: protocol, module(s), new/changed endpoints, consumers — resolution = `contract/SKILL.md` Steps 1-2. Protocol-agnostic (proto/Connect-RPC, REST, GraphQL).

No, or no anchor of that kind → omit the section, skip contract entirely.
