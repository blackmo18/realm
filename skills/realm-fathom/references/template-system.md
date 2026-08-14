# Subsystem investigator

Investigate subsystem `<entityName>` under `<projectRoot>`.

Use `<graphifySeed>` as candidate locations. If graphify is stale, verify every seeded
fact against current code. If the match is merely thin, read seeded locations first and
search only to fill gaps. Do not repeat a repository-wide sweep.

Return caveman-compressed findings covering subsystem boundary, public surface, internal
data flow, external dependencies, consumers, configuration, and constraints.
