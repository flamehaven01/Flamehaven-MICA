# MICA v0.2.0 Lineage Profile

Status:
- draft optional profile
- not part of the stable `v0.1.9` baseline
- intended for projects that need more than current-state memory and want a thin historical chain for why major memory-relevant changes happened
- v0.2.1 triage status: `needs dogfood trace`

## v0.2.1 Triage Note

Status: `needs dogfood trace`

Minimal adoption contract:
- `why_lineage`
- `invariant_revision_lineage`

Do not use when:
- Git history plus lessons already make conceptual ancestry easy enough to recover
- the project has not yet produced enough meaningful phase shifts to justify a lineage layer

## Purpose

The `Lineage Profile` gives MICA a structured way to remember **how the current state came to be**.

Base MICA already remembers current identity, invariants, and lessons.

The lineage layer adds a lightweight historical chain for:

- why a statement changed
- why an invariant was added, revised, or removed
- how a drift condition was discovered and resolved
- how a project moved from one operating state to another

It is not a full history engine. It is a **memory-facing explanation chain**.

## Design Rule

The lineage layer must:

- remain optional
- remain file-based
- remain compact
- avoid duplicating Git history

Git already answers:

- who changed which file
- when code changed

The lineage layer should answer:

- why the project memory changed
- what conceptual transition happened
- which prior state this new state descends from

## Core Idea

Current MICA is strong at preserving present structure.

The lineage question is different:

`What is the meaningful ancestry of the current memory state?`

This is especially useful when a project has passed through multiple conceptual revisions and a future session needs to know not only what is true now, but why the project no longer follows an older pattern.

## Proposed Components

### 1. why_lineage

Captures the rationale ancestry behind major memory or playbook revisions.

Draft example:

```yaml
why_lineage:
  - id: LIN-001
    current_statement: chi_squared_weighting
    supersedes: heuristic_weighting
    rationale_ref: lessons/2026-03-27-v495-chi2-omega.md
```

### 2. invariant_revision_lineage

Captures the change history of `design_invariants`.

Draft example:

```yaml
invariant_revision_lineage:
  - invariant_id: DI-001
    event: introduced
    reason: prevent arbitrary weighting regression
    evidence_ref: lessons/2026-03-27-v495-chi2-omega.md
  - invariant_id: DI-001
    event: revised
    reason: clarified measurement-count requirement
    evidence_ref: lessons/2026-04-10-formalization-note.md
```

### 3. drift_lineage

Captures the lifecycle of important drift events.

Draft example:

```yaml
drift_lineage:
  - drift_id: DRF-001
    discovered_in: lessons/2026-04-02-playbook-lag.md
    resolved_in: lessons/2026-04-03-playbook-sync.md
    affected_track: math_core
```

### 4. state_transition_lineage

Captures meaningful phase shifts in the project rather than low-level file edits.

Draft example:

```yaml
state_transition_lineage:
  - id: STL-001
    from_state: heuristic_phase
    to_state: chi_squared_phase
    evidence_ref: lessons/2026-03-27-v495-chi2-omega.md
```

## Suggested Placement

Recommended minimal placement:

1. define lineage structures in the archive
2. use playbook sections to explain how lineage should be interpreted
3. reference lessons as the narrative evidence layer

Current recommendation:
- keep lineage as compact pointers, not full narrative duplication
- let lessons remain the long-form memory surface
- use lineage only for high-value transitions

## Relationship to Git History

The `Lineage Profile` must not try to replace Git.

Git is better at:

- file-level change history
- author attribution
- commit chronology

The `Lineage Profile` is better at:

- conceptual ancestry
- invariant ancestry
- drift ancestry
- reasoning continuity across sessions

If the profile begins to mirror raw commit history, it has become too heavy.

## Relationship to Lessons

Lessons remain the narrative memory layer.

The lineage layer should be thinner:

- lessons tell the story
- lineage points to the story and states what changed in conceptual terms

This lets later sessions recover ancestry quickly without rereading every lesson file.

## Relationship to Approval and Drift

The profile complements both:

- `Approval` says who may authorize protected structural change
- `Drift` says when surfaces no longer agree
- `Lineage` says how the project moved from the old state to the new one

It is therefore a natural follow-up after those profiles exist.

## Why This Matters for Flamehaven-TOE

For `Flamehaven-TOE`, lineage is useful because the project is not merely accumulating edits. It is moving through conceptual phases.

Examples:

- heuristic weighting phase
- chi-squared weighting phase
- future cross-check or bridge activation phases

Without lineage, later sessions can see only the current state plus scattered lessons.
With lineage, they can recover the conceptual ancestry of why the present formulation exists.

That reduces the risk of repeating superseded designs.

## Minimal Adoption Candidate

The smallest useful version of this profile would add only:

- `why_lineage`
- `invariant_revision_lineage`

and defer drift/state-transition lineage until real cycles justify them.

## Risks

Main risks of this profile:

- duplicating Git history
- writing too much ceremony around every small change
- turning lineage into another long narrative layer instead of a compact index

That is why the profile should only record high-value conceptual transitions.

## Acceptance Test

The profile is worth keeping only if, in dogfood use:

- it helps a later session understand why a current invariant or formulation exists
- it reduces rereading cost across many lesson files
- it stays compact enough to remain a fast orientation layer

## Current Decision

Keep the `Lineage Profile` in `v0.2.0` as a draft profile candidate.

It is especially promising for research-heavy projects with phase shifts, but it should remain a thin conceptual ancestry layer rather than a second version-control system.
