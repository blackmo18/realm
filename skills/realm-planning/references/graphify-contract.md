# Graphify Contract

Phase 1 discovery defaults to the `graphify` CLI when `graphify-out/graph.json` exists — pure graph traversal, zero LLM tokens, far cheaper than an investigator spawn.

| Command | Returns | Cost |
|---|---|---|
| `graphify query "<topic>" --budget 500` | `Traversal:` header (`Start:` seed labels, node count) + flat `NODE label [src=path loc=Lnn community=N]` list | ~475 tok |
| `graphify affected "<X>" --depth 1` | typed blast radius: `label [relation] path:Lline` | ~300-500 tok |
| `graphify explain "<X>"` | one node: ID, `src` path+line, type, community, degree, neighbor labels (no paths) | ~110 tok |
| `graphify path "A" "B"` | shortest chain, direction + confidence tier | ~40 tok |

Guardrails:
- **Drift guard**: seeding is label string match. A topic whose words aren't node labels drifts silently — ranking can put unrelated files above the real target. Retry once with the vocab-expansion recipe (`.claude/skills/graphify/references/query.md`) before concluding greenfield.
- **Disambiguate by `src=` path, never by bare label** — node IDs are pre-#1504, same-named files (e.g. many `page.tsx`) collide.
- **NEVER** Read or grep `graph.json` directly (10+ MB) — always through the CLI.
- **NEVER** read `GRAPH_REPORT.md` whole (~230 KB / ~60k tok) — section-anchored `sed`/`grep` only. Anchors: `## Community Hubs (Navigation)` L12, `## God Nodes` L938, `## Communities` L973.
- `graphify-out/wiki/index.md` may not exist — do not assume it.
- No per-subcommand `--help` — `graphify query --help` runs a real (garbage) traversal, it does not print usage.
- Graph absent or stale → fall back to the legacy grep/investigator path (see `phase1/SKILL.md` Step 1).
