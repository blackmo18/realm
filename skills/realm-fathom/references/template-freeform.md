# Freeform investigator

Answer `<query>` about the codebase under `<projectRoot>`.

Use `<graphifySeed>` as candidate locations. If graphify is stale, verify every seeded
fact against current code. If the match is merely thin, read seeded locations first and
search only to fill gaps. Do not repeat a repository-wide sweep.

Identify relevant entities with name, type, location, responsibility, and connection to
the question. Map the end-to-end flow. Cover the most likely interpretation first and note
material alternatives. Return caveman-compressed findings ordered by relevance.
