# realm-plan

Free-form ideation canvas — think, research, design, and plan inside a persistent workspace. Saves to vault across sessions. Finalizes to real vault nodes when ready.

---

## Syntax

```bash
# Single section
/realm-plan plan "refactor auth to JWT"
/realm-plan design "API versioning strategy"
/realm-plan scaffold "NotificationService"
/realm-plan investigate "caching bug"
/realm-plan deep-research "event sourcing tradeoffs"

# Chain — generation order hint, not a hard pipeline
/realm-plan deep-research->design->plan "auth refactor"
/realm-plan investigate->plan "caching bug"
/realm-plan scaffold->design->plan "PaymentService"
/realm-plan research->design "new queue architecture"

# Session management
/realm-plan list                              # all in-progress work
/realm-plan list plans                        # filter by category
/realm-plan resume plans/auth-refactor        # continue saved canvas
/realm-plan resume plans/auth-refactor design # resume, jump to section

# Flags
/realm-plan design --ui "onboarding flow"     # adds a11y considerations
/realm-plan plan --feature "notifications"    # scope to feature
```

---

## How It Works

Chain syntax defines which agents run and in what order to populate sections. That is all — not a hard pipeline. After generation, one free-form loop opens on the full canvas. No stage gates. No forced accepts.

```
/realm-plan deep-research->design->plan "auth refactor"
  │
  ├─ vault pre-load (realm-agent-query)
  ├─ deep-research → research section
  ├─ design (sees research) → design section
  ├─ plan (sees research + design) → plan section
  │
  └─ ONE free-form loop — user drives
       update any section, add sections, skip sections
       save → persists, stays in loop
       finalize → promotes to vault nodes
```

---

## Section Modes

| Mode | Agent | Output |
|------|-------|--------|
| `plan` | `planner` | Goals, risks, phases, open decisions |
| `design` | `architect` | Options, recommendation, consequences, ADR stub |
| `scaffold` | `code-architect` | Boundary, interface, data shapes, file list, build order |
| `investigate` | `cavecrew-investigator` | file:line map, call chains, vault drift — local codebase |
| `deep-research` / `research` | ECC deep-research (firecrawl + exa) | Findings, sources, implications — external web/docs |

---

## Vault Persistence

Work items persist in vault under `work/`, categorized by intent:

```
vault/projects/<slug>/work/
├── index.md          ← auto-maintained master list
├── plans/            ← building something (terminal mode: plan)
├── designs/          ← deciding / architecting (terminal mode: design)
├── research/         ← learning / investigating (terminal mode: research or investigate)
└── scaffolds/        ← blueprinting modules (terminal mode: scaffold)
    └── <slug>/
        ├── _meta.md  ← category, chain, status, section registry
        └── *.md      ← one file per section
```

Category is assigned automatically from the terminal (last) mode in the chain:
- `research->design->plan` → `plans/`
- `research->design` → `designs/`
- standalone `investigate` → `research/`

Slug = kebab-case from topic, no date prefix. Date lives in `_meta.md`.

---

## Loop Commands

| Command | Effect |
|---------|--------|
| `update: <section> — <feedback>` | Re-run section agent with feedback |
| `add section: <mode>` | Generate new section, append to canvas |
| `skip: <section>` | Mark skipped, remove from display |
| `dig deeper: <section>` | Expand section inline |
| `alternatives: <section>` | Generate alternative approaches |
| `re-run: <section>` | Regenerate section from scratch |
| `add: <constraint>` | Incorporate into relevant sections |
| `show <section>` / `show all` | Print section or full canvas |
| `save` | Persist to vault, stay in loop |
| `finalize` | Promote sections to vault nodes → `/realm-manifest` |
| `discard` | Delete work item. Vault unchanged. |

---

## Finalize → Vault

On `finalize`, sections are classified by content and promoted:

| Category | Primary vault destination |
|---|---|
| `plans/` | `sessions/` (task block) + extracted `decisions/` |
| `designs/` | `decisions/` (ADR) + `architecture.md` update |
| `research/` | `discoveries/` |
| `scaffolds/` | `classes/` + `systems/` stubs |

Writes `manifest-draft.md` → run `/realm-manifest` to commit to vault.

---

## Recall

```bash
/realm-recall work:plans/auth-refactor          # full canvas
/realm-recall work:designs/api-versioning design # just design section
/realm-recall "auth design"                      # searches work/ + decisions/ + systems/
```
