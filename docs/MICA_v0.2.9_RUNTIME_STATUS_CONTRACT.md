# MICA v0.2.9 Runtime Status Contract

## Purpose

v0.2.9 introduces flow-plane machinery without letting optional flow failures masquerade as core truth failures.
This document fixes the reporting contract.

## Report split

Runtime output must report:

- `Core`
- `Flow`
- flow subchecks that matter to governance

## Core states

Allowed values:

- `CLOSED`
- `INCOMPLETE`
- `LEGACY`
- `INACTIVE`

Core state is derived from package contract truth, not from optional flow convenience.

## Flow states

Allowed values:

- `FLOW_OFFLINE`
- `FLOW_ENABLED`
- `FLOW_DEGRADED`

## State rules

- `FLOW_DEGRADED` must not invalidate `Core=CLOSED` when `flow_policy.required=false`
- `FLOW_DEGRADED` must escalate package truth only when `flow_policy.required=true`
- `FLOW_OFFLINE` is acceptable when flow is disabled
- `FLOW_ENABLED` means configured machinery is present and passing minimum health checks

## Minimum `FLOW_DEGRADED` triggers

At least one of:

- required observation artifact missing while flow is enabled
- configured adapter health check fails past the allowed retry budget
- recall trace required for active runtime checks but unavailable
- promotion enforcement cannot evaluate a configured hard gate

Package implementations may add stricter triggers, but may not weaken these.

## PASS example

```text
Core: CLOSED
Flow: FLOW_ENABLED
Observation: PASS
Candidates: 3 pending, 1 approved
Promotion gate: PASS
```

## FAIL example

```text
Core: CLOSED
Flow: FLOW_DEGRADED
Observation: PASS
Candidates: 2 pending, 1 approved
Promotion gate: FAIL
Reason: candidate cand_00042 entered agent_context while operator_review.state=pending
```
