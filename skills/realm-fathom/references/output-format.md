# Fathom output

Omit the drift section when no conflict exists.

```text
FATHOM: <query>
sources: code:<status>(<graphify|investigator>) vault:<status> graphify:<status>

-- FLOW --
<signature, responsibility, flow, callers, errors, guards>

-- CONTEXT [vault] --
<rationale, ADRs, intent, invariants>

-- DRIFT --
<each code/vault conflict with both values>

-- VERDICT --
<what code does, why it exists, and critical caveats>
```

If code is missing, say it cannot be located. If vault state is missing, say Realm is not
initialized. If no vault node matches, say so without weakening the code findings.
