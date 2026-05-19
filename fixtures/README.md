# MICA v0.2.6 Fixtures

Minimal test packages for validating PCT behavior and runtime output.
Each fixture is a self-contained project root. Run tools against them directly.

## Usage

```bash
python tools/mica_pct.py fixtures/valid_bound_di
python tools/mica_pct.py fixtures/unbound_critical_di
python tools/mica_pct.py fixtures/dead_lesson_ref
python tools/mica_pct.py fixtures/binding_required_fail
python tools/mica_runtime.py fixtures/hook_output_violations_only --format hook
```

## Fixture Map

| Fixture | Expected PCT-010 | Expected PCT-011 | Notes |
|---------|-----------------|-----------------|-------|
| `valid_bound_di/` | PASS | INFO | All critical DIs have origin_episode; no lesson_ref declared |
| `unbound_critical_di/` | WARN | INFO | Critical DI lacks binding; CLOSED CONTRACT preserved |
| `dead_lesson_ref/` | PASS | WARN | lesson_ref declared but file missing |
| `hook_output_violations_only/` | WARN | INFO | Hook output demo: violations_only filter + max_di_lines |
| `binding_required_fail/` | FAIL | INFO | v0.2.6: di_policy.critical_binding_required=true breaks contract |

## Expected Outputs

### valid_bound_di

```
PCT-010 [PASS] all 2 critical DIs have binding
PCT-011 [INFO] no lesson_ref fields declared; nothing to validate
Overall: CLOSED CONTRACT
```

### unbound_critical_di

```
PCT-010 [WARN] critical DIs missing binding.origin_episode: ['DI-001']
              -- set di_policy.critical_binding_required: true to escalate to FAIL
PCT-011 [INFO] no lesson_ref fields declared; nothing to validate
Overall: CLOSED CONTRACT
```

CLOSED CONTRACT is preserved. PCT-010 WARN is a maturity indicator, not a hard fail.

### dead_lesson_ref

```
PCT-010 [PASS] all 1 critical DIs have binding
PCT-011 [WARN] binding.lesson_ref dead links: [('DI-001', 'memory/lessons/missing.md')]
Overall: CLOSED CONTRACT
```

PCT-011 WARN does not break CLOSED CONTRACT. Fix: create the lesson file or remove lesson_ref.

### hook_output_violations_only

```bash
python tools/mica_runtime.py fixtures/hook_output_violations_only --format hook
```

Expected output (3 critical DIs, only 2 have violation_count > 0, max_di_lines: 2):

```
[MICA] hook-output-test v1.0.0 | mode=memory_injection | pattern=readme_protocol | DI=3crit/0high | pct=CLOSED | last=2026-05-19
[MICA:DI] DI-001(critical): first-violated-di [3x]
[MICA:DI] DI-002(critical): second-violated-di [1x]
```

DI-003 is suppressed (no violation_count). Cap of 2 is reached after DI-002.
