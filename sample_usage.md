# Realm — Sample Usage

## Bootstrap

```bash
/realm-forge        # once per project — scaffold vault dirs + realm-state.json
/realm-phase        # scan repo → diff vs vault → stage manifest-draft.md
/realm-manifest     # review draft → write nodes → archive
```

## Plan — free-form ideation canvas → vault

```bash
# Single section
/realm-plan plan "refactor auth to JWT"              # planner → decisions/ + sessions/
/realm-plan investigate "caching bug"                # cavecrew-investigator → discoveries/
/realm-plan deep-research "event sourcing tradeoffs" # firecrawl+exa → discoveries/ + learning/
/realm-plan scaffold "NotificationService"           # code-architect → classes/ + systems/ stubs
/realm-plan design "API versioning strategy"         # architect → decisions/ + architecture.md
/realm-plan design --ui "checkout flow"              # adds a11y considerations

# Chain — generation order hint, not a hard pipeline
/realm-plan deep-research->design->plan "auth refactor"
/realm-plan investigate->plan "caching bug"
/realm-plan scaffold->design->plan "PaymentService"

# Session management
/realm-plan list                                     # show all in-progress work items
/realm-plan resume auth-refactor                     # continue saved canvas
```

Chain defines which agents run and in what order to populate sections. After generation, one free-form loop: update any section, add sections, skip, save, resume across sessions. `finalize` promotes sections to real vault nodes.

## Sync

```bash
/realm-flourish                        # quick sync after small code changes (git-diff based)
/realm-phase function:validateUser     # targeted rescan — 10-20× cheaper than full phase
/realm-convey                          # compress conversation → pick topics → targeted phase
```

## Query — vault only

```bash
/realm-recall validateUser             # compressed function node (~20 tokens)
/realm-recall validateUser --with-deps # function + deps (~80 tokens)
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
/realm-status       # node counts, stale docs, pipeline health
```
