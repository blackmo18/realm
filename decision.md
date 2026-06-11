 /btw once this is done how can we efficiently pull inform from real, and sync project decision, architecture, function, result, input into it?

    1. Reads realm-state.json → knows which docs exist
    2. Reads overview.md + relevant ADRs for current work area
    3. Caveman-compresses them → injects into context cheap
    4. Main thread now has live architectural context before touching code

    For specific queries: realm-check decisions loads just ADRs. realm-check arch loads just architecture.md. Targeted, cheap.

    ---
    Push: Code/Session → Realm

    Four sync surfaces:

    ┌─────────────────────┬────────────────────────────────┬───────────────────────────────────────────────────────────────────────────────┐
    │        What         │              When              │                                      How                                      │
    ├─────────────────────┼────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────┤
    │ Architecture drift  │ After adding/changing services │ realm-phase re-scans → finds gap → realm-manifest patches architecture.md     │
    ├─────────────────────┼────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────┤
    │ New decision        │ During coding session          │ /realm-adr "title" — quick ADR skill that writes directly, no phase needed    │
    ├─────────────────────┼────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────┤
    │ Session discoveries │ End of session                 │ /realm-session — writes sessions/YYYY-MM-DD.md from conversation context      │
    ├─────────────────────┼────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────┤
    │ Milestone done      │ After milestone completes      │ realm-status shows stale flag; /realm-manifest updates overview.md checkboxes │
    └─────────────────────┴────────────────────────────────┴───────────────────────────────────────────────────────────────────────────────┘

    Automatic push via Stop hook: 
    Wire a Stop hook that prompts you to log the session:
    "Stop": [{ "command": "echo 'Run /realm-session to log this session'" }]
    Not fully automatic (Claude still writes it) but you never forget.
    
    ---
    The Real Efficiency Win

    realm-phase is the sync engine. Run it after any significant work block:
    - It diffs repo reality vs vault (via cavecrew-investigator)
    - Marks diverged docs stale
    - Stages updates in manifest-draft.md
    - You review, then realm-manifest commits

    The cost: one realm-phase + one realm-manifest per work block. Maybe 2 minutes. The payoff: every new Claude session starts with accurate architectural context instead of re-deriving it from scratch.

    Compression is the token multiplier — vault docs stay caveman-compressed, so pulling 5 docs into context costs ~40% of the tokens of prose docs. You can afford to pull more context per session.
