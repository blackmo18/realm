# Node-Graph Knowledge Architecture

**Problem**: Caveman-compressed full docs (5 docs × ~1.5K tokens = 7.5K tokens per pull) still expensive.

**Solution**: Granular node linking + indexed lookup. Pull only what's needed.

---

## Node Structure

Each decision, function, class, discovery is a **discrete node** with metadata:

```yaml
# decisions/node-auth-flow.md
---
id: auth-flow
type: decision
title: Multi-stage authentication flow
tags: [auth, security, session]
status: active
depends_on: [oauth-provider, token-validation]
related: [login-ui, auth-service, session-refresh]
compressed: |
  Auth: 3-stage. OAuth → token gen → session cookie.
  Refresh: Silent via iframe, manual via endpoint.
  Revoke: Immediate on logout + 7d session expiry.
---

Full prose here (pulled only on expansion)
```

```yaml
# functions/node-validateUser.md
---
id: validateUser
type: function
class: AuthService
params: [token: string, context: RequestContext]
returns: User | null
tags: [auth, validation, critical-path]
status: active
depends_on: [token-codec, user-db]
implemented_by: [auth-middleware, api-guard]
compressed: |
  Validates JWT. Decodes token → verifies signature → checks expiry.
  Cache hit avoids DB lookup (99% case). Returns User or null.
  Called 2M+ times/day, <1ms p95.
---

Full implementation, benchmarks, edge cases...
```

---

## Index Structure (realm-index.json)

```json
{
  "nodes": {
    "auth-flow": { "file": "decisions/node-auth-flow.md", "type": "decision", "compressed_tokens": 18 },
    "validateUser": { "file": "functions/node-validateUser.md", "type": "function", "compressed_tokens": 22 },
    "UserService": { "file": "classes/node-UserService.md", "type": "class", "compressed_tokens": 45 }
  },
  "by_tag": {
    "auth": ["auth-flow", "validateUser", "UserService", "login-ui", "session-refresh"],
    "security": ["auth-flow", "token-validation", "rate-limit"],
    "critical-path": ["validateUser", "cache-lookup", "db-query"]
  },
  "by_name": {
    "validateUser": "validateUser",
    "UserService": "UserService",
    "LoginUI": "login-ui"
  },
  "dependencies": {
    "auth-flow": ["oauth-provider", "token-validation"],
    "validateUser": ["token-codec", "user-db"]
  },
  "inbound_links": {
    "token-codec": ["validateUser", "token-refresh"],
    "UserService": ["validateUser", "login-ui", "admin-panel"]
  }
}
```

---

## Query Operations

### Single Node (Compressed)
```bash
/realm-recall decision:auth-flow
# → Loads node header + compressed summary
# Cost: ~18 tokens
# Expansion: /realm-recall auth-flow --full

/realm-recall function:validateUser
# → Loads function signature + compressed description
# Cost: ~22 tokens

/realm-recall auth
# → Loads all nodes tagged 'auth', compressed
# Cost: 18 + 22 + ... = ~80 tokens (vs 7.5K for full docs)
```

### With Dependencies
```bash
/realm-recall validateUser --deps
# → validateUser (22) + token-codec (15) + user-db (18)
# Cost: ~55 tokens
# (vs pulling entire auth-service.md which might be 1K+)
```

### With Inbound Links
```bash
/realm-recall UserService --trace
# → Shows dependency tree including inbound links
# Cost: <10 tokens (no content, just link structure)
# (User reviews, then selectively expands branches)
```

### Full Trace
```bash
/realm-recall validateUser --trace
# → Shows full dependency tree visually
# Cost: Just index lookups, no content pull
# (User reviews, then selectively pulls branches of interest)
```

---

## Compression Format (Caveman Style)

Each node stores TWO versions:

```
compressed: |
  Validates JWT. Decodes → verifies → checks expiry.
  Cache hit = no DB. <1ms p95. 2M+/day.
  Called by: auth-middleware, api-guard.

full: |
  [Full implementation, benchmarks, edge cases, examples...]
```

**Compressed** pulled by default (~20 tokens/node).
**Full** pulled only when user asks or context budget allows.

---

## Integration: realm-phase Updates Index

After `realm-phase` detects changes:

1. Scans repo for new functions, classes, decisions
2. Updates realm-index.json
3. Auto-creates node stubs with compressed summaries
4. Flags them for review

```bash
realm-phase --update-index
# → Compares vault nodes against repo reality
# → Updates dependencies, inbound links
# → Marks stale nodes
```

---

## Token Math

| Approach | Tokens | Cost |
|----------|--------|------|
| Pull 5 full prose docs | 7.5K | High |
| Pull 5 compressed nodes | ~110 | **98% savings** |
| Pull 1 node + 3 deps (compressed) | ~80 | 99% savings |
| Pull tag (10 nodes, compressed) | ~220 | 97% savings |

---

## Implementation Priority

1. **realm-index.json** schema + builder script
2. **Node file format** (YAML + caveman compressed block)
3. **realm-recall** skill (query → load compressed → optionally expand)
4. **realm-phase** enhancement (auto-update index + compress)
5. **Dependency tracer** (visualize before pulling)

This turns the vault into a **lightweight RDF/knowledge graph** without the overhead of a full semantic system.
