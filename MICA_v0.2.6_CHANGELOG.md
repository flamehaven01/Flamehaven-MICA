# MICA v0.2.6 Changelog

## Release: Binding Enforcement Edition

v0.2.6 adds one behavioral change: PCT-010 can now escalate from WARN to FAIL.
All other behavior is preserved. No spec format changes.

---

## Changes

### tools/mica_core.py

| Change | Detail |
|--------|--------|
| `HARD_FAIL_CHECKS` | Added `PCT-010` |
| `run_pct_checks()` | Reads `di_policy.critical_binding_required` from mica.yaml |
| PCT-010 branch | FAIL when `critical_binding_required=True` and unbound DIs exist; WARN otherwise |
| Docstring | v0.2.6 escalation note added |
| WARN message | Updated: no longer references "planned v0.2.6" |

### tools/mica_pct.py

| Change | Detail |
|--------|--------|
| Version string | Updated to v0.2.6 |
| Docstring | v0.2.6 escalation note added |

### tools/mica_runtime.py

| Change | Detail |
|--------|--------|
| Version string | Updated to v0.2.6 |
| Docstring | v0.2.6 note: no runtime.py changes needed (pct_status already delegates) |

### mica.yaml.schema.json

| Change | Detail |
|--------|--------|
| `di_policy` block | New optional object with `critical_binding_required` boolean |

### fixtures/

| Change | Detail |
|--------|--------|
| `binding_required_fail/` | New fixture: PCT-010 FAIL scenario |
| `fixtures/README.md` | Added binding_required_fail entry and expected output |
| `unbound_critical_di` WARN text | Updated to match new message (no longer says "planned v0.2.6") |

### CI / tooling

| Change | Detail |
|--------|--------|
| `.github/workflows/ci.yml` | New: runs pytest + ruff on push and PR (Python 3.9, 3.11, 3.12) |
| `tests/test_pct_fixtures.py` | New: 5 fixture-based pytest tests |
| `pyproject.toml` | New: ruff and pytest configuration |
| `requirements-dev.txt` | New: pytest, ruff, pyyaml versions |

---

## What did NOT change

- `mica.yaml` format
- Archive JSON format
- DI binding schema
- PCT-001 through PCT-009 behavior
- PCT-011 behavior
- CLOSED CONTRACT definition (when `critical_binding_required` is absent or false)
- All profiles, templates (except bootstrap version bump), and carry-forward spec docs
