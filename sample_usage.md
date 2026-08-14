# Realm — Sample Usage

## Bootstrap

```bash
/realm-forge        # once per project — scaffold vault dirs + realm-state.json
```

Codex invocation uses `$realm-forge`; the examples below use Claude Code/Gemini slash syntax.

## Plan

```bash
/realm-planning "refactor auth to JWT"          # Phase 1: architecture and ADR direction
/realm-planning "refactor auth to JWT" --phase2 # Phase 2: implementation blueprint
/realm-planning "add request tracing" --lite    # affected files + must-pass tests only
```

## Query — vault only

```bash
/realm-recall validateUser             # compressed function node (~20 tokens)
/realm-recall validateUser --deps      # function + deps (~80 tokens)
/realm-recall @auth                    # all #auth nodes (~200 tokens)
/realm-recall "why JWT"                # semantic → decision nodes
/realm-recall auth --trace             # link tree only (<10 tokens)
```

## Query — deep investigation (code + vault)

```bash
/realm-fathom function:validateUser          # signature, flow, callers + vault why + drift check
/realm-fathom class:AuthService              # full class: methods, deps + vault ADRs
/realm-fathom system:PaymentPipeline         # subsystem boundary + vault architectural intent
/realm-fathom "how does auth flow work"      # freeform → maps relevant files/functions end-to-end
/realm-fathom validateUser                   # bare name — type auto-detected
```

`realm-fathom` runs live code and vault queries in parallel. Live code is ground truth. Vault adds why/ADR context. Any conflict is flagged as `VAULT DRIFT` — never silently blended.

Use before modifying unfamiliar code. Use to audit whether vault docs match current behavior.

## Status

```bash
/realm-status       # live node counts, stale docs, and vault health
```

For Codex, replace each leading `/` with `$`.
