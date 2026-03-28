# MICA v0.2.0 Result Contract Profile

Status:
- draft optional profile
- not part of the stable `v0.1.9` baseline
- intended for projects that want each maintenance or dogfood cycle to leave behind a small, machine-readable outcome artifact
- v0.2.1 triage status: `needs dogfood trace`

## v0.2.1 Triage Note

Status: `needs dogfood trace`

Minimal adoption contract:
- `cycle_id`
- `what_changed`
- `next_action`
- `unresolved_items`

Do not use when:
- lessons alone still provide fast enough cycle recovery
- cycle frequency is too low to justify a dedicated compact result layer

## Purpose

The `Result Contract Profile` gives MICA a lightweight structure for recording **what a cycle produced**.

Base MICA already preserves:

- current state
- lessons
- invariants
- drift and lineage candidates

The result contract adds a more compact question:

`What is the minimal structured record that this cycle should leave behind?`

This is useful when lessons are too narrative and the project also needs a short machine-readable outcome record.

## Design Rule

The result layer must:

- remain optional
- remain file-based
- remain compact
- avoid becoming a full workflow engine

The goal is not to script execution.
The goal is to leave behind a small structured artifact that later sessions can interpret quickly.

## Core Idea

Lessons are good for narrative memory.
The result contract is for compact structured memory.

It should make it easy to answer:

- what changed
- what was affected
- whether unresolved issues remain
- what the next step is

without forcing later sessions to reread full lesson files first.

## Proposed Components

### 1. cycle_id

Each cycle should have a stable identifier.

Draft example:

```yaml
cycle_id: CYC-2026-03-28-001
```

### 2. what_changed

A short structured list of the major changed surfaces.

Draft example:

```yaml
what_changed:
  - code
  - playbook
  - archive
```

### 3. affected_track

Optionally binds the result to a declared track.

Draft example:

```yaml
affected_track:
  - math_core
  - docs
```

### 4. invariant_impact

Records whether invariants were added, revised, untouched, or violated.

Draft example:

```yaml
invariant_impact:
  status: revised
  affected_invariants:
    - DI-001
```

### 5. drift_status

Records whether drift was discovered, resolved, or left open.

Draft example:

```yaml
drift_status:
  status: resolved
  related_drift_ids:
    - DRF-001
```

### 6. approval_status

If approval-sensitive boundaries were crossed, records the resulting state.

Draft example:

```yaml
approval_status:
  status: not_required
```

Possible values:

- `not_required`
- `acknowledged`
- `approved`
- `blocked`

### 7. next_action

Records the next expected move.

Draft example:

```yaml
next_action:
  label: sync_dashboard_explanation
  urgency: normal
```

### 8. unresolved_items

A compact list of open issues left by the cycle.

Draft example:

```yaml
unresolved_items:
  - old heuristic wording remains in one status surface
```

## Suggested Placement

Recommended minimal placement:

1. write result-contract records as small files in a future `memory/results/` directory
2. allow the playbook to specify when a cycle should emit such a record
3. let lessons remain the narrative companion artifact

Current recommendation:
- do not require a results directory yet
- first validate the contract as a draft schema-like pattern
- only add `memory/results/` after real dogfood use shows it reduces rereading cost

## Relationship to Lessons

The `Result Contract Profile` does not replace lessons.

- lessons tell the story
- result contracts summarize the outcome

The two are complementary.

Result contracts should stay short enough that later sessions can scan them first, then decide whether a full lesson file is needed.

## Relationship to Other Profiles

The result contract becomes more informative once the earlier profiles exist:

- `Drift` helps classify mismatch outcomes
- `Track Map` helps localize the result
- `Lineage` helps connect the result to prior conceptual states
- `Approval` helps state whether protected boundaries were crossed
- `Consistency` helps standardize what a good result record should contain

This is why the profile belongs at the end of the first `v0.2.0` sequence.

## Why This Matters for Flamehaven-TOE

For `Flamehaven-TOE`, result contracts could eventually make cycle closeout much easier to recover.

Instead of rereading:

- long lessons
- scattered rationale notes
- multiple updated surfaces

a later session could first inspect a compact cycle record describing:

- which formulation changed
- whether drift was involved
- whether invariants moved
- what remains unresolved

That would be especially useful once many conceptual cycles accumulate.

## Minimal Adoption Candidate

The smallest useful version of this profile would add only:

- `cycle_id`
- `what_changed`
- `next_action`
- `unresolved_items`

and defer approval/drift/invariant integration until real cycles justify the extra structure.

## Risks

Main risks of this profile:

- duplicating lessons
- creating empty formalism for small projects
- pushing MICA toward workflow bureaucracy

That is why the first version should stay compact and avoid mandatory result artifacts.

## Acceptance Test

The profile is worth keeping only if, in dogfood use:

- later sessions recover cycle outcomes faster
- result records stay short and useful
- lessons remain necessary for narrative depth while result contracts add genuine scan-value

## Current Decision

Keep the `Result Contract Profile` in `v0.2.0` as a draft profile candidate.

It is the natural final candidate in the first branch set because it summarizes what the earlier profiles help structure, but it should remain lightweight and optional.
