# Realm Knowledge Workflow: Token-Efficient Integration

**Goal**: Write knowledge once in Obsidian, query surgically, sync efficiently—all while saving 85-98% tokens vs full-doc pulls.

---

## Three Layers

### Layer 1: Write (Obsidian Native)

**You write here:**
- `decisions/<id>.md` — Architecture decision with [[wikilinks]] to implementations
- `functions/<id>.md` — Function/method with [[depends_on]] and [[called_by]] links
- `classes/<id>.md` — Service/class with [[dependencies]] and [[dependents]] links
- `discoveries/<date>-<topic>.md` — Session notes, findings, linked to [[decision]] and [[function]] nodes
- `sessions/<date>-<summary>.md` — What was discovered/decided/changed, with [[node]] references

**Obsidian features work automatically:**
- Graph view: visually explore dependencies
- Backlinks panel: "what calls validateUser?" → lists all inbound [[links]]
- Tag pane: filter by #auth, #critical-path, #performance
- Search: find by function name, decision title, class name
- Aliases: link to `validateUser` even if filename is `node-validateUser.md`

---

### Layer 2: Sync (realm Pipeline)

**realm-forge** (once per project):
```bash
/realm-forge
→ Creates vault dirs: decisions/, functions/, classes/, systems/, discoveries/, sessions/
→ Writes .realm/realm-state.json (project anchor)
→ Scaffolds templates with frontmatter + compressed + full structure
```

**realm-phase** (after code changes, before writing):
```bash
/realm-phase
→ Scans repo with cavecrew-investigator
→ Finds new functions, classes, decisions, patterns
→ Diffs against existing vault docs
→ Stages manifest-draft.md (review before committing)
→ Cost: 2-3 minutes, zero vault writes
```

**realm-manifest** (after phase review):
```bash
/realm-manifest
→ Writes staged nodes to vault (decisions/, functions/, classes/)
→ Auto-generates backlinks between nodes
→ Updates session log with what was synced
→ Archives draft for history
→ Cost: <1 minute vault write
```

**realm-status** (anytime):
```bash
/realm-status
→ Shows what nodes exist (committed/planned/stale)
→ Lists tags and node counts
→ Suggests queries for pulling context
→ Zero scans, instant read
```

---

### Layer 3: Query (realm-recall)

**Pull by function:**
```bash
realm-recall function:validateUser
→ Loads: frontmatter + Compressed section
→ Cost: ~20 tokens
→ Shows: signature, one-liner, depends_on, called_by

realm-recall function:validateUser --with-deps
→ Adds: all [[depends_on]] nodes (compressed)
→ Cost: ~80 tokens (vs 500+ for full prose docs)

realm-recall function:validateUser --expand
→ Loads: full prose after reviewing compressed
→ Cost: +80 tokens (user choice, not automatic)
```

**Pull by tag (cluster query):**
```bash
realm-recall @auth --trace
→ Shows dependency tree (no content, just links)
→ Cost: <10 tokens
→ User visually explores in Obsidian

realm-recall @auth --compressed
→ Loads all #auth nodes, compressed (~20 tokens each)
→ Cost: ~150-200 tokens for ~10 nodes
→ Savings: 85-90% vs full prose docs

realm-recall @auth --count
→ Estimates cost before pulling
→ "10 nodes, ~200 if compressed, ~1500 if full"
```

**Pull by dependency (impact analysis):**
```bash
realm-recall decision:auth-flow --with-implementations
→ Decision + all [[AuthService]], [[validateUser]] that implement it
→ Cost: ~80-120 tokens

realm-recall function:validateUser --with-dependents
→ Function + everything that [[calls it]]
→ Cost: ~60-100 tokens
```

---

## Workflow: Single Coding Session

### Start of Session

```bash
/realm-status
→ Prints what nodes exist, suggests queries
→ Quick orientation: "what decision applies to what I'm building?"

realm-recall @auth --trace
→ Shows auth decision tree, zero tokens
→ User visually explores in Obsidian
→ Decides "I need validateUser context"

realm-recall function:validateUser --with-deps
→ ~80 tokens, includes all token validation, user lookup
→ Claude now has focused context for this task
```

**Token cost so far: ~80 tokens** (would be 500-800 for full docs)

### During Coding

New discovery: "validateUser cache hit rate is 99%, which is why token validation is so cheap."

```bash
/realm-session
→ Logs to sessions/<YYYY-MM-DD>-<topic>.md
→ Links: "discovered: [[validateUser]] cache hit rate, relates to [[decision:auth-flow]]"
```

### End of Session (or after milestone)

```bash
/realm-phase
→ Scans repo: finds new caching logic you added
→ Generates: discovery note, updates to function node
→ Stages: manifest-draft.md for review

(Review draft: "looks good")

/realm-manifest
→ Writes: updated validateUser node with new performance notes
→ Writes: session log entry with what changed
→ Archives: draft for history
```

**Next session**: `/realm-status` shows updated nodes; Claude can query latest without re-scanning.

---

## Token Math: Real Scenarios

### Scenario 1: "I need auth context"

**Old way (caveman extract full docs):**
```
Pull: auth-service.md (1.2K), token-strategy.md (800), session-refresh.md (950)
Cost: ~3K tokens
Resolution time: slow, lots of irrelevant prose
```

**New way (node-graph query):**
```bash
realm-recall @auth --trace                # <10 tokens
→ Review tree in Obsidian

realm-recall decision:auth-flow --compressed # ~20 tokens
realm-recall function:validateUser --with-deps # ~80 tokens

Cost: ~110 tokens
Savings: 96%
```

### Scenario 2: "Why does validateUser call UserDB?"

**Old way:**
Pull entire auth-service.md (1.2K tokens) to find that one dependency.

**New way:**
```bash
realm-recall function:validateUser --compressed # ~20 tokens
→ See depends_on: [[UserDB]]
```

**Savings: 98%**

### Scenario 3: "What calls validateUser?"

**Old way:**
Manual grep of codebase + cross-check docs = slow + error-prone

**New way:**
```bash
realm-recall function:validateUser --trace # <10 tokens
→ Shows called_by: [[auth-middleware]], [[LoginUI]]

Or in Obsidian: open validateUser node → Backlinks panel shows all callers
```

**Cost: ~10 tokens**

### Scenario 4: "Show me all critical-path functions"

**Old way:**
Pull 4-5 service files (3-4K tokens) to extract critical functions.

**New way:**
```bash
realm-recall #critical-path --trace          # <10 tokens
→ Shows structure

realm-recall #critical-path --compressed    # ~200 tokens
→ All critical functions + dependencies, compressed
```

**Savings: 90%**

---

## Integration with Claude Sessions

### Recommended hooks

Add to `.claude/CLAUDE.md` or agent config:

```bash
Stop hook:
  echo "Session note: run /realm-session to log discoveries"
  
Pre-session hook (future):
  /realm-status
  (If stale docs exist or phase.draftReady: recommend /realm-phase first)
```

### Standard opening for each session

```bash
# Quick orient
/realm-status

# Pull focused context if starting on specific area
realm-recall function:validateUser --with-deps

# Or explore by decision
realm-recall decision:auth-flow --trace
```

---

## Obsidian as the Interface

Users don't need `/realm-recall` for browsing—Obsidian handles it natively:

- **Graph View**: see all nodes and their connections (free visual query)
- **Backlinks**: "what calls this?" or "what depends on this?"
- **Tag Pane**: filter by #auth, #critical-path, etc.
- **Search**: find by function name, decision title
- **Aliases**: use clean [[validateUser]] even if filename is node-validateUser.md

**Claude uses `/realm-recall`** for pulling structured context into chat.
**Humans use Obsidian** for exploring the graph visually.

---

## Compression Policy (Caveman Style)

Every node stores TWO versions:

```markdown
---
id: validateUser
type: function
---

# validateUser()

Compressed: Validates JWT. Decodes → verifies → checks expiry. Cache: 99%. <1ms p95.

## Full Implementation

[Full prose: 200 lines of code docs, examples, edge cases, benchmarks...]
```

**Default pull**: Load only Compressed (~20 tokens).
**User expand**: Load Full if needed (~80 tokens).
**Obsidian native**: User can read full prose in editor anytime.

---

## Maintenance: Keeping Nodes Fresh

### After code changes:
```bash
/realm-phase
→ Detects divergence (cavecrew-investigator scans repo)
→ Stages updates
→ Never writes until user reviews
```

### Stale detection:
realm-status shows `stale` docs when:
- Function signature changed but node not updated
- Service renamed but old decision still references old name
- Performance changed (new benchmark)

**Goal**: vault stays current with zero manual sync overhead.

---

## Token Efficiency Summary

| Operation | Old Way | New Way | Savings |
|-----------|---------|---------|---------|
| Pull function + deps | 500-800 tokens | ~80 tokens | 90% |
| Pull auth cluster | 3-4K tokens | ~200 tokens | 95% |
| Show dependency tree | 500 tokens | <10 tokens | 98% |
| Single decision context | 1K tokens | ~20 tokens | 98% |
| Tag-based cluster query | 2-3K tokens | ~150-300 tokens | 85-95% |

**Key insight:** Compressed node headers (frontmatter + one-liner) are ~20 tokens. Full prose docs are 500-2K tokens. Lazy expansion lets users choose depth after reviewing compressed.

---

## Next Steps

1. Update your existing skills (realm-forge, realm-phase, realm-manifest, realm-status) ✓
2. Create realm-recall skill for queries ✓
3. Set up your Obsidian vault with initial structure via `/realm-forge`
4. Run `/realm-phase` to scan your project and stage first nodes
5. Run `/realm-manifest` to write nodes to vault
6. Use `/realm-recall @tag --trace` to explore visually
7. Add Stop hook to prompt `/realm-session` at end of each session

You now have a knowledge system that:
- ✓ Costs 85-98% fewer tokens than full-doc extraction
- ✓ Integrates with Obsidian natively (graph view, backlinks, tags)
- ✓ Syncs repo↔vault changes automatically (realm-phase)
- ✓ Supports lazy expansion (pull compressed, expand only what matters)
- ✓ Grows incrementally (add nodes as you code)
