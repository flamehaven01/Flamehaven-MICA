# MICA v0.2.4 Approval Note

## Approval Status

Approved as the correct successor to v0.2.3.

This approval is based on one central judgment:

- v0.2.3 introduced DI binding but placed the schema in the wrong domain
- v0.2.4 closes the coordinate gap and adds two operational improvements without expanding scope

---

## Why v0.2.4 is better

### 1. Archive schema is now schema-governed

The fundamental flaw in v0.2.3 was that PCT-010 validated `archive.design_invariants[].binding`
but no schema governed the `binding` object in the archive domain.

v0.2.3 placed `diBinding` inside `mica.yaml.schema.json/$defs/driftClass`, which governs
`mica.yaml`'s `drift_profile.classes`. That is a different object from `archive.design_invariants`.
PCT-010 was checking structure that had no schema backing.

v0.2.4 fixes this by shipping `mica-v0.2.4-archive-di-binding.schema.json` as a dedicated
patch schema for the archive domain. The coordinate gap is closed.

### 2. PCT-010 now has a defined maturity path

In v0.2.3, PCT-010 was a perpetual WARN with no documented escalation condition.
Operators had no signal for when the standard would enforce binding.

v0.2.4 defines the path explicitly:

- WARN in v0.2.3–v0.2.5
- escalates to FAIL when `binding_required: true` is set in `mica.yaml` (planned v0.2.6)
- global FAIL reviewed at v0.3.0

This gives operators a migration schedule rather than an indefinite advisory.

### 3. PCT-011 closes a silent failure mode

v0.2.3 allowed `binding.lesson_ref` to declare a file path that did not exist.
A dead `lesson_ref` asserts evidence that cannot be read — it is worse than no reference.

PCT-011 catches this at session start. The check is WARN (not a contract-breaker),
but the failure mode is now detectable rather than silent.

### 4. hook_output policy gives operators control

v0.2.3 emitted all DIs in hook output with no volume control.
Projects with many critical DIs had no mechanism to suppress low-signal invariants.

v0.2.4 adds `hook_output: {max_di_lines, di_filter}` to `invocation_protocol`.
`di_filter: violations_only` ensures only DIs with recorded violations appear.
Omitting the policy preserves v0.2.3 behavior exactly.

---

## Design Position

v0.2.4 follows the same narrowing principle as v0.2.2 and v0.2.3:

MICA becomes more reliable by tightening schema coverage and PCT validation,
not by expanding scope.

The four changes in v0.2.4 are all corrections to existing gaps, not new features.

---

## Remaining Limits

### 1. binding_required is not yet enforced

PCT-010 remains WARN in v0.2.4. Projects with unbound critical DIs still pass CLOSED CONTRACT.
This is intentional — forcing binding on all existing archives would be a breaking change.
The escalation condition is documented but deferred to v0.2.6.

### 2. allOf composition requires operator care

The archive DI schema uses `allOf` without `additionalProperties: false` at the combined level
to preserve backward compatibility with legacy fields (`rationale`, `track`, `note`).
This means undeclared fields on archive DIs pass validation silently.
Operators must not rely on the schema to reject arbitrary fields in the archive.

### 3. hook_output is honor-system at runtime

`max_di_lines` and `di_filter` are declared in `mica.yaml` and interpreted by `mica_runtime.py`.
They are not enforced at the hook adapter level. If the hook bypasses `mica_runtime.py`,
the policy has no effect.

---

## Final Judgment

MICA v0.2.4 should be treated as:

- the version that closes the schema-PCT coordinate gap introduced in v0.2.3
- the first version where archive DI binding has formal schema governance
- the first version where PCT-010 has a documented escalation timeline

## Short Verdict

> v0.2.4 is approved because it closes the coordinate gap between what PCT-010 validates
> and what the schema governs, adds dead-link detection for lesson_ref, documents the
> PCT-010 maturity path, and gives hook operators volume control — all without expanding
> MICA's scope beyond project-memory invocation.
