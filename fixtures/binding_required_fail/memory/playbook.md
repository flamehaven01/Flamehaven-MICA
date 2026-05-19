# Binding Required Fail Fixture Playbook

Fixture for MICA v0.2.6 PCT-010 FAIL scenario.

## Expected PCT-010 behavior

When `di_policy.critical_binding_required: true` is set in mica.yaml
and DI-001 has no `binding.origin_episode`, PCT-010 reports FAIL
(not WARN). This breaks CLOSED CONTRACT.

Expected output from `python tools/mica_pct.py fixtures/binding_required_fail`:

```
PCT-010 [FAIL] critical DIs missing binding.origin_episode: ['DI-001'] -- di_policy.critical_binding_required is true
PCT-009 [FAIL] package incomplete. failing checks: ['PCT-010']

Overall: INCOMPLETE
```
