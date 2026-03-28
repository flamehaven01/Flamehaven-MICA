# MICA v0.2.1 Profile Status Matrix

Status:
- workstream matrix for `draft/v0.2.1`
- summarizes the six `v0.2.0` profile candidates by readiness and use boundary

## Matrix

| Profile | v0.2.1 status | Representative priority | Minimal adoption contract | Do not use when |
|---|---|---:|---|---|
| `Drift` | `adopt now` | 1 | `drift_response_policy` + `source_classes` | the project is too small to have meaningful multi-surface divergence |
| `Track Map` | `adopt now` | 2 | `track_map` + optional `track_authority_hint` | the project is genuinely single-surface and track labels add no clarity |
| `Lineage` | `needs dogfood trace` | 3 | `why_lineage` + `invariant_revision_lineage` | the project changes are shallow enough that Git + lessons already suffice |
| `Consistency` | `needs dogfood trace` | 4 | `calibration_anchors` + `pre_update_validation_gate` | anchors would become performative ceremony rather than real orientation aids |
| `Result Contract` | `needs dogfood trace` | 5 | `cycle_id` + `what_changed` + `next_action` + `unresolved_items` | cycle frequency is low and lessons alone remain sufficient |
| `Approval` | `draft only` | 6 | `approval_policy` + `approval_identity` | the project is single-owner and does not yet produce meaningful approval/denial traces |

## Reading Rule

Use the matrix in this order:

1. check whether the profile is `adopt now`, `needs dogfood trace`, or `draft only`
2. check the minimal adoption contract
3. check the “do not use when” condition before adding the profile

## Current Interpretation

The matrix implies:

- `Drift` and `Track Map` are the strongest near-term candidates
- `Lineage`, `Consistency`, and `Result Contract` need real cycle evidence before broader adoption
- `Approval` remains the most conditional and easiest to over-apply

## Boundary Rule

No profile moves upward in status without either:

- repeated real project use, or
- a clear reduction in session cost, ambiguity, or regression risk

This is the core discipline that `v0.2.1` is meant to add.
