# Contract Template

Used by `realm-planning/contract`. One file per API **module** (proto
service, REST route group, or GraphQL schema) — not per individual endpoint.
Protocol-agnostic: pick the endpoint block that matches what Step 1 resolved.

---

```markdown
---
id: <slug>-api-contracts
title: "<ModuleName> API Contracts"
type: contract
status: draft | active
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [contract, api, <slug>]
links:
  - "[[ADR-<NNN>-<slug>]]"           <!-- omit if ADR not written yet -->
  - "[[planning/<NNN>-plan-<slug>]]" <!-- omit if not written yet -->
---

# <ModuleName> API Contracts

**Protocol**: proto (connect-rpc) | REST | GraphQL
**Source**: `<path to .proto | route file | .graphql schema>`

## Endpoints

<!-- proto (connect-rpc) endpoint block -->
### <MethodName>

- **Protocol**: proto (connect-rpc)
- **RPC**: `<ServiceName>/<MethodName>`
- **Status**: draft | implemented
- **Request** — `<RequestMessage>`

  | Field | Type | Notes |
  |---|---|---|
  | field_name | type | meaning / constraint |

- **Response** — `<ResponseMessage>`

  | Field | Type | Notes |
  |---|---|---|
  | field_name | type | meaning |

- **Auth/Permission**: <entitlement or gate name, or "none">
- **Consumers**: <module/route list>

<!-- REST endpoint block -->
### <METHOD> <path>

- **Protocol**: REST
- **Route**: `<METHOD> /api/orders/:id`
- **Status**: draft | implemented
- **Request** — path/query params + body shape

  | Field | Location | Type | Notes |
  |---|---|---|---|
  | field_name | path \| query \| body | type | meaning / constraint |

- **Response** — status code + body shape

  | Field | Type | Notes |
  |---|---|---|
  | field_name | type | meaning |

- **Auth/Permission**: <entitlement or gate name, or "none">
- **Consumers**: <module/route list>

<!-- GraphQL endpoint block -->
### <query|mutation|subscription> <fieldName>

- **Protocol**: GraphQL
- **Operation**: `<query|mutation|subscription> <fieldName>`
- **Status**: draft | implemented
- **Arguments**

  | Arg | Type | Notes |
  |---|---|---|
  | arg_name | type | meaning / constraint |

- **Return type** — `<TypeName>`

  | Field | Type | Notes |
  |---|---|---|
  | field_name | type | meaning |

- **Auth/Permission**: <entitlement or gate name, or "none">
- **Consumers**: <module/route list>

<!-- repeat ### per endpoint, ordered as declared in source; a module file uses exactly one block style, matching its resolved protocol -->
```

Field notes:
- `status` (frontmatter) — `draft` until the handler/resolver has a working implementation; flip to `active` once confirmed (grep/anchor, never assume).
- `status` (per-endpoint) — tracks individually; a module file can mix draft + implemented rows during rollout.
- `Consumers` — module/route granularity, not individual call sites.
- Never mix endpoint block styles in one file — a module's protocol is fixed by Step 1 resolution.
