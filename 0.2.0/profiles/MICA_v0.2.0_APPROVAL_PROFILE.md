# MICA v0.2.0 Approval Profile

Status:
- draft optional profile
- not part of the stable `v0.1.9` baseline
- intended for projects that need stronger change authorization than `design_invariants` alone

## Purpose

The `Approval Profile` adds a thin authorization layer on top of `MICA` memory.

It answers questions the base package does not fully answer:

- which changes may proceed automatically
- which changes require explicit human acknowledgment
- which changes remain blocked unless a named authority approves them

This is an `ASDP`-derived import, but kept deliberately small and memory-facing.

## Design Rule

The approval layer must:

- remain file-based
- remain portable
- remain optional
- never require runtime orchestration code

If a project ignores the profile, the base `MICA` package must still remain readable.

## Proposed Components

### 1. approval_policy

Defines the change classes and their required authorization level.

Draft structure:

```yaml
approval_profile:
  enabled: true
  default_action: require_acknowledgment
  rules:
    - id: APR-001
      change_class: design_invariant_modification
      required_action: explicit_approval
      authority: project_owner
    - id: APR-002
      change_class: archive_metadata_update
      required_action: auto_allow
    - id: APR-003
      change_class: canonical_statement_rewrite
      required_action: explicit_approval
      authority: project_owner
```

### 2. approval_identity

Defines who may approve protected classes of change.

Draft example:

```yaml
approval_identity:
  primary_authority: project_owner
  recognized_authorities:
    - project_owner
    - designated_maintainer
```

### 3. evidence_contract

Defines what evidence must exist before approval-sensitive changes are accepted.

Draft example:

```yaml
evidence_contract:
  design_invariant_modification:
    requires:
      - rationale_note
      - affected_files
      - approval_record
  canonical_statement_rewrite:
    requires:
      - rationale_note
      - provenance_update
      - approval_record
```

### 4. decision_contract

Defines the minimal decision artifact that records approval events.

Draft example:

```yaml
decision_contract:
  required_fields:
    - decision_id
    - change_class
    - authority
    - rationale
    - timestamp
```

## Suggested Placement

The `Approval Profile` should not be forced into every package.

Preferred placement options:

1. `mica.yaml` optional top-level field
2. playbook section for narrative usage rules
3. future `memory/approval/` directory only if the profile proves necessary in repeated dogfood cycles

Current recommendation:
- define policy metadata in `mica.yaml`
- record concrete decisions in playbook or lessons until a dedicated decision artifact is justified

## Relationship to design_invariants

`design_invariants` and `Approval Profile` do different work.

- `design_invariants` say what must not be violated
- `Approval Profile` says who may authorize a protected structural change and what evidence must accompany it

Example:

- `DI-001` blocks arbitrary weighting
- `Approval Profile` says that changing `DI-001` itself requires explicit approval by the project owner plus rationale evidence

## Minimal Adoption Candidate

The smallest useful version of the profile would add only:

- `approval_policy`
- `approval_identity`

and leave `evidence_contract` / `decision_contract` for a later step.

## Risks

Main risks of this profile:

- turning MICA into a policy engine
- requiring too much ceremony for small projects
- duplicating what playbook text already does informally

That is why this profile must stay optional and thin.

## Acceptance Test

The profile is worth keeping only if, in dogfood use:

- it prevents at least one real unauthorized high-impact change
- it does not make low-risk archive maintenance cumbersome
- it remains understandable from files alone

## Current Decision

Keep the `Approval Profile` in `v0.2.0` as a draft profile candidate.

Do not promote it into the stable core until a real project uses it and produces at least one clear approval/denial trace.
