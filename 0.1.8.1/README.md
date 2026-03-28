# MICA v0.1.8.1 Universal Patch Pack

Status: operator-facing manual for the `0.1.8.1` patch release

This folder is the entrypoint for the `v0.1.8.1` universal patch.

`v0.1.8.1` does not replace the universal model. It patches three concrete gaps in `v0.1.8`:

1. `selfTestCheck.expression`
   - lets self-test checks carry a machine-evaluable predicate
2. `invocation_protocol.self_test_runtime`
   - makes the runtime that executes `self_test_policy` explicit
3. `trackEntry.invariants` authority note
   - makes `designInvariantEntry.track` authoritative and `trackEntry.invariants` derived

## Files

Primary file in this folder:

- `mica-v0.1.8.1-universal.schema.json`

Companion files in the parent MICA directory:

- `../mica-v0.1.8-minimal-instance.json`
- `../mica-v0.1.8-fill-template.json`
- `../MICA_v0.1.8_UNIVERSAL_USAGE.md`
- `../MICA_INVOCATION_PATTERNS_v1.0.md`

## What To Read First

If you are evaluating the patch:

1. `mica-v0.1.8.1-universal.schema.json`
2. `../MICA_v0.1.8_UNIVERSAL_USAGE.md`
3. `PLAYBOOK.md`

If you are creating a new archive:

1. `../mica-v0.1.8-minimal-instance.json`
2. `../mica-v0.1.8-fill-template.json`
3. `mica-v0.1.8.1-universal.schema.json`
4. `PLAYBOOK.md`

## Release Intent

Use `v0.1.8.1` when:

- you already want the `v0.1.8` universal model
- you need a clearer onboarding path
- you want a portable self-test predicate layer
- you need explicit authority rules for `track_map`

Do not use this patch to relax governance. This patch exists to make `v0.1.8` easier to adopt and less ambiguous to operate.

## Package Model

Treat the patch pack as four layers:

1. Schema
   - `mica-v0.1.8.1-universal.schema.json`
2. Usage discipline
   - `../MICA_v0.1.8_UNIVERSAL_USAGE.md`
3. Minimal starting point
   - `../mica-v0.1.8-minimal-instance.json`
4. Human-fill authoring aid
   - `../mica-v0.1.8-fill-template.json`

The schema is normative.
The usage doc is normative usage discipline.
The minimal instance is a valid starting point.
The fill template is an authoring aid and is intentionally not schema-valid.

## Important Warning

`../mica-v0.1.8-fill-template.json` is not a validator target.

It contains `_comment_*` helper keys and placeholder text. Use it as a drafting aid only.

Validation target:

- `mica-v0.1.8.1-universal.schema.json`

Recommended instance baseline:

- `../mica-v0.1.8-minimal-instance.json`

## Patch Summary

### Patch 1: self-test expressions

`selfTestCheck.expression` is optional.

Meaning:

- if present: a runtime may evaluate it directly
- if absent: the check remains human-run or implementation-specific

This avoids breaking existing archives while opening a machine-readable path for AI session, Python, and CI runtimes.

### Patch 2: explicit self-test runtime

`invocation_protocol.self_test_runtime` clarifies who runs the tests.

Most important value:

- `readme_protocol_ai_session`

This makes README-as-Protocol a declared runtime, not just an implied pattern.

### Patch 3: track authority direction

`designInvariantEntry.track` is authoritative.

`trackEntry.invariants` is derived.

This prevents dual-edit drift.

## Recommended Adoption Path

For most teams:

1. start from `../mica-v0.1.8-minimal-instance.json`
2. validate against `mica-v0.1.8.1-universal.schema.json`
3. use `../mica-v0.1.8-fill-template.json` only while drafting
4. read `PLAYBOOK.md`
5. finalize against the usage rules

## Versioning Note

`v0.1.8.1` is a patch release over `v0.1.8`, not a new universal branch.

Operational interpretation:

- `v0.1.8` = universal model with invocation and self-test architecture
- `v0.1.8.1` = onboarding and execution-discipline patch

