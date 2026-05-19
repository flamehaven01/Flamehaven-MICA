# MICA v0.2.5 -> v0.2.6 Comparison

## Summary

v0.2.5 and v0.2.6 share the same spec format. The difference is in tooling and enforcement.

- v0.2.5 closed the runtime coherence gap (pct_status() vs mica_pct.py agreement)
- v0.2.6 closes the binding enforcement gap (PCT-010 WARN -> FAIL opt-in)

No mica.yaml or archive format changes. Migration is tool-only for the minimal path.

---

## Comparison Table

| Area | v0.2.5 | v0.2.6 | Judgment |
|------|--------|--------|----------|
| PCT-010 enforcement | WARN only; no hard gate | FAIL when `critical_binding_required: true` | v0.2.6 better |
| Backward compatibility | Full | Full (opt-in flag; absent = v0.2.5 behavior) | Same |
| HARD_FAIL_CHECKS | PCT-001,002,003,004,007,008 | + PCT-010 | v0.2.6 adds PCT-010 |
| PCT-010 WARN | "planned v0.2.6" in message | "set di_policy... to escalate to FAIL" | v0.2.6 accurate |
| CI coverage | None | pytest (5 tests) + ruff + GitHub Actions | v0.2.6 better |
| Fixture coverage | 4 fixtures | 5 fixtures (+ binding_required_fail) | v0.2.6 better |
| mica.yaml schema | No di_policy | `di_policy.critical_binding_required` added | v0.2.6 extends |
| Spec format | Defined | Unchanged | Same |
| Archive format | Unchanged | Unchanged | Same |
| DI binding schema | Unchanged | Unchanged | Same |

---

## Detailed Delta

### 1. PCT-010 Escalation

#### v0.2.5

PCT-010 always emitted WARN when critical DIs lacked `binding.origin_episode`.
CLOSED CONTRACT was preserved regardless. The WARN message said "planned v0.2.6":

```
PCT-010 [WARN] critical DIs missing binding.origin_episode: ['DI-001']
              -- escalates to FAIL when binding_required: true is set (planned v0.2.6)
```

#### v0.2.6

PCT-010 emits FAIL when `di_policy.critical_binding_required: true` is set in mica.yaml
and unbound critical DIs exist:

```
PCT-010 [FAIL] critical DIs missing binding.origin_episode: ['DI-001']
              -- di_policy.critical_binding_required is true
```

When the flag is absent or false, PCT-010 emits WARN (v0.2.5 behavior preserved):

```
PCT-010 [WARN] critical DIs missing binding.origin_episode: ['DI-001']
              -- set di_policy.critical_binding_required: true to escalate to FAIL
```

The implementation change in `run_pct_checks()`:

```python
# v0.2.5
elif unbound:
    results.append((
        "PCT-010", "WARN",
        f"critical DIs missing binding.origin_episode: {unbound}"
        f" -- escalates to FAIL when binding_required: true is set (planned v0.2.6)",
    ))

# v0.2.6
di_policy = yd.get("di_policy", {}) if isinstance(yd.get("di_policy"), dict) else {}
critical_binding_required = bool(di_policy.get("critical_binding_required", False))
# ...
elif unbound:
    if critical_binding_required:
        results.append(("PCT-010", "FAIL", f"... -- di_policy.critical_binding_required is true"))
    else:
        results.append(("PCT-010", "WARN", f"... -- set di_policy... to escalate to FAIL"))
```

### 2. HARD_FAIL_CHECKS

```python
# v0.2.5
HARD_FAIL_CHECKS = frozenset({"PCT-001", "PCT-002", "PCT-003", "PCT-004", "PCT-007", "PCT-008"})

# v0.2.6
HARD_FAIL_CHECKS = frozenset({"PCT-001", "PCT-002", "PCT-003", "PCT-004", "PCT-007", "PCT-008", "PCT-010"})
```

PCT-010 in HARD_FAIL_CHECKS only affects `is_closed_contract()` when PCT-010 emits FAIL.
When it emits WARN, the check has no effect on contract status.

### 3. CI and Testing

v0.2.5 shipped fixtures but no runner. v0.2.6 adds:

- `tests/test_pct_fixtures.py` — 5 tests, one per fixture
- `.github/workflows/ci.yml` — matrix: Python 3.9, 3.11, 3.12; steps: pytest + ruff
- `pyproject.toml` — ruff and pytest configuration
- `requirements-dev.txt` — pytest, ruff, pyyaml versions

### 4. New Fixture

`fixtures/binding_required_fail/` demonstrates the new FAIL path:
- mica.yaml sets `di_policy.critical_binding_required: true`
- DI-001 has no `binding.origin_episode`
- Expected: PCT-010 FAIL, PCT-009 FAIL, Overall INCOMPLETE

---

## What v0.2.5 got right that v0.2.6 preserves

- The runtime coherence fix (pct_status() and mica_pct.py always agree)
- The indentation-aware YAML fallback parser
- The shared mica_core.py architecture
- The "surface vs enforce" guard terminology
- All spec documents, profiles, and templates

v0.2.6 does not touch any of these.

---

## Final Comparison Judgment

v0.2.5 was the correct implementation of the spec.

v0.2.6 adds the enforcement option that v0.2.5 correctly deferred,
plus the CI foundation that makes future changes safe to ship.

If the goal is a standard where maintainers can opt into binding enforcement
and have CI catch regressions, v0.2.6 is the required successor.
