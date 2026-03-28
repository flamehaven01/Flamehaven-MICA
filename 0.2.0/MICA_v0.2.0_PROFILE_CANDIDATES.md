# MICA v0.2.0 Profile Candidates

Status:
- draft candidate list for the `0.2.0` branch
- `0.1.9` remains the current stable living standard

## Why v0.2.0 Exists

`v0.1.9` closed the core MICA package contract:

- `mica.yaml` composition contract
- archive alignment on the same version axis
- `PCT-*` package completeness checks
- three placement contexts

`v0.2.0` is not a bugfix branch.
It is the first branch for **optional extensions** derived from stronger control-plane ideas in `ASDP`, while keeping MICA itself a memory layer.

## Design Rule

MICA must remain:

- portable
- file-based
- AI-readable
- memory-layer first

Therefore, any import from `ASDP` must be:

- optional
- thin
- memory-facing only

MICA must **not** become a full sovereign execution architecture.

## Candidate Profiles

### 1. Lineage Profile

Purpose:
- make institutional memory more explicit across time

Candidate additions:
- `why_lineage`
- `approval_lineage`
- `drift_lineage`
- `invariant_revision_lineage`

Why this matters:
- current MICA remembers state and lessons
- lineage would make the historical reason for state changes machine-readable

### 2. Drift Profile

Purpose:
- detect structured drift between project surfaces

Candidate additions:
- `drift_response_policy`
- source-aware drift classes
- code/playbook/docs/archive divergence rules

Example drift conditions:
- code changed, playbook unchanged
- archive invariants changed, approval note absent
- README narrative changed, canonical statement unchanged

### 3. Approval Profile

Purpose:
- formalize which changes require acknowledgment, approval, or block

Candidate additions:
- `approval_policy`
- `approval_identity`
- `evidence_contract`
- `decision_contract`

Why this matters:
- `design_invariants` can already block behavior
- approval profile would define who can authorize exceptions or structural changes

### 4. Consistency Profile

Purpose:
- reduce interpretive variance across sessions and runtimes

Candidate additions:
- calibration anchors
- expected output patterns
- pre-update validation gate

Why this matters:
- helps keep MICA updates and archive evolution reproducible

### 5. Track Map Profile

Purpose:
- map memory to explicit project subdomains

Candidate additions:
- `track_map`
- track-specific invariants
- track-specific drift checks

Example tracks:
- `math_core`
- `dashboard`
- `tests`
- `docs`
- `data_pipeline`

### 6. Result Contract Profile

Purpose:
- make each maintenance or dogfood cycle produce a small structured outcome artifact

Candidate additions:
- `cycle_id`
- `what_changed`
- `invariant_impact`
- `approval_status`
- `drift_detected`
- `next_action`

Why this matters:
- lessons remain narrative
- result contracts would add machine-readable cycle outputs

## Recommended Order

Recommended `v0.2.0` exploration order:

1. `Approval Profile`
2. `Drift Profile`
3. `Track Map Profile`
4. `Lineage Profile`
5. `Consistency Profile`
6. `Result Contract Profile`

This order keeps the first additions closest to MICA's existing role:

- constraint preservation
- package integrity
- evolution discipline

## Non-Goals

`v0.2.0` should not:

- replace `ASDP`
- embed runtime orchestration
- add server-dependent behavior
- convert MICA into a full policy engine

## Working Principle

`v0.1.9` made MICA a living standard.
`v0.2.0` should make MICA a stronger memory layer without losing its portability.
