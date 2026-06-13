# Realm — Visual Reference

Pipeline flows, vault structure, and guard logic for [Realm](README.md).

---

## Table of Contents

- [Core Pipeline](#core-pipeline)
- [Conversation Capture (realm-convey)](#conversation-capture-realm-convey)
- [Ideation Canvas (realm-plan)](#ideation-canvas-realm-plan)
- [Queries](#queries)
- [Vault Structure](#vault-structure)
- [Local Pipeline State (.realm/)](#local-pipeline-state-realm)
- [Guards](#guards)

---

## Core Pipeline

Decision capture from conversation to vault:

```mermaid
flowchart TD
    A(["/realm-forge"]):::cmd -->|"bootstrap vault dirs + realm-state.json"| B

    B(["/realm-convey"]):::cmd -->|"compress conversation → ADR interview"| C1
    C1[".realm/manifest-draft.md\nADR nodes + discoveries"]:::file -->|"review draft"| C

    C(["/realm-manifest"]):::cmd -->|"write nodes → link → archive draft"| V

    V[("Obsidian Vault\ndecisions/ · discoveries/ · sessions/")]:::vault

    classDef cmd   fill:#1e1e2e,stroke:#89b4fa,color:#cdd6f4,rx:6
    classDef file  fill:#1e1e2e,stroke:#a6e3a1,color:#cdd6f4,rx:4
    classDef vault fill:#1e1e2e,stroke:#f38ba8,color:#cdd6f4,rx:8
```

> No vault writes at convey time — review the staged draft before committing.

---

## Conversation Capture (realm-convey)

Extract decisions from a conversation and stage them as ADR nodes:

```mermaid
flowchart TD
    CV(["/realm-convey"]):::cmd -->|"compress + dissect conversation"| TL["topic list\ndecisions · discoveries · session"]:::file
    TL -->|"user selects items"| SEL{selection}:::choice

    SEL -->|"decisions chosen"| INT["structured ADR interview\nper decision (inline)"]:::step
    SEL -->|"discoveries only"| ST[".realm/manifest-draft.md\ndiscovery stubs"]:::file
    SEL -->|"none"| NO["no-op"]:::warn

    INT -->|"answered"| DR[".realm/manifest-draft.md\nADR nodes with rationale + rejected + consequences"]:::file
    DR --> RM(["/realm-manifest"]):::cmd
    RM --> V[("Obsidian Vault")]:::vault

    classDef cmd    fill:#1e1e2e,stroke:#89b4fa,color:#cdd6f4
    classDef file   fill:#1e1e2e,stroke:#a6e3a1,color:#cdd6f4
    classDef step   fill:#1e1e2e,stroke:#cba6f7,color:#cdd6f4
    classDef choice fill:#1e1e2e,stroke:#f9e2af,color:#cdd6f4
    classDef warn   fill:#1e1e2e,stroke:#fab387,color:#cdd6f4
    classDef vault  fill:#1e1e2e,stroke:#f38ba8,color:#cdd6f4
```

> No codebase scan. No investigator agents. Decisions already exist in the conversation.

---

## Ideation Canvas (realm-plan)

Single-intent invocation — routes to the matching agent, saves to `work/`:

```mermaid
flowchart TD
    PL(["/realm-plan &lt;intent&gt; &lt;topic&gt;"]):::cmd --> VC["pre-load vault context"]:::file
    VC --> IR{intent}:::choice

    IR -->|plan| AG1(["planner"]):::agent
    IR -->|design| AG2(["architect"]):::agent
    IR -->|scaffold| AG3(["code-architect"]):::agent
    IR -->|investigate| AG4(["cavecrew-investigator"]):::agent
    IR -->|deep-research| AG5(["firecrawl + exa"]):::agent

    AG1 --> WP["work/plans/"]:::dir
    AG2 --> WD["work/designs/"]:::dir
    AG3 --> WS["work/scaffolds/"]:::dir
    AG4 --> WR["work/research/"]:::dir
    AG5 --> WR

    WP & WD & WS & WR --> FIN{finalize?}:::choice
    FIN -->|Yes| VN["vault nodes\ndecisions/ · systems/ · sessions/"]:::vault
    FIN -->|Decisions made| CV(["/realm-convey"]):::cmd
    FIN -->|No| RS["resumable\nacross sessions"]:::ok

    classDef cmd    fill:#1e1e2e,stroke:#89b4fa,color:#cdd6f4
    classDef file   fill:#1e1e2e,stroke:#a6e3a1,color:#cdd6f4
    classDef dir    fill:#1e1e2e,stroke:#89b4fa,color:#cdd6f4
    classDef choice fill:#1e1e2e,stroke:#f9e2af,color:#cdd6f4
    classDef agent  fill:#1e1e2e,stroke:#f9e2af,color:#cdd6f4
    classDef vault  fill:#1e1e2e,stroke:#f38ba8,color:#cdd6f4
    classDef ok     fill:#1e1e2e,stroke:#a6e3a1,color:#cdd6f4
```

Chain syntax — generation order hint, not a hard pipeline:

```mermaid
flowchart LR
    CH(["/realm-plan A->B->C &lt;topic&gt;"]):::cmd --> S1["stage A\ne.g. deep-research"]:::stage
    S1 -->|"output feeds next"| S2["stage B\ne.g. design"]:::stage
    S2 -->|"output feeds next"| S3["stage C\ne.g. plan"]:::stage
    S3 --> WK["work/&lt;category&gt;/\n&lt;canvas&gt;.md"]:::file

    classDef cmd   fill:#1e1e2e,stroke:#89b4fa,color:#cdd6f4
    classDef stage fill:#1e1e2e,stroke:#f9e2af,color:#cdd6f4
    classDef file  fill:#1e1e2e,stroke:#a6e3a1,color:#cdd6f4
```

---

## Queries

Read-only skills — no pipeline state required:

```mermaid
flowchart LR
    Q1(["/realm-recall &lt;query&gt;"]):::cmd  --> R["compressed ADR context\nwhy · rejected · constraints"]:::out
    Q2(["/realm-status"]):::cmd             --> S["read-only\nhealth check"]:::out
    Q3(["/realm-fathom &lt;entity|question&gt;"]):::cmd --> F["live code ＋ vault\nconsolidated report"]:::out

    classDef cmd fill:#1e1e2e,stroke:#89b4fa,color:#cdd6f4
    classDef out fill:#1e1e2e,stroke:#cba6f7,color:#cdd6f4
```

### Fathom investigation flow

```mermaid
flowchart TD
    FT(["/realm-fathom &lt;query&gt;"]):::cmd --> GV{vault\ninitialized?}

    GV -->|Yes| PAR["spawn parallel"]:::note
    GV -->|No| CI2(["cavecrew-investigator"]):::agent

    PAR --> CI(["cavecrew-investigator\n(live code — ground truth)"]):::agent
    PAR --> RQ(["realm-agent-query\n(vault context)"]):::agent

    CI  --> CO["code findings\nsignature · flow · callers"]:::out
    RQ  --> VO["vault context\nwhy · rejected · consequences"]:::out
    CI2 --> CO

    CO --> DR{drift\ndetected?}
    VO --> DR

    DR -->|Yes| DW["VAULT DRIFT flagged\nboth values shown"]:::warn
    DR -->|No| VD["VERDICT\nwhat + why + caveats"]:::out
    DW --> VD

    classDef cmd   fill:#1e1e2e,stroke:#89b4fa,color:#cdd6f4
    classDef agent fill:#1e1e2e,stroke:#f9e2af,color:#cdd6f4
    classDef out   fill:#1e1e2e,stroke:#cba6f7,color:#cdd6f4
    classDef note  fill:#1e1e2e,stroke:#a6e3a1,color:#cdd6f4
    classDef warn  fill:#1e1e2e,stroke:#f38ba8,color:#cdd6f4
```

---

## Vault Structure

```mermaid
graph TD
    ROOT["&lt;vault&gt;/projects/&lt;slug&gt;/"]:::dir

    ROOT --> OV["overview.md\n─ milestone tracker, stack, key files"]:::node
    ROOT --> AR["architecture.md\n─ service map, event shapes, schema groups"]:::node
    ROOT --> DE["decisions/\n─ ADRs — context, decision, rejected, consequences"]:::dir
    ROOT --> DI["discoveries/\n─ perf notes, bug findings, unexpected constraints"]:::dir
    ROOT --> SE["sessions/\n─ per-session decision logs"]:::dir
    ROOT --> WK["work/\n─ in-progress realm-plan canvases"]:::dir

    classDef dir  fill:#1e1e2e,stroke:#89b4fa,color:#cdd6f4
    classDef node fill:#1e1e2e,stroke:#a6e3a1,color:#cdd6f4
```

---

## Local Pipeline State (.realm/)

```mermaid
graph LR
    ROOT[".realm/"]:::dir
    ROOT --> RS["realm-state.json\n─ doc registry + pipeline state"]:::node
    ROOT --> MD["manifest-draft.md\n─ staged draft (convey → manifest)"]:::node
    ROOT --> AR["archive/\n─ past drafts after each manifest run"]:::dir

    classDef dir  fill:#1e1e2e,stroke:#89b4fa,color:#cdd6f4
    classDef node fill:#1e1e2e,stroke:#a6e3a1,color:#cdd6f4
```

`.realm/` is added to `.gitignore` by realm-forge. Local state, not repo state.

---

## Guards

Prerequisite checks enforced by each skill:

```mermaid
flowchart LR
    CV(["/realm-convey"]):::cmd -->|requires| RS["realm-state.json\nexists?"]
    RS -->|No| RI(["/realm-forge"]):::warn
    CV -->|blocks on| USR["user item\nselection"]

    M(["/realm-manifest"]):::cmd -->|requires| DR["phase.draftReady\n== true?"]
    DR -->|No| RC(["/realm-convey"]):::warn

    FT(["/realm-fathom"]):::cmd -->|soft guard| RS3["realm-state.json\nexists?"]
    RS3 -->|No| CO["proceeds code-only\nnote vault unavailable"]:::ok

    classDef cmd  fill:#1e1e2e,stroke:#89b4fa,color:#cdd6f4
    classDef warn fill:#1e1e2e,stroke:#fab387,color:#cdd6f4
    classDef ok   fill:#1e1e2e,stroke:#a6e3a1,color:#cdd6f4
```
