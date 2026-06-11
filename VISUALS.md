# Realm — Visual Reference

Pipeline flows, vault structure, and guard logic for [Realm](README.md).

---

## Table of Contents

- [Core Pipeline](#core-pipeline)
- [Incremental Update](#incremental-update)
- [Conversation Capture](#conversation-capture)
- [Queries](#queries)
- [Vault Structure](#vault-structure)
- [Local Pipeline State (.realm/)](#local-pipeline-state-realm)
- [Guards](#guards)

---

## Core Pipeline

Full pipeline from bootstrap to vault:

```mermaid
flowchart TD
    A(["/realm-forge"]):::cmd -->|"bootstrap vault dirs + realm-state.json"| B

    B(["/realm-phase"]):::cmd -->|"scan repo → compress → diff vs vault"| C1
    C1[".realm/manifest-draft.md"]:::file -->|"review draft"| C

    C(["/realm-manifest"]):::cmd -->|"write + link nodes → archive draft"| V

    V[("Obsidian Vault")]:::vault

    classDef cmd   fill:#1e1e2e,stroke:#89b4fa,color:#cdd6f4,rx:6
    classDef file  fill:#1e1e2e,stroke:#a6e3a1,color:#cdd6f4,rx:4
    classDef vault fill:#1e1e2e,stroke:#f38ba8,color:#cdd6f4,rx:8
```

> No vault writes at phase time — review the draft before committing.

---

## Incremental Update

Quick sync after small code changes:

```mermaid
flowchart LR
    RF(["/realm-flourish"]):::cmd -->|"git diff + targeted scan"| D{structural\ndecision?}
    D -->|No| AC["auto-commit\nminor changes"]:::ok
    D -->|Yes| SM["fall back to\nstaged mode"]:::warn

    classDef cmd  fill:#1e1e2e,stroke:#89b4fa,color:#cdd6f4
    classDef ok   fill:#1e1e2e,stroke:#a6e3a1,color:#cdd6f4
    classDef warn fill:#1e1e2e,stroke:#fab387,color:#cdd6f4
```

---

## Conversation Capture

Compress a conversation and route selected topics to the vault:

```mermaid
flowchart TD
    CV(["/realm-convey"]):::cmd -->|"compress + dissect conversation"| TL["topic list\nfunctions · classes · decisions · discoveries"]:::file
    TL -->|"user selects items"| SEL{selection}:::choice
    SEL -->|"entities chosen"| RP(["/realm-phase (targeted)"]):::cmd
    SEL -->|"decisions/discoveries only"| ST[".realm/manifest-draft.md\nstubs only"]:::file
    SEL -->|"none"| NO["no-op"]:::warn
    RP --> DR[".realm/manifest-draft.md"]:::file

    classDef cmd    fill:#1e1e2e,stroke:#89b4fa,color:#cdd6f4
    classDef file   fill:#1e1e2e,stroke:#a6e3a1,color:#cdd6f4
    classDef choice fill:#1e1e2e,stroke:#f9e2af,color:#cdd6f4
    classDef warn   fill:#1e1e2e,stroke:#fab387,color:#cdd6f4
```

---

## Queries

Read-only skills — no pipeline state required:

```mermaid
flowchart LR
    Q1(["/realm-recall &lt;topic&gt;"]):::cmd --> R["compressed context\nfrom vault"]:::out
    Q2(["/realm-status"]):::cmd            --> S["read-only\nhealth check"]:::out

    classDef cmd fill:#1e1e2e,stroke:#89b4fa,color:#cdd6f4
    classDef out fill:#1e1e2e,stroke:#cba6f7,color:#cdd6f4
```

---

## Vault Structure

```mermaid
graph TD
    ROOT["&lt;vault&gt;/projects/&lt;slug&gt;/"]:::dir

    ROOT --> OV["overview.md\n─ milestone tracker, stack, key files"]:::node
    ROOT --> AR["architecture.md\n─ service map, event shapes, schema groups"]:::node
    ROOT --> DE["decisions/\n─ ADRs — one node per decision"]:::dir
    ROOT --> FN["functions/\n─ critical functions — signature, deps, callers"]:::dir
    ROOT --> CL["classes/\n─ services/classes — methods, deps, dependents"]:::dir
    ROOT --> SY["systems/\n─ subsystems and integrations"]:::dir
    ROOT --> DI["discoveries/\n─ ephemeral findings, perf notes, bug post-mortems"]:::dir
    ROOT --> SE["sessions/\n─ per-session discovery logs"]:::dir

    classDef dir  fill:#1e1e2e,stroke:#89b4fa,color:#cdd6f4
    classDef node fill:#1e1e2e,stroke:#a6e3a1,color:#cdd6f4
```

---

## Local Pipeline State (.realm/)

```mermaid
graph LR
    ROOT[".realm/"]:::dir
    ROOT --> RS["realm-state.json\n─ doc registry + pipeline state"]:::node
    ROOT --> MD["manifest-draft.md\n─ staged draft (phase → manifest)"]:::node
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
    P(["/realm-phase"]):::cmd -->|requires| RS["realm-state.json\nexists?"]
    RS -->|No| RI(["/realm-forge"]):::warn

    M(["/realm-manifest"]):::cmd -->|requires| DR["phase.draftReady\n== true?"]
    DR -->|No| RP(["/realm-phase"]):::warn

    F(["/realm-flourish"]):::cmd -->|blocks if| SD["staged draft\npending?"]
    SD -->|Yes| CM["commit or\ndiscard first"]:::warn

    CV(["/realm-convey"]):::cmd -->|requires| RS2["realm-state.json\nexists?"]
    RS2 -->|No| RI2(["/realm-forge"]):::warn
    CV -->|blocks on| USR["user item\nselection"]

    classDef cmd  fill:#1e1e2e,stroke:#89b4fa,color:#cdd6f4
    classDef warn fill:#1e1e2e,stroke:#fab387,color:#cdd6f4
```
