# v0.2.4 → v0.2.5 Migration Guide

## Overview

v0.2.5 is a tool-only migration. The spec (mica.yaml format, archive format,
DI binding structure) is unchanged. Only the tool files need to be replaced.

If you use `mica_pct.py` without `mica_runtime.py`, or vice versa, you can
migrate just one tool. They remain standalone scripts.

---

## What changes

| File | Action |
|------|--------|
| `tools/mica_core.py` | New — add to tools/ |
| `tools/mica_pct.py` | Replace with v0.2.5 version |
| `tools/mica_runtime.py` | Replace with v0.2.5 version |
| `mica.yaml` | No change required |
| Archive JSON | No change required |
| Playbook | No change required |

---

## Migration Procedure

### Step 1 — copy tools

Copy the three tool files from the v0.2.5 SDK into your project's `tools/` directory:

```
tools/mica_core.py      ← new file
tools/mica_pct.py       ← replaces v0.2.4 version
tools/mica_runtime.py   ← replaces v0.2.4 version
```

All three files must be in the same directory. `mica_pct.py` and `mica_runtime.py`
add their own directory to `sys.path` at startup so they can find `mica_core.py`.

### Step 2 — update mica_spec (recommended)

```yaml
# mica.yaml
mica_spec: "0.2.5"
```

```json
{
  "mica_spec": "0.2.5",
  "mica_schema_version": "0.2.5"
}
```

PCT-006 will WARN if mica.yaml and archive mica_spec differ. Updating both together
keeps the spec aligned.

### Step 3 — validate

```bash
python tools/mica_pct.py .
```

Expected: same CLOSED CONTRACT result as before (or better if prior pct_status()
was masking a real issue).

### Step 4 — verify hook output (if using hook_trigger)

```bash
python tools/mica_runtime.py . --format hook
```

Check the `pct=` field. If it changed from `CLOSED` to `INCOMPLETE`, the package
has a PCT issue that the v0.2.4 shallow check was hiding. Run `mica_pct.py` to
find which check is failing.

---

## pct= field change

The most common behavior change is in `pct=` in hook output.

Packages that were masking PCT issues under v0.2.4 will now report `pct=INCOMPLETE`.
This is the correct behavior. Investigate by running `mica_pct.py`.

Common causes:
- `mode: protocol_evolution` without a `lessons` layer (PCT-004 FAIL)
- `primary_pattern: hook_trigger` without `hook_script` (PCT-008 FAIL)
- `hook_script` path declared but file missing (PCT-008 FAIL)

---

## YAML parser change

If you relied on the fallback YAML parser (no PyYAML installed) and had
`invocation_protocol.hook_output` or multi-key `layers[]` items, the v0.2.4
parser silently dropped those fields. v0.2.5 parses them correctly.

If you now see different behavior from `mica_runtime.py --format hook` when
PyYAML is absent, it is because the v0.2.5 parser is reading `hook_output`
policy that v0.2.4 was ignoring.

---

## Checklist

- [ ] `tools/mica_core.py` added
- [ ] `tools/mica_pct.py` replaced
- [ ] `tools/mica_runtime.py` replaced
- [ ] `mica_spec: "0.2.5"` in `mica.yaml`
- [ ] `mica_spec: "0.2.5"` in archive JSON
- [ ] `python tools/mica_pct.py .` returns CLOSED CONTRACT
- [ ] `python tools/mica_runtime.py . --format hook` shows accurate `pct=` field
