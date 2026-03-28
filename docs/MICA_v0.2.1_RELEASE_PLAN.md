# MICA v0.2.1 Release Plan

Status:
- release intent document for the `draft/v0.2.1` workstream
- not a new profile branch
- focused on triage, adoption discipline, and profile boundary cleanup

## Release Intent

`v0.2.1` is **not** a profile-expansion release.

It exists to narrow and stabilize what was opened in `v0.2.0`.

Its role is to:

- keep the six existing draft profiles
- remove ambiguity about which are immediately useful
- reduce overlap and unclear boundaries between them
- define which profiles are dogfood-ready and which remain speculative

## Non-Goals

`v0.2.1` does not:

- add a seventh profile
- replace `v0.1.9` as the stable core
- promote every draft profile into adopt-now status
- turn MICA into a runtime governance engine

## Core Work Axes

### 1. Profile Triage

Each draft profile must receive a clear status:

- `adopt now`
- `needs dogfood trace`
- `draft only`

### 2. Adoption Discipline

Each profile must state:

- minimal adoption contract
- when it should not be used
- what kind of project pressure justifies it

### 3. Cross-Profile Coherence

The six profiles must be made less redundant.

The key requirement is that each one answers a meaningfully different question:

- `Approval` → who may authorize protected structural change?
- `Drift` → which project surfaces no longer agree?
- `Track Map` → which subdomain does a memory or issue belong to?
- `Lineage` → how did the current state emerge?
- `Consistency` → how do later sessions interpret the package similarly?
- `Result Contract` → what compact outcome should each cycle leave behind?

### 4. Dogfood Gating

Profiles that look good in theory but lack real project evidence must remain draft.

`v0.2.1` should make that explicit rather than leaving it implicit.

## Representative Dogfood Priority Order

This is not TOE-exclusive, but it is informed by real multi-surface project conditions.

Recommended adoption order:

1. `Drift`
2. `Track Map`
3. `Lineage`
4. `Consistency`
5. `Result Contract`
6. `Approval`

Rationale:

- `Drift` solves the most immediate and repeatable pain
- `Track Map` makes drift and invariants more precise
- `Lineage` becomes useful once drift and track localization exist
- `Consistency` is helpful after a project has several interpretive surfaces
- `Result Contract` becomes useful once cycle history is dense enough
- `Approval` is most context-sensitive and easiest to over-apply

## Deliverables

`v0.2.1` should produce:

- this release plan
- a profile status matrix
- status labels inside each profile document
- explicit “when not to use” guidance in each profile
- updated pointers in root and `0.2.0` documentation

## Completion Criteria

`v0.2.1` is complete when:

- all six profiles have explicit status
- the dogfood-ready subset is named
- the representative adoption order is clear
- the difference between draft and adoptable profiles is easy to read
- one or two next dogfood targets can be named without expanding the profile set further

## Release Interpretation

If `v0.2.0` created the first candidate profile set, then `v0.2.1` should be read as:

`candidate-set discipline`

It is the first version that says not only what could be added to MICA, but also what should be adopted first and what should remain provisional.
