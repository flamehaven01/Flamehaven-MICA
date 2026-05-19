# MICA v0.2.3 → v0.2.4 Comparison

## Summary

v0.2.3 and v0.2.4 share the same operational direction — both enforce DI binding evidence.
The difference is where the enforcement is anchored.

- v0.2.3 introduced DI binding, but schema was in the wrong domain (mica.yaml, not archive)
- v0.2.4 moves the schema anchor to the correct domain and adds two operational improvements

That makes v0.2.4 the architecturally coherent successor.

---

## Comparison Table

| Area | v0.2.3 | v0.2.4 | Judgment |
|------|--------|--------|----------|
| Archive DI binding schema | Absent — `diBinding` lived in `mica.yaml.schema.json/$defs/driftClass` | `mica-v0.2.4-archive-di-binding.schema.json` — dedicated patch schema | v0.2.4 better |
| Schema-PCT coordinate | PCT-010 checks archive; schema governs mica.yaml DI classes — mismatched domains | PCT-010 checks archive; `archive-di-binding.schema.json` governs archive | v0.2.4 better |
| PCT-010 maturity path | Perpetual WARN — no documented escalation condition | WARN → FAIL when `binding_required: true` (v0.2.6); global FAIL at v0.3.0 | v0.2.4 better |
| lesson_ref validation | Undetected dead links — PCT had no check | PCT-011: WARN when `binding.lesson_ref` path does not exist | v0.2.4 better |
| Hook output volume | Unlimited — all critical DIs emitted | `hook_output: {max_di_lines, di_filter}` in `invocation_protocol` | v0.2.4 better |
| Backward compatibility | N/A | Archives without `binding` continue to work; `hook_output` optional | v0.2.4 preserves |
| allOf composition | N/A | `designInvariantEntryV024` uses `allOf` without top-level `additionalProperties: false` | v0.2.4 correct |
| CLOSED CONTRACT impact | PCT-010 WARN did not break status | PCT-010/011 WARN do not break status (by design) | Same |

---

## Detailed Delta

### 1. Schema Domain Correction

#### v0.2.3

v0.2.3 added `diBinding` to `mica.yaml.schema.json/$defs/driftClass`:

```json
"driftClass": {
  "properties": {
    "binding": { "$ref": "#/$defs/diBinding" }
  }
}
```

This governs `mica.yaml drift_profile.classes[].binding` — a mica.yaml construct.

But PCT-010 checks `archive.design_invariants[severity==critical]` — a different object
in a different file. The schema and the check were in different domains.

#### v0.2.4

A dedicated schema covers the archive domain:
`mica-v0.2.4-archive-di-binding.schema.json`

It defines `diBinding` and `designInvariantEntryV024`, governs
`archive.design_invariants[].binding`, and is referenced by a `$comment` in the schema
clarifying domain separation.

---

### 2. PCT-010 Maturity Path

#### v0.2.3

PCT-010 emitted a WARN when critical DIs lacked `binding.origin_episode`.
No escalation condition was documented. The WARN was effectively permanent.

#### v0.2.4

PCT-010 WARN message now states:

```
escalates to FAIL when binding_required: true is set (planned v0.2.6)
```

Operators know what behavior triggers FAIL. The standard has a migration timeline.

---

### 3. PCT-011 — New Validator

#### v0.2.3

`binding.lesson_ref` could point to a non-existent file. No check detected this.
A dead `lesson_ref` asserted evidence that could not be read. Silent failure.

#### v0.2.4

PCT-011 validates `binding.lesson_ref` paths at session start:

| State | PCT-011 result |
|-------|---------------|
| Dead link found | WARN — named broken paths |
| All paths exist | PASS |
| No `lesson_ref` fields declared | INFO |

WARN does not break CLOSED CONTRACT. But the failure mode is now visible.

---

### 4. Hook Output Volume Control

#### v0.2.3

Hook output emitted all critical DIs unconditionally:

```text
[MICA:DI] DI-001(critical): no-destructive-reset [2x]
[MICA:DI] DI-002(critical): billing-thresholds-are-measured
[MICA:DI] DI-003(critical): chunk-cache-thresholds-are-tested
[MICA:DI] DI-004(critical): no-schema-drift
```

Projects with many critical DIs had no control over hook context pollution.

#### v0.2.4

`hook_output` policy in `invocation_protocol`:

```yaml
hook_output:
  max_di_lines: 2
  di_filter: violations_only
```

Effect on the same four DIs (assuming only DI-001 and DI-003 have `violation_count > 0`):

```text
[MICA:DI] DI-001(critical): no-destructive-reset [2x]
[MICA:DI] DI-003(critical): chunk-cache-thresholds-are-tested [1x]
```

DI-002 and DI-004 are suppressed (zero-violation). Cap of 2 is respected.
Omitting `hook_output` preserves v0.2.3 behavior exactly.

---

## What v0.2.3 did correctly

v0.2.3 introduced the right concept — grounding critical invariants in the episodes
that created them. The `binding` block structure (`origin_episode`, `violation_count`,
`lesson_ref`, `last_triggered`) is unchanged in v0.2.4.

v0.2.3's contribution was the concept. v0.2.4's contribution is the correct placement.

---

## Final Comparison Judgment

v0.2.3 was the correct operational intent.

v0.2.4 is the correct architectural execution.

If the goal is a standard where schema, PCT, and archive are aligned in the same domain,
v0.2.4 is the required successor.
