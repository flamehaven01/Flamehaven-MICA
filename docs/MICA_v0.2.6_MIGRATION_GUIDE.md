# v0.2.5 -> v0.2.6 Migration Guide

## Overview

v0.2.6 is non-breaking. Packages that do not set `di_policy.critical_binding_required: true`
behave identically to v0.2.5.

Migration has two paths:

- **Minimal**: replace tool files only. Existing packages see no behavior change.
- **Enforcement**: opt in per package by adding `di_policy` to mica.yaml.

---

## What changes

| File | Action |
|------|--------|
| `tools/mica_core.py` | Replace with v0.2.6 version |
| `tools/mica_pct.py` | Replace with v0.2.6 version |
| `tools/mica_runtime.py` | Replace with v0.2.6 version |
| `mica.yaml` | Optional: add `di_policy.critical_binding_required: true` to enforce binding |
| Archive JSON | Optional: bump `mica_spec` to `"0.2.6"` |

---

## Minimal migration (tool replacement only)

### Step 1 — copy tools

```
tools/mica_core.py      <- replace v0.2.5 version
tools/mica_pct.py       <- replace v0.2.5 version
tools/mica_runtime.py   <- replace v0.2.5 version
```

All three must be in the same directory.

### Step 2 — validate

```bash
python tools/mica_pct.py .
```

Expected: same CLOSED CONTRACT result as before.
PCT-010 WARN behavior is unchanged when `di_policy` is absent.

---

## Enforcement migration (opt-in binding gate)

### Step 1 — replace tools (same as minimal)

### Step 2 — add di_policy to mica.yaml

```yaml
di_policy:
  critical_binding_required: true
```

Add after the `mode:` field.

### Step 3 — run PCT check

```bash
python tools/mica_pct.py .
```

If any critical DIs lack `binding.origin_episode`, PCT-010 will now FAIL.
The validator output names which DIs need binding.

### Step 4 — bind critical DIs

For each FAIL DI, add a `binding` block to the archive JSON:

```json
{
  "id": "DI-001",
  "severity": "critical",
  "binding": {
    "origin_episode": "EXP-001: describe the incident that motivated this invariant",
    "violation_count": 0,
    "lesson_ref": "",
    "last_triggered": ""
  }
}
```

`origin_episode` must be non-empty (minimum 10 characters).

### Step 5 — re-validate

```bash
python tools/mica_pct.py .
```

Expected: PCT-010 PASS, CLOSED CONTRACT.

---

## WARN message change

The PCT-010 WARN message changed in v0.2.6:

- v0.2.5: `-- escalates to FAIL when binding_required: true is set (planned v0.2.6)`
- v0.2.6: `-- set di_policy.critical_binding_required: true to escalate to FAIL`

If you have documentation or tests matching the old WARN text, update them.

---

## CI setup (new in v0.2.6)

If you are migrating to the repo-based MICA distribution:

```bash
pip install -r requirements-dev.txt
pytest -v
ruff check tools/ tests/
```

---

## Checklist

- [ ] `tools/mica_core.py` replaced
- [ ] `tools/mica_pct.py` replaced
- [ ] `tools/mica_runtime.py` replaced
- [ ] `python tools/mica_pct.py .` returns expected result
- [ ] (If opting in) `di_policy.critical_binding_required: true` in mica.yaml
- [ ] (If opting in) All critical DIs have `binding.origin_episode`
- [ ] (If opting in) `python tools/mica_pct.py .` returns CLOSED CONTRACT
