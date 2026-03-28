# MICA v0.1.8.1 Playbook

Status: concise operator playbook for creating and validating a `v0.1.8.1` universal archive

## Goal

Produce a schema-valid MICA archive with:

- explicit invocation
- explicit self-test runtime
- stable track authority
- minimal onboarding ambiguity

## Step 0: Choose The Right Branch

Use `v0.1.8.1 universal` if the target is:

- operational archive
- AI session continuity
- README-as-Protocol or equivalent invocation
- governance without lab parity contracts

Do not use it for:

- parity-driven laboratory orchestration
- cycle-contract experimentation

For that, use `mica-lab-v0.1.5.schema.json`.

## Step 1: Pick Your Starting Mode

Use one of these:

- `Lite`
  - minimum viable context anchor
- `Standard`
  - normal operational archive
- `Full`
  - governance-grade archive

These are usage profiles, not different schemas.

## Step 2: Start From The Correct File

Recommended starting file:

- `../mica-v0.1.8-minimal-instance.json`

Drafting aid:

- `../mica-v0.1.8-fill-template.json`

Do not validate the fill template directly.

## Step 3: Fill The Irreducible Core

Before anything else, fill these correctly:

1. `mica_schema_version`
2. `project`
3. `design_invariants`
4. `invocation_protocol`
5. `provenance_registry`
6. `session_report_format`
7. `drift_response_policy`
8. `self_test_policy`

If these are weak, the archive may be valid JSON but not a useful MICA.

## Step 4: Set Invocation Explicitly

Recommended default:

- `primary_pattern: readme_protocol`
- `self_test_runtime: readme_protocol_ai_session`

Why:

- most portable
- easiest to explain
- directly compatible with README-as-Protocol handoff

## Step 5: Write Self-Tests Correctly

Every self-test should answer three questions:

1. what is being checked
2. who can evaluate it
3. what happens if it fails

Recommended shape:

- `description`
- `check_type`
- `severity`
- optional `expression`
- optional `target`
- `on_fail`

Use `expression` when you want shared logic across:

- AI session
- Python validator
- CI runner

Leave `expression` absent when the check is intentionally human-run.

## Step 6: Use track_map Only When It Is Warranted

Use `track_map` only if:

1. the project has 2 or more logical file groups
2. at least one DI applies only to a subset of those groups
3. tasks can meaningfully route by track

If not, omit `track_map`.

Default rule:

- no `track_map` means all DIs apply uniformly

## Step 7: Respect Track Authority

Single source of truth:

- `designInvariantEntry.track`

Derived field:

- `trackEntry.invariants`

Do not manually edit `trackEntry.invariants` first.

Correct flow:

1. assign or change `designInvariantEntry.track`
2. recompute the track entry invariant list
3. run self-test

## Step 8: Choose A Realistic Profile

### Lite

Use when:

- onboarding
- first install
- retrofitting a project

Allowable shortcut:

- copy operational policy blocks from the minimal instance

### Standard

Use when:

- the archive will actually be used in maintenance sessions

Add:

- real self-test expressions
- meaningful semantic rules
- track_map if needed
- real deviation log entries

### Full

Use when:

- governance traceability matters
- you want audit-grade handoff

Add:

- complete artifact manifest
- updated self-test results
- rich self-consistency checks
- track discipline and README sync

## Step 9: Validate In This Order

1. schema validation
2. invocation completeness
3. self-test coverage
4. provenance completeness
5. track authority consistency

Do not start by polishing examples.
Start by making the archive operational.

## Step 10: Watch For Common Failure Modes

### Failure 1: Schema-valid but operationally empty

Cause:

- copied defaults
- no real provenance
- no real DIs

Fix:

- replace boilerplate fields with project-specific values

### Failure 2: Human-only self-tests disguised as machine checks

Cause:

- expression missing
- runtime unclear

Fix:

- either add `expression`
- or clearly accept that the check is human-run

### Failure 3: track drift

Cause:

- `designInvariantEntry.track` and `trackEntry.invariants` edited separately

Fix:

- treat DI track assignment as authoritative

### Failure 4: Template submitted to validator

Cause:

- using `fill-template.json` as if it were an instance

Fix:

- validate the minimal instance or a cleaned derived file only

## Step 11: Recommended Session Runtime

Default recommendation:

- invocation via README
- self-test runtime via AI session
- secondary validator later if needed

This is the most practical universal path today.

## Step 12: Release Rule

Do not call an archive complete unless:

- schema passes
- invocation is explicit
- self-test runtime is explicit
- provenance exists
- at least one critical DI exists
- profile choice is clear

That is the minimum bar for a usable `v0.1.8.1` universal MICA.

