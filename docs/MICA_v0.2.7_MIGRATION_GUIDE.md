# v0.2.6 -> v0.2.7 Migration Guide

## Overview

v0.2.7 is non-breaking. Packages that do not use domain-namespaced DI IDs and
do not set `di_policy.namespace_mode` see no behavior change.

Migration has three paths:

- **Minimal**: update tool docstrings only. No format changes.
- **Namespace declaration**: add `di_policy.namespace_mode` to mica.yaml.
- **Schema migration**: upgrade from v0.2.4 DI binding schema to v0.2.7.

---

## What changes

| File | Action |
|---|---|
| `tools/mica_core.py` | Replace with v0.2.7 version (docstring only) |
| `tools/mica_pct.py` | Replace with v0.2.7 version (docstring only) |
| `tools/mica_runtime.py` | Replace with v0.2.7 version (docstring only) |
| `mica.yaml` | Optional: add `di_policy.namespace_mode` |
| Archive JSON | Optional: bump `mica_spec` to `"0.2.7"` |
| DI binding schema ref | Optional: update to `mica-v0.2.7-archive-di-binding.schema.json` |

---

## Minimal migration (tool replacement only)

### Step 1 — copy tools

```
tools/mica_core.py      <- replace v0.2.6 version
tools/mica_pct.py       <- replace v0.2.6 version
tools/mica_runtime.py   <- replace v0.2.6 version
```

### Step 2 — validate

```bash
python tools/mica_pct.py .
```

Expected: same CLOSED CONTRACT result as before.

---

## Namespace declaration migration

If your archive uses domain-namespaced DI IDs (e.g., `DI-EQA-001`, `DI-BIO-003`):

### Step 1 — add namespace_mode to mica.yaml

```yaml
di_policy:
  namespace_mode: domain_namespaced
```

If using the grandfathered `INV-xxx` prefix:

```yaml
di_policy:
  namespace_mode: legacy_inv
```

### Step 2 — validate

```bash
python tools/mica_pct.py .
```

No PCT behavior change — this is a declaration for governance and tooling consumers.

---

## COMPACT_MODE declaration

If your archive intentionally operates without mica.yaml:

No code changes required. Optionally declare intent in the archive JSON:

```json
{
  "project": {
    "status": "active",
    "purpose": "Intentional COMPACT_MODE deployment. No mica.yaml. pct=LEGACY is expected."
  }
}
```

`pct=LEGACY` remains the correct terminal state.

---

## Schema upgrade: v0.2.4 -> v0.2.7 DI binding schema

The v0.2.7 schema (`mica-v0.2.7-archive-di-binding.schema.json`) accepts all IDs
that v0.2.4 accepted, plus domain-namespaced and `INV-` forms.

If your archive has a `$schema` reference to the v0.2.4 file, update it:

```json
{
  "$schema": "flamehaven/mica/mica-v0.2.7-archive-di-binding.schema.json"
}
```

All existing `DI-NNN` IDs remain valid under the new pattern. No DI renames required.

---

## Checklist

- [ ] `tools/mica_core.py` replaced
- [ ] `tools/mica_pct.py` replaced
- [ ] `tools/mica_runtime.py` replaced
- [ ] `python tools/mica_pct.py .` returns expected result
- [ ] (If domain-namespaced) `di_policy.namespace_mode: domain_namespaced` in mica.yaml
- [ ] (If legacy INV-) `di_policy.namespace_mode: legacy_inv` in mica.yaml
- [ ] (If COMPACT deployment) `project.purpose` notes intentional no-mica.yaml
