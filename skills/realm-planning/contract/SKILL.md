---
name: realm-planning:contract
description: >
  Draft/write a readable API contract file for an API surface (proto/Connect-RPC
  service, REST route group, or GraphQL schema) that is new or changing in the
  current plan. Lets a consumer (frontend, other backend module) start against
  the contract before Phase 2 or implementation lands. Protocol-agnostic —
  not tied to WSC's current Connect-RPC stack. Triggered from Phase 1 Step 7
  (embedded Contract Delta) or explicitly via "write contract" after Phase 1
  approval.
---

# realm-planning — Contract

One file per API **module** — the unit consumers think in terms of, not per
individual endpoint. A module can hold multiple endpoints (a proto file can
declare multiple `service` blocks — see `backend/proto/wsc/v1/pos.proto`:
`PosService`, `CatalogService`, `ShiftService`; a REST route group is
everything under one resource path prefix; a GraphQL schema is one module
unless it's split by domain).

Protocol-agnostic by design — WSC is Connect-RPC only today, but this fragment
must not assume that. Same steps, different resolution table in Step 1.

## Trigger

Gate already decided in `phase1/SKILL.md` Step 7 (`../references/contract-delta-gate.md`) — trust it, don't re-derive.
No `## Contract Delta` in the approved plan → this fragment never runs.

- `## Contract Delta` present → user says `write contract` / `draft contract`
  any time after Phase 1 approval. Standalone — no Phase 2 or `write adr`
  dependency, that's the point (unblock consumer early).
- Existing contract file for the resolved slug → update in place (append new
  endpoints, mark changed ones, bump `updated:`). Never duplicate.

## Step 1 — Resolve module scope + protocol

Reuse the Phase 1 Anchor Set — no re-scan. Identify protocol from the anchor's
`src=` path / kind, then resolve module scope per row:

| Protocol | Module unit | Where to find endpoints |
|---|---|---|
| proto (Connect-RPC/gRPC) | `service <Name> { ... }` block | grep `rpc \|^message ` in the one resolved `.proto` file |
| REST | route group (shared path prefix / router file) | grep `router\.\(get\|post\|put\|patch\|delete\)\|@Get\|@Post\|...` (match project's router/framework idiom) or OpenAPI/Swagger spec if one exists |
| GraphQL | schema file or domain-scoped resolver module | grep `type Query\|type Mutation\|type Subscription\|extend type` in the resolved `.graphql`/schema file, or resolver map file |

Changed/new endpoints only for enhancement mode (diff against current file);
full endpoint list for anchored-new/greenfield.

Anchor table missing line numbers → one targeted grep on the single resolved
file, not a broader search. Never guess protocol from project defaults — read
the anchor's actual file extension/location.

## Step 2 — Resolve consumers

Graph present: `graphify affected "<resolved file>" --depth 1` — typed blast
radius, keep caller/import relations only. Works the same regardless of
protocol; the anchor is a file either way (`.proto`, route file, `.graphql`).
Graph absent: grep the generated/imported client for proto (`gen/go`,
`gen/ts`), grep fetch/axios/client calls to the route path for REST, grep
query/mutation document imports for GraphQL.

List consumer **modules/routes**, not individual call sites (e.g.
`frontend/app/menu-builder`, not every `.tsx` that imports the client).

## Step 3 — Slug + filename

Slug = kebab-case of the module name, protocol-specific suffix stripped:
- proto: `<ServiceName>` minus trailing `Service` (`CatalogService` → `catalog`)
- REST: route group name (`/api/orders/*` → `orders`)
- GraphQL: schema/domain name (`OrderSchema` / `orders.graphql` → `orders`)

Filename convention: `../references/vault-conventions.md`.

## Step 4 — Write

Use `../references/contract-template.md`. Write to
`<projectDir>/contracts/<slug>-api-contracts.md` (create `contracts/` if
missing — vault already has the empty dir from bootstrap in most projects).

Frontmatter `status`:
- `draft` — endpoint declared (proto rpc / route handler stub / GraphQL field), no working implementation yet
- `active` — implementation confirmed (confirm by anchor/grep, never assume)

Per-endpoint `status` tracks independently — a module file can mix draft and
implemented rows during rollout.

`links:` omit rules: `../references/vault-conventions.md` — contract can land
before planning/execution/ADR files exist (that's the unblock case).

This file is also what Phase 2 Step 1 gates on — a filename existence check
against `contracts/<slug>-api-contracts.md`, protocol-agnostic. Land this
write before Phase 2 is attempted for any Contract Delta topic.

## Step 5 — Backlink (only for files that already exist)

Most common ordering: contract is written right after Phase 1 approval, before
`write adr` or Phase 2 — so usually nothing exists yet to backlink into. Check
anyway, cheapest first:

- `planning/<NNN>-plan-<slug>.md` exists → append `- "[[<slug>-api-contracts]]"` to its `links:`
- `decisions/ADR-<NNN>-<slug>.md` exists → same
- `execution/<NNN>-exct-<slug>.md` exists → same

Backlink direction for whichever of these gets written *later*: `../references/vault-conventions.md`.

## Step 6 — Summary

```
write contract complete

  contract:  contracts/<slug>-api-contracts.md
  protocol:  proto (connect-rpc) | REST | GraphQL
  module:    <ServiceName / route group / schema name>  (<n> endpoints)
  consumers: <consumer list>
  status:    draft | active
```
