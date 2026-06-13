---
name: realm-agent-compress
description: DEPRECATED — compression and validation merged into realm-agent-write (haiku). This stub exists for backwards compatibility only. Do not invoke directly.
tools: ["Read"]
model: haiku
---

## Deprecated

Compression and validation are now handled inline by `realm-agent-write`.

If you see this agent invoked, the calling skill is outdated. Update `realm-manifest/SKILL.md` to spawn `realm-agent-write` directly (skip the compress step).

Print and STOP:
```
realm-agent-compress is deprecated.
Compression merged into realm-agent-write.
Run /realm-manifest — it now uses a single agent.
```
