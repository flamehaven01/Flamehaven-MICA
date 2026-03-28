# MICA v0.2.0 Consistency Profile

Status:
- draft optional profile
- not part of the stable `v0.1.9` baseline
- intended for projects where repeated AI sessions should converge on similar interpretations of the same memory state

## Purpose

The `Consistency Profile` adds a thin structure for reducing **interpretive variance** across sessions.

Base MICA already preserves memory.
The consistency layer asks a different question:

`Will two later sessions read this package and behave in roughly the same way?`

This matters most when a project depends on:

- stable conceptual interpretation
- repeatable decision framing
- low variance in update discipline

## Design Rule

The consistency layer must:

- remain optional
- remain file-based
- remain memory-facing
- avoid becoming a full evaluation runtime

Its role is not to prove model correctness.
Its role is to reduce avoidable variation in how a MICA-aware session interprets and updates the package.

## Core Idea

Current MICA is strong at preserving:

- identity
- invariants
- lessons
- rationale traces

The consistency question is:

`What anchors or checks should a session use before it changes memory?`

This profile answers that with lightweight artifacts instead of runtime enforcement.

## Proposed Components

### 1. calibration_anchors

Defines a small set of high-value reference examples or orientation anchors.

Draft example:

```yaml
calibration_anchors:
  - id: ANK-001
    label: canonical_math_phase
    reference: lessons/2026-03-27-v495-chi2-omega.md
  - id: ANK-002
    label: current_statement_anchor
    reference: archive.canonical_statement
```

The goal is to keep later sessions from drifting too far from the project's accepted reference points.

### 2. expected_output_patterns

Defines what a valid update or interpretation should roughly look like.

Draft example:

```yaml
expected_output_patterns:
  - id: EOP-001
    context: archive_update
    expectation: "state the changed surface, rationale, and next action"
  - id: EOP-002
    context: lesson_entry
    expectation: "record failure pattern, consequence, and prevention rule"
```

This is not strict templating. It is a guidance layer that reduces ambiguity.

### 3. pre_update_validation_gate

Defines minimal checks that should pass before a session writes back to memory.

Draft example:

```yaml
pre_update_validation_gate:
  required_checks:
    - package_complete
    - no_unresolved_critical_drift
    - changed_surface_named
    - rationale_present
```

This gate is still procedural, not executable.
Its purpose is to make memory updates less arbitrary.

### 4. variance_notes

Provides a place to record where session interpretation has historically varied.

Draft example:

```yaml
variance_notes:
  - id: VAR-001
    area: math_core
    note: "sessions often over-read old heuristic weighting references"
```

This helps later sessions avoid known interpretive traps.

## Suggested Placement

Recommended minimal placement:

1. define profile metadata in `mica.yaml`
2. explain anchor usage and validation steps in the playbook
3. store concrete variance evidence in lessons

Current recommendation:
- keep anchors few and high-value
- keep expected patterns short
- keep validation gates procedural rather than heavy

## Relationship to Drift Profile

The `Consistency Profile` does not replace drift handling.

- `Drift` asks whether surfaces disagree
- `Consistency` asks whether future sessions can interpret the package in a stable way

The two profiles are related but distinct.

Example:

- no new drift may exist
- but sessions may still vary in how they interpret old lesson files or canonical language

That is a consistency problem, not necessarily a drift problem.

## Relationship to Lineage

`Lineage` explains ancestry.
`Consistency` explains how to keep interpretation stable once that ancestry exists.

Together they reduce:

- rereading cost
- interpretive variance
- memory update noise

## Why This Matters for Flamehaven-TOE

For `Flamehaven-TOE`, consistency matters because the project has:

- conceptual phases
- mathematical explanation surfaces
- evolving lessons
- version-sensitive narrative wording

Without consistency anchors, a later session may read the same package and still place too much weight on outdated or secondary surfaces.

With a lightweight consistency layer, the package can say:

- what to trust first
- what a good update should include
- what known interpretive traps to avoid

## Minimal Adoption Candidate

The smallest useful version of this profile would add only:

- `calibration_anchors`
- `pre_update_validation_gate`

and defer expected output patterns or variance notes until real dogfood cycles show they help.

## Risks

Main risks of this profile:

- creating too much ceremony around every update
- confusing consistency with correctness
- turning anchor lists into another bulky memory surface

That is why the profile should start with a very small number of anchors and checks.

## Acceptance Test

The profile is worth keeping only if, in dogfood use:

- later sessions converge faster on the same interpretation
- update quality becomes more regular
- anchor overhead stays small relative to the orientation benefit

## Current Decision

Keep the `Consistency Profile` in `v0.2.0` as a draft profile candidate.

It is especially useful for research-heavy projects with evolving conceptual language, but it should remain a lightweight orientation and pre-update discipline layer rather than a scoring engine.
