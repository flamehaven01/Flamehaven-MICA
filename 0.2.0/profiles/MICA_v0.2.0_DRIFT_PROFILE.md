# MICA v0.2.0 Drift Profile

Status:
- draft optional profile
- not part of the stable `v0.1.9` baseline
- intended for projects where divergence between code, docs, playbook, and archive creates recurring confusion

## Purpose

The `Drift Profile` adds a thin, file-based way to classify and respond to **surface divergence** inside a MICA-managed project.

It is designed for cases where the project is still functioning, but its descriptive surfaces no longer agree.

Typical examples:

- code changed but playbook still describes the old model
- README changed but canonical statement still reflects the old intent
- archive invariants changed without a matching rationale note
- status messages or operating prompts still reference superseded versions

This profile does not try to detect semantic truth automatically at runtime.
It defines a disciplined way for humans and MICA-aware AI sessions to identify, record, and react to drift.

## Design Rule

The drift layer must:

- remain file-based
- remain optional
- remain memory-facing
- avoid becoming a full monitoring engine

It may classify drift and recommend responses, but it must not require background daemons, watchers, or server-side enforcement.

## Core Idea

`MICA` already stores:

- identity
- canonical statement
- invariants
- lessons

The `Drift Profile` adds a small amount of structure for a new question:

`Do the major project surfaces still describe the same project state?`

## Proposed Components

### 1. drift_response_policy

Defines the main drift classes and the expected response.

Draft structure:

```yaml
drift_profile:
  enabled: true
  default_action: warn_continue
  classes:
    - id: DRF-001
      label: code_playbook_divergence
      severity: error
      action: require_acknowledgment
    - id: DRF-002
      label: docs_canonical_divergence
      severity: warning
      action: warn_continue
    - id: DRF-003
      label: invariant_change_without_rationale
      severity: critical
      action: block_session
    - id: DRF-004
      label: version_reference_staleness
      severity: warning
      action: warn_continue
```

### 2. source_classes

Defines which project surfaces are compared.

Draft example:

```yaml
source_classes:
  - code
  - playbook
  - archive
  - readme
  - changelog
  - prompt_surface
```

The profile should allow projects to choose only the surfaces that actually matter.

### 3. drift_evidence_expectations

Defines what evidence is sufficient to record a drift event.

Draft example:

```yaml
drift_evidence_expectations:
  code_playbook_divergence:
    requires:
      - changed_surface
      - stale_surface
      - brief_explanation
  invariant_change_without_rationale:
    requires:
      - changed_invariant
      - missing_rationale_reference
```

### 4. response_actions

Defines the intended session-level behavior after drift is recognized.

Draft actions:

- `block_session`
- `require_acknowledgment`
- `warn_continue`
- `log_only`

These actions should align with the same practical force language already used elsewhere in MICA.

## Suggested Placement

Recommended minimal placement:

1. optional policy metadata in `mica.yaml`
2. narrative interpretation rules in the playbook
3. actual drift events recorded in lessons or future result-contract artifacts

Current recommendation:
- define drift classes in `mica.yaml`
- record concrete drift traces in lessons until a dedicated drift ledger is justified

## Relationship to design_invariants

The `Drift Profile` is not a replacement for `design_invariants`.

- `design_invariants` define what must not be violated
- `Drift Profile` defines what to do when project surfaces no longer agree, even if no invariant has yet been formally violated

Example:

- playbook still describes heuristic weighting
- code now uses chi-squared weighting
- no invariant may be violated yet
- but the project has clearly entered a state of `code_playbook_divergence`

That is a drift problem, not necessarily an invariant problem.

## Why This Matters for Flamehaven-TOE

For `Flamehaven-TOE`, the most realistic early profile value is not approval. It is drift handling.

Examples already seen in practice:

- code patch applied, playbook not updated
- status or SPARC messaging still referencing a superseded version
- explanation surfaces lagging behind the actual mathematical model

These are exactly the types of mismatch the drift layer should make explicit.

## Minimal Adoption Candidate

The smallest useful version of this profile would add only:

- `drift_response_policy`
- `source_classes`

and would store actual drift cases in lessons rather than creating a dedicated drift ledger.

## Risks

Main risks of this profile:

- over-classifying normal project change as drift
- creating too much maintenance ceremony
- drifting toward a generalized observability system

That is why the first implementation should stay small and focus on a few high-value drift classes only.

## Acceptance Test

The profile is worth keeping only if, in dogfood use:

- it catches real surface mismatches that would otherwise waste session time
- it stays understandable from files alone
- it improves session recovery and update discipline without becoming bureaucratic

## Current Decision

Keep the `Drift Profile` in `v0.2.0` as a draft profile candidate.

It is a stronger near-term candidate than `Approval Profile` for single-owner research projects, because it addresses real divergence without requiring multi-actor approval structure.
