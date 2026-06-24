# MICA Fixtures

Minimal test packages for validating PCT behavior and runtime output.
Each fixture is a self-contained project root. Run tools against them directly.

## Usage

```bash
python tools/mica_pct.py fixtures/valid_bound_di
python tools/mica_pct.py fixtures/unbound_critical_di
python tools/mica_pct.py fixtures/dead_lesson_ref
python tools/mica_pct.py fixtures/binding_required_fail
python tools/mica_pct.py fixtures/compact_mode
python tools/mica_pct.py fixtures/domain_namespaced_di
python tools/mica_pct.py fixtures/doctrinal_binding
python tools/mica_pct.py fixtures/stale_archive
python tools/mica_pct.py fixtures/violation_count_incoherent
python tools/mica_runtime.py fixtures/hook_output_violations_only --format hook
```

## Fixture Map

| Fixture | Version | PCT-010 | PCT-011 | PCT-012 | Contract | Notes |
|---|---|---|---|---|---|---|
| `valid_bound_di/` | v0.2.5 | PASS | INFO | INFO | CLOSED | All critical DIs have real binding |
| `unbound_critical_di/` | v0.2.5 | WARN | INFO | INFO | CLOSED | Critical DI lacks binding; no `critical_binding_required` |
| `dead_lesson_ref/` | v0.2.5 | PASS | WARN | INFO | CLOSED | `lesson_ref` declared but file missing |
| `hook_output_violations_only/` | v0.2.5 | WARN | INFO | INFO | CLOSED | Hook output filter demo |
| `binding_required_fail/` | v0.2.6 | FAIL | INFO | INFO | INCOMPLETE | `critical_binding_required=true` + unbound DI |
| `compact_mode/` | v0.2.7 | — | — | — | LEGACY | No mica.yaml; PCT-001 FAIL expected |
| `domain_namespaced_di/` | v0.2.7 | PASS | INFO | INFO | CLOSED | DI-EQA-xxx/DI-BIO-xxx + `critical_binding_required` |
| `doctrinal_binding/` | v0.2.8 | PASS+WARN | INFO | INFO | CLOSED | Bound but doctrinal origin_episode |
| `stale_archive/` | v0.2.8 | INFO | INFO | WARN | CLOSED | `max_archive_age_days=90`, last_updated=2020-01-01 |
| `violation_count_incoherent/` | v0.2.8 | PASS+WARN | INFO | INFO | CLOSED | `violation_count=3` + empty `last_triggered` |

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

### dead_lesson_ref

```
PCT-010 [PASS] all 1 critical DIs have binding
PCT-011 [WARN] binding.lesson_ref dead links: [('DI-001', 'memory/lessons/missing.md')]
Overall: CLOSED CONTRACT
```

### binding_required_fail

```
PCT-010 [FAIL] critical DIs missing binding.origin_episode: ['DI-001']
              -- di_policy.critical_binding_required is true
Overall: INCOMPLETE CONTRACT
```

### compact_mode

```
PCT-001 [FAIL] mica.yaml missing (checked root + memory/)
PCT-009 [FAIL] package incomplete. failing checks: ['PCT-001']
Overall: (LEGACY — no mica.yaml, intentional COMPACT deployment)
```

### domain_namespaced_di

```
PCT-010 [PASS] all 3 critical DIs have binding
Overall: CLOSED CONTRACT
```

### doctrinal_binding (v0.2.8)

```
PCT-010 [PASS] all 2 critical DIs have binding
PCT-010 [WARN] doctrinal binding (no episode code, version ref, or date): ['DI-001', 'DI-002']
              -- ground origin_episode in a real incident
Overall: CLOSED CONTRACT
```

### stale_archive (v0.2.8)

```
PCT-012 [WARN] archive last_updated 2020-01-01 is NNNN days old (max_archive_age_days=90)
Overall: CLOSED CONTRACT
```

### violation_count_incoherent (v0.2.8)

```
PCT-010 [PASS] all 1 critical DIs have binding
PCT-010 [WARN] violation_count > 0 but last_triggered empty: ['DI-001']
Overall: CLOSED CONTRACT
```

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
