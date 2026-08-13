# Fathom Investigator Prompt Templates

Load-on-demand reference for `realm-agent-fathom`. Read this file once per run in Step 1.

---

## Template: function or class

```
Investigate <entityType> "<entityName>" in the codebase at <projectRoot>.

You are the backup crawler. Reason graphify wasn't trusted as-is: <graphifyReason>

Seed from graphify (candidate files/symbols — verify, don't re-derive):
<graphifySeed, or "none — cold search, use Grep/Glob directly" if empty>

If reason is staleness: treat the seed as a starting hint only, not fact —
files changed since it was built, so confirm current state with Read rather
than trusting seeded line numbers or signatures.
If seed present and reason is missing/thin (not staleness): Read the seeded
locations first, use Grep/Glob only to fill gaps the seed didn't cover.
Do not repeat a repo-wide sweep the seed already answered.

Extract and report:
1. Full signature — params, return type, generics, modifiers
2. Responsibility — one-liner: what it does (not how)
3. Execution flow — ordered bullets: what happens step-by-step when called
4. Key dependencies — internal calls, external libs, DB, I/O, network
5. Callers / entry points — who calls this and in what context
6. Error paths — exceptions thrown, error returns, edge cases handled
7. Guards and invariants — inline "DO NOT", precondition checks, assertion comments
8. Performance signals — benchmarks, complexity comments, known bottlenecks

Output: caveman-compressed. Code is ground truth — report what you find, not what you expect.
```

---

## Template: system

```
Investigate subsystem "<entityName>" in the codebase at <projectRoot>.

You are the backup crawler. Reason graphify wasn't trusted as-is: <graphifyReason>

Seed from graphify (candidate files/symbols — verify, don't re-derive):
<graphifySeed, or "none — cold search, use Grep/Glob directly" if empty>

If reason is staleness: treat the seed as a starting hint only, not fact —
files changed since it was built, so confirm current state with Read rather
than trusting seeded line numbers or signatures.
If seed present and reason is missing/thin (not staleness): Read the seeded
locations first, use Grep/Glob only to fill gaps the seed didn't cover.
Do not repeat a repo-wide sweep the seed already answered.

Map:
1. Boundary — what files/packages constitute this subsystem
2. Public surface — entry points, exported API, event emitters
3. Internal flow — how data moves through the subsystem
4. External dependencies — other subsystems, services, DBs it calls
5. Consumers — what calls into this subsystem and why
6. Configuration — env vars, config keys, feature flags affecting behavior
7. Known constraints — rate limits, size limits, timeout values, guards

Output: caveman-compressed, grouped by category.
```

---

## Template: freeform

```
Investigate this question about the codebase at <projectRoot>:
"<query>"

You are the backup crawler. Reason graphify wasn't trusted as-is: <graphifyReason>

Seed from graphify (candidate files/symbols — verify, don't re-derive):
<graphifySeed, or "none — cold search, use Grep/Glob directly" if empty>

If reason is staleness: treat the seed as a starting hint only, not fact —
files changed since it was built, so confirm current state with Read rather
than trusting seeded line numbers or signatures.
If seed present and reason is missing/thin (not staleness): Read the seeded
locations first, use Grep/Glob only to fill gaps the seed didn't cover.
Do not repeat a repo-wide sweep the seed already answered.

Find the relevant functions, classes, files, and flows that answer this question.
For each relevant entity:
- Name, type (function/class/file), location
- What it does (one-liner)
- How it connects to the question
- Key flow steps if it is a primary handler

Map the end-to-end flow that answers the question.
If multiple interpretations are possible, cover the most likely one first, note alternatives.
Output: caveman-compressed, ordered by relevance to the question.
```

---

## Output format

Print exactly this structure. Omit `── DRIFT ──` section entirely when `hasDrift: false`.

```
FATHOM: <query>
sources: code<✓ if codeFound else ✗>(<codeSource: graphify|investigator>)  vault:<✓ if vaultFound | ✗(not initialized) if vaultAvailable false | ✗(no nodes) if vaultAvailable true but vaultFound false>  graphify:<✓ if graphifyAvailable else ✗(no graph)><(stale — N changed) if graphifyStale>
─────────────────────────────────────────────────────────────────────

── FLOW ─────────────────────────────────────────────────────────────
<codeFindings — signature, responsibility, execution flow, callers, error paths, guards>

[if codeFound: false]
Cannot locate "<entityName or query>" in codebase.
Check spelling or run /realm-phase for a full scan.

── CONTEXT [vault] ──────────────────────────────────────────────────
<vaultContext — why it exists, ADR refs, architectural intent, invariant rationale, linked decisions>

[if vaultAvailable: false]
Vault not initialized. Run /realm-forge to enable architectural context.

[if vaultAvailable: true and vaultFound: false]
No vault nodes for this query.
Run /realm-phase then /realm-manifest to document this entity.

── DRIFT ────────────────────────────────────────────────────────────
<each VAULT DRIFT entry>
→ Vault likely stale. Run /realm-flourish to sync.

── VERDICT ──────────────────────────────────────────────────────────
<2-3 sentences: what it does (from code) + why it exists (from vault if available) + critical caveats or drift warnings>
```
