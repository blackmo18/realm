# Step 5 — Output Format (caveman-compressed)

> Loaded only from realm-recall Step 5, after nodes are resolved and flags applied.

Apply caveman rules: drop articles/filler, use fragments, keep technical data exact. Omit empty fields.

**ADR node (single):**
```
<id> [decision·<status>] #tag1 #tag2
<one-liner from Compressed:>
decided: <decision field>
rejected: <rejected_alternatives field, compressed>
consequences: <consequences field, compressed>
[Full prose if --full]

## Canvas: <section>          ← only if source_plan present and intent matched
<section file content, caveman-compressed>
origin: <source_plan>
```

**Cluster:**
```
recall:<query> <N>nodes

1 decision:<id> #tags
  <one-liner>
  decided: <...>
  rejected: <...>

2 discovery:<id> #tags
  <one-liner>
...
→ <id> --full | <query> --deps | <query> --trace
```

**--trace:**
```
tree:<query>

<type>:<id>
├─related:[[A]][[B]]
└─related:[[C]]

~<N×20>t compressed. Obsidian graph for visual.
```

## Step 6 — Footer

```
recall done · <N>nodes · ~<estimated>t · mode:<compressed|full|trace>
[canvas: +<Nt> (<section> from <source_plan>)]   ← only if canvas expanded
→ /realm-recall <id> --full | --deps | --no-canvas | /realm-fathom <entity> for live+vault
```
