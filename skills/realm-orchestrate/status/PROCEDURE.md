# status — orchestration status

Only reached when the routing guard already confirmed `ORCH_ACTIVE=true`. No
plan re-read, no vault scan, no `find`.

```bash
python3 "<realmOrchestrateSkillDir>/scripts/orchestrate.py" status --project-root .
```

Print the output verbatim (caveman-compress the surrounding sentence, not the
block itself — it's already terse `KEY=value` / table lines). Do not re-derive
counts or state from `run.json` yourself; the script already computed them.

End with one line pointing at the next action:

```
→ /realm-orchestrate resume to continue, /realm-orchestrate abort to drop it.
```
