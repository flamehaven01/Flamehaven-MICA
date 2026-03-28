# MICA v0.2.0 Roadmap

Status:
- draft roadmap for the `0.2.0` branch
- `v0.1.9` remains the current stable living standard

## Branch Goal

`v0.2.0` exists to test whether selected `ASDP` control-plane ideas can be imported into `MICA` as **optional, memory-facing profiles**.

This branch must preserve three constraints:

1. `MICA` remains a memory layer
2. all additions stay file-based and portable
3. stable `v0.1.9` packages remain understandable without `v0.2.0` features

## Development Order

1. `Approval Profile`
2. `Drift Profile`
3. `Track Map Profile`
4. `Lineage Profile`
5. `Consistency Profile`
6. `Result Contract Profile`

## Why Approval Comes First

`Approval` is the smallest useful import from `ASDP`.

It strengthens `MICA` where `design_invariants` alone are not enough:

- who may authorize structural change
- what requires explicit acknowledgment
- what remains blocked even when archive memory exists

That makes it the best first profile for validating the `0.2.0` branch direction.

## Why Drift Comes Immediately After

`Drift` is the most obvious next profile because it addresses the most common failure mode in long-lived projects:

- code changed, playbook unchanged
- docs changed, archive unchanged
- narrative surface changed, canonical statement unchanged

Unlike approval, drift can already produce value in single-owner projects.

That makes it a strong second profile and, in some projects, the first profile likely to produce practical dogfood evidence.

## Why Track Map Comes Next

`Track Map` is the natural follow-up to drift.

Once a project recognizes that drift happens across multiple surfaces, the next question is:

`Which subdomains of the project actually matter, and which invariants or drift classes belong to each one?`

This is especially important for projects with clearly different working zones, such as:

- core math or protocol logic
- docs and explanations
- dashboard or UI surfaces
- tests and validation layers

`Track Map` keeps MICA from treating the whole project as one undifferentiated memory object.

## Why Lineage Comes After Track Map

Once a project can say:

- which surfaces drifted
- which subdomain the issue belongs to

the next useful question is:

`How did this state emerge over time?`

`Lineage` gives MICA a way to record the historical chain behind:

- invariant changes
- drift discoveries
- rationale updates
- approval-sensitive transitions

That makes it the natural fourth profile in the branch.

## Why Consistency Comes After Lineage

Once a project can explain:

- what changed
- where it changed
- why it changed over time

the next risk is interpretive instability across sessions.

`Consistency` gives MICA a way to define:

- calibration anchors
- expected output patterns
- pre-update validation gates

This helps reduce session variance without requiring a runtime execution framework.

## Why Result Contract Comes Last

`Result Contract` is the most synthesis-oriented profile in the branch.

It depends on the earlier profiles because a useful cycle result should ideally be able to say:

- what changed
- whether drift was involved
- which track it affected
- whether any approval-sensitive boundary was crossed
- what the next action is

That makes it the natural final profile in the initial `0.2.0` candidate set.

## Branch Deliverables

Minimum branch deliverables:

- one profile spec draft
- one examples draft
- one compatibility note
- one decision note on whether the profile belongs in `v0.2.0` or later

## Exit Criteria

`v0.2.0` is ready for stabilization only if:

- at least one profile is internally coherent
- profile semantics do not break `v0.1.9` package portability
- profile syntax can be ignored by `v0.1.9` readers without corrupting the base package
- the branch still clearly stops short of becoming a full `ASDP` runtime

## Non-Goals

This branch does not:

- add runtime enforcement code
- replace `ASDP`
- introduce server or network dependency
- rewrite `v0.1.9` archive schema from scratch
