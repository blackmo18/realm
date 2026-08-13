# Anchor Resolution — enhancement mode

Phase 1 Step 2 (enhancement), filling anchor-set gaps after the vault/ADR `source_plan` pass. Graph before grep always; disambiguate every hit by `src=` path, never trust a bare label.

| Anchor kind | Resolve via (graph present) | Resolve via (graph absent) |
|-------------|-------------|-------------|
| file | `graphify explain "<file>"` — src path, community, neighbors | CLAUDE.md key-files, execution node file list |
| class | `graphify explain "<ClassName>"` | vault `classes/` nodes |
| function | `graphify explain "<fnName>"` | vault `functions/` nodes, then grep `export function <name>` |
| route | App Router convention — route string maps to dir, no search | same |
| api endpoint | same convention under `src/app/api/` | same |
| external api | `graphify explain "<ApiClient>"` | API client file (e.g. `EcommerceApi.ts`) |
| 1-hop callers | `graphify affected "<seedFile>" --depth 1` — typed `[relation] path:Lline` (enhancement breaks consumers, not dependencies) | investigator (see `investigator-rules.md`) |
| relation between two known anchors | `graphify path "A" "B"` | — |

Investigator is a fallback, not a default spawn — see `investigator-rules.md` for the four trigger conditions.
