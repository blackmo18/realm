# Realm — Visual Reference

Pipeline flows, vault structure, and guard logic for [Realm](README.md).

---

## Table of Contents

- [Core Pipeline](#core-pipeline)
- [Two-Phase Planning (realm-planning)](#two-phase-planning-realm-planning)
- [God-File Triage (realm-concise)](#god-file-triage-realm-concise)
- [Queries & Fathom Investigation](#queries--fathom-investigation)
- [Vault Structure](#vault-structure)
- [Local Pipeline State (.realm/)](#local-pipeline-state-realm)
- [Guards](#guards)

---

## Core Pipeline

Decision memory & knowledge flow from AI host to Obsidian vault:

```mermaid
flowchart TD
    A(["/realm-forge"]):::cmd -->|"bootstrap vault dirs + realm-state.json"| V[("Obsidian Vault\ndecisions/ · discoveries/ · sessions/")]:::vault

    F(["/realm-fathom"]):::cmd -->|"live code ＋ vault parallel read"| V
    R(["/realm-recall"]):::cmd -->|"compressed decision query"| V
    S(["/realm-status"]):::cmd -->|"health check & doc registry"| V

    P(["/realm-planning"]):::cmd -->|"two-phase plan & ADR commit"| V
    C(["/realm-concise"]):::cmd -->|"god-file triage → queue refactors"| P

    classDef cmd   fill:#1e1e2e,stroke:#89b4fa,color:#cdd6f4,rx:6
    classDef vault fill:#1e1e2e,stroke:#f38ba8,color:#cdd6f4,rx:8
```

---

## Two-Phase Planning (realm-planning)

Structured planning operating inside native plan mode:

```mermaid
flowchart TD
    PL(["/realm-planning &lt;topic&gt;"]):::cmd --> P1["Phase 1: High-Level Architecture & ADR Direction"]:::step
    P1 -->|"graphify / cavecrew-investigator search"| ARCH(["architect agent"]):::agent
    ARCH --> P1OUT["Phase 1 Plan Output"]:::file

    P1OUT --> CD{Contract Delta?}:::choice
    CD -->|Yes| WC["write contract\ncontracts/&lt;slug&gt;-api-contracts.md"]:::file
    CD -->|No| P2

    WC --> P2["Phase 2: Code-Level Implementation Blueprint"]:::step
    P2 --> CARCH(["code-architect agent"]):::agent
    CARCH --> P2OUT["Phase 2 Implementation Blueprint"]:::file

    P2OUT --> ADR["write adr\ndecisions/ADR-NNN.md"]:::vault

    classDef cmd    fill:#1e1e2e,stroke:#89b4fa,color:#cdd6f4
    classDef file   fill:#1e1e2e,stroke:#a6e3a1,color:#cdd6f4
    classDef step   fill:#1e1e2e,stroke:#cba6f7,color:#cdd6f4
    classDef choice fill:#1e1e2e,stroke:#f9e2af,color:#cdd6f4
    classDef agent  fill:#1e1e2e,stroke:#f9e2af,color:#cdd6f4
    classDef vault  fill:#1e1e2e,stroke:#f38ba8,color:#cdd6f4
```

---

## God-File Triage (realm-concise)

Deterministic crawler finds oversized files, scores blast radius, and manages queue:

```mermaid
flowchart TD
    CS(["/realm-concise"]):::cmd --> PY["scripts/concise.py\n(LOC count · blast radius · churn)"]:::step
    PY --> ST[".realm/concise-state.json\n(script-owned queue)"]:::file
    PY --> LD["docs/GOD_FILES.md\n(committed ledger)"]:::file

    ST --> REC["/realm-concise recommend &lt;file&gt;"]:::cmd
    REC -->|"user confirms approve"| APP["Queue Status: Approved"]:::ok
    APP -->|"user confirms plan"| PLAN["/realm-planning &lt;topic&gt;"]:::cmd

    classDef cmd  fill:#1e1e2e,stroke:#89b4fa,color:#cdd6f4
    classDef step fill:#1e1e2e,stroke:#cba6f7,color:#cdd6f4
    classDef file fill:#1e1e2e,stroke:#a6e3a1,color:#cdd6f4
    classDef ok   fill:#1e1e2e,stroke:#a6e3a1,color:#cdd6f4
```

---

## Queries & Fathom Investigation

Read-only skills — no state mutation required:

```mermaid
flowchart LR
    Q1(["/realm-recall &lt;query&gt;"]):::cmd  --> R["compressed ADR context\nwhy · rejected · constraints"]:::out
    Q2(["/realm-status"]):::cmd             --> S["read-only\nhealth check"]:::out
    Q3(["/realm-fathom &lt;entity|question&gt;"]):::cmd --> F["live code ＋ vault\nconsolidated report"]:::out

    classDef cmd fill:#1e1e2e,stroke:#89b4fa,color:#cdd6f4
    classDef out fill:#1e1e2e,stroke:#cba6f7,color:#cdd6f4
```

### Fathom Investigation Flow

```mermaid
flowchart TD
    FT(["/realm-fathom &lt;query&gt;"]):::cmd --> GV{vault\ninitialized?}

    GV -->|Yes| PAR["parallel read"]:::note
    GV -->|No| CI2(["cavecrew-investigator"]):::agent

    PAR --> CI(["graphify / cavecrew-investigator\n(live code — ground truth)"]):::agent
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
    ROOT --> WK["work/\n─ in-progress planning canvases"]:::dir

    classDef dir  fill:#1e1e2e,stroke:#89b4fa,color:#cdd6f4
    classDef node fill:#1e1e2e,stroke:#a6e3a1,color:#cdd6f4
```

---

## Local Pipeline State (.realm/)

```mermaid
graph LR
    ROOT[".realm/"]:::dir
    ROOT --> RS["realm-state.json\n─ doc registry + pipeline state"]:::node
    ROOT --> CS["concise-state.json\n─ god-file triage queue"]:::node
    ROOT --> AR["archive/\n─ past state snapshots"]:::dir

    classDef dir  fill:#1e1e2e,stroke:#89b4fa,color:#cdd6f4
    classDef node fill:#1e1e2e,stroke:#a6e3a1,color:#cdd6f4
```

`.realm/` is added to `.gitignore` by `realm-forge`. Local state, not repo state.

---

## Guards

Prerequisite checks enforced by each skill:

```mermaid
flowchart LR
    REC(["/realm-recall"]):::cmd -->|requires| RS["realm-state.json\nexists?"]
    RS -->|No| RI(["/realm-forge"]):::warn

    PL(["/realm-planning"]):::cmd -->|requires| RS2["realm-state.json\nexists?"]
    RS2 -->|No| RI2(["/realm-forge"]):::warn

    FT(["/realm-fathom"]):::cmd -->|soft guard| RS3["realm-state.json\nexists?"]
    RS3 -->|No| CO["proceeds code-only\nnote vault unavailable"]:::ok

    classDef cmd  fill:#1e1e2e,stroke:#89b4fa,color:#cdd6f4
    classDef warn fill:#1e1e2e,stroke:#fab387,color:#cdd6f4
    classDef ok   fill:#1e1e2e,stroke:#a6e3a1,color:#cdd6f4
```
