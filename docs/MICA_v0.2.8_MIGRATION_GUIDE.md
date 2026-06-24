# v0.2.7 -> v0.2.8 Migration Guide

## Overview

v0.2.8 is non-breaking. All changes are additive WARN signals. No existing packages
that pass v0.2.7 PCT will fail under v0.2.8 PCT.

Migration has two paths:

- **Minimal**: replace tool files. New PCT signals surface automatically.
- **Freshness opt-in**: add `di_policy.max_archive_age_days` to mica.yaml.

---

## What changes

| File | Action |
|---|---|
| `tools/mica_core.py` | Replace with v0.2.8 version |
| `tools/mica_pct.py` | Replace with v0.2.8 version (docstring only) |
| `tools/mica_runtime.py` | Replace with v0.2.8 version (docstring only) |
| `mica.yaml` | Optional: add `di_policy.max_archive_age_days` |
| Archive JSON | Optional: bump `mica_spec` to `"0.2.8"` |

---

## Minimal migration (tool replacement only)

### Step 1 — copy tools

```
tools/mica_core.py      <- replace v0.2.7 version
tools/mica_pct.py       <- replace v0.2.7 version
tools/mica_runtime.py   <- replace v0.2.7 version
```

### Step 2 — validate

```bash
python tools/mica_pct.py .
```

Expected: same CLOSED CONTRACT result as before, plus possible new WARNs:

- `PCT-006 [WARN]` if `mica_spec` is >= 2 versions behind `0.2.8`
- `PCT-010 [WARN]` if any critical DI's `origin_episode` has no episode code, version ref, or date
- `PCT-010 [WARN]` if any critical DI has `violation_count > 0` but empty `last_triggered`

None of these break CLOSED CONTRACT.

---

## Addressing doctrinal binding WARNs

If PCT-010 WARN fires for doctrinal binding on your critical DIs, the fix is to
ground the `origin_episode` in a real incident. At minimum, add:

- An episode code: `EXP-NNN: <description>` — preferred, most explicit
- A version reference: `v0.8.6: <description>`
- A date: `2026-04-07: <description>`

Example — before (doctrinal):
```json
"origin_episode": "Enforcement of data integrity to prevent financial risk."
```

Example — after (grounded):
```json
"origin_episode": "EXP-001: stub data returned on 2026-03-14 caused incorrect BUY signal on AAPL."
```

For DIs where no real violation has occurred yet, the WARN is expected — it signals
the binding has not been grounded yet. No action required until a real episode occurs.

---

## Fixing violation_count coherence WARNs

If a critical DI has `binding.violation_count > 0` but `binding.last_triggered` is empty:

```json
"binding": {
  "origin_episode": "EXP-001: ...",
  "violation_count": 3,
  "last_triggered": "2026-04-07"
}
```

Set `last_triggered` to the date of the most recent violation.

---

## Enabling archive freshness check (PCT-012)

Add to `mica.yaml`:

```yaml
di_policy:
  max_archive_age_days: 180
```

Recommended values:

| Context | Value |
|---|---|
| Active project (frequent sessions) | 90 |
| Maintenance mode | 180 |
| Stable / archived package | 365 |

Then ensure `operation_meta.last_updated` in your archive JSON is an ISO date:

```json
"operation_meta": {
  "last_updated": "2026-06-24"
}
```

Update `last_updated` each time the archive is meaningfully changed.

---

## Checklist

- [ ] `tools/mica_core.py` replaced
- [ ] `python tools/mica_pct.py .` returns expected result
- [ ] (If PCT-010 doctrinal WARN) `origin_episode` grounded with episode code, version, or date
- [ ] (If PCT-010 coherence WARN) `last_triggered` set for DIs with `violation_count > 0`
- [ ] (Optional) `di_policy.max_archive_age_days` added for PCT-012
- [ ] (Optional) `mica_spec` bumped to `"0.2.8"` in mica.yaml and archive
