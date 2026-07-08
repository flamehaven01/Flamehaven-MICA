# MICA v0.2.9 Memory-First Architecture Draft

## Purpose

This draft is retained as memory-first groundwork for `v3.0.0`.
It explores deeper substrate layers, but those layers are subordinate to MICA's invocation-first contract and should not be mistaken for the project's primary identity.

This draft defines the next concrete shape for teams that want MICA to be more than a
portable archive plus playbook package.

The governing idea is simple:

- current MICA treats `archive` and `playbook` as the package body
- memory-first MICA treats them as governed exports from a deeper memory substrate

This is the closest honest evolution path toward the structure demonstrated by
`agentmemory`, while preserving what MICA is uniquely good at:

- truthful package contracts
- promotion discipline
- provenance-aware exports
- portable cross-repo loading

## Design stance

The earlier v0.2.9 blueprint says:

> v0.2.9 is not the release that makes MICA a general memory engine.

That remains true for the shipping governance slice.
But if the goal is to build the next real substrate, the right move is not to discard that
slice. The right move is to invert the package hierarchy:

- `sessions`, `observations`, `memories`, `recall`, `slots`, and `graph` become first-class
- `archive` and `playbook` become derived, governed, export-grade surfaces

## What MICA lacks today

Compared with a memory-native system, current MICA is still thin in four areas:

1. It does not treat session capture as a first-class artifact.
2. It does not treat memory objects as the package center of gravity.
3. It does not expose slots or graph relations as loadable contract layers.
4. It validates promotion well, but it does not yet define the persistent memory substrate
   that feeds promotion.

## What MICA should preserve

Memory-first does not mean copying another repository's product shape.
MICA should keep three differentiators:

1. A portable `mica.yaml` contract that other repositories can load without guessing paths.
2. Hard boundaries between raw memory, reviewed lesson, and exported invariant truth.
3. Honest runtime state reporting so memory degradation does not silently masquerade as truth.

## Canonical memory-first package shape

```text
repo/
  mica.yaml
  memory/
    mica.sessions.jsonl
    mica.observe.jsonl
    mica.memories.jsonl
    mica.recall.jsonl
    mica.slots.json
    mica.graph.jsonl
    mica_archive.json
    mica_playbook.md
```

This is the minimum useful structure.

If a repo is larger, domain islands can be added later:

```text
repo/
  mica.yaml
  memory/
    mica.sessions.jsonl
    mica.observe.jsonl
    mica.memories.jsonl
    mica.recall.jsonl
    mica.slots.json
    mica.graph.jsonl
    exports/
      core.mica_archive.json
      core.mica_playbook.md
      biology.mica_archive.json
      biology.mica_playbook.md
```

## Layer model

### Primary operational layers

- `sessions`: session lifecycle and actor boundaries
- `observations`: append-only raw evidence stream
- `memories`: normalized durable memory objects
- `recall`: what was surfaced, to whom, and why
- `slots`: current stable working facts and handles
- `graph`: relations across memories, sessions, and exported truths

### Derived governed layers

- `archive_export`: promoted institutional memory
- `playbook_export`: human-readable operating doctrine

The critical shift is that archive and playbook are no longer assumed to be authored first.
They are exported from memory plus governance.

## Proposed `mica.yaml` contract

```yaml
mica_spec: "0.2.9"
mode: memory_first

memory_policy:
  primary_store: memory/
  session_capture: true
  observation_append_only: true
  memory_exports_required: true
  slot_projection_enabled: true
  graph_projection_enabled: true

flow_policy:
  enabled: true
  required: false

promotion_policy:
  candidate_to_lesson_requires:
    - source_event
    - observed_at_utc
    - project_scope
    - operator_review
  candidate_to_binding_requires:
    - origin_episode
    - supporting_event_ids
    - operator_review
    - trust_tier_not_opaque

layers:
  - id: sessions
    kind: sessions
    path: memory/mica.sessions.jsonl
    loading_hint: on_demand

  - id: observe
    kind: observations
    path: memory/mica.observe.jsonl
    loading_hint: always

  - id: memories
    kind: memories
    path: memory/mica.memories.jsonl
    loading_hint: on_demand

  - id: recall
    kind: recall
    path: memory/mica.recall.jsonl
    loading_hint: on_demand

  - id: slots
    kind: slots
    path: memory/mica.slots.json
    loading_hint: always

  - id: graph
    kind: graph
    path: memory/mica.graph.jsonl
    loading_hint: on_demand

  - id: archive_export
    kind: archive
    path: memory/mica_archive.json
    loading_hint: always

  - id: playbook_export
    kind: playbook
    path: memory/mica_playbook.md
    loading_hint: always
```

## Artifact contracts

Companion schema drafts in this repository:

- `mica.sessions.schema.json`
- `mica.observe.schema.json`
- `mica.memories.schema.json`
- `mica.recall.schema.json`
- `mica.slots.schema.json`
- `mica.graph.schema.json`

### `mica.sessions.jsonl`

Purpose:

- define the session envelope that observations belong to
- carry actor, repository, and task metadata

Minimum fields:

- `schema_version`
- `session_id`
- `opened_at_utc`
- `closed_at_utc`
- `project_scope`
- `actors`
- `source`
- `session_hash`

### `mica.observe.jsonl`

Purpose:

- remain the raw evidence stream
- preserve redacted but referentially stable provenance

Minimum fields:

- `schema_version`
- `event_id`
- `timestamp_utc`
- `session_id`
- `hook`
- `scope`
- `summary`
- `redaction`
- `trust_tier`
- `source_system`
- `event_hash`
- `prev_event_hash`

### `mica.memories.jsonl`

Purpose:

- hold durable memory objects created from one or more observations
- separate raw evidence from memory synthesis

Minimum fields:

- `schema_version`
- `memory_id`
- `created_at_utc`
- `updated_at_utc`
- `kind`
- `status`
- `project_scope`
- `summary`
- `source_event_ids`
- `source_session_ids`
- `trust_basis`
- `promotion_stage`
- `slot_refs`
- `graph_refs`

Suggested `kind` values:

- `fact`
- `lesson`
- `decision`
- `task_state`
- `constraint`
- `binding_candidate`

### `mica.recall.jsonl`

Purpose:

- record what was surfaced and whether it went to a human or an agent

Minimum fields:

- `schema_version`
- `recall_id`
- `timestamp_utc`
- `target`
- `memory_ids`
- `candidate_ids`
- `session_id`
- `reason`
- `policy_snapshot`

Required `target` values:

- `operator_review`
- `agent_context`

### `mica.slots.json`

Purpose:

- provide fast stable handles for currently important state

Minimum shape:

```json
{
  "schema_version": "mica.slots.v1",
  "slots": [
    {
      "slot_id": "active_goal",
      "value_ref": "mem_00042",
      "updated_at_utc": "2026-07-07T15:00:00Z",
      "stability": "volatile"
    }
  ]
}
```

Suggested slot classes:

- active goal
- active branch
- current invariant set
- blocked reason
- next operator decision

### `mica.graph.jsonl`

Purpose:

- carry relations that are expensive to reconstruct every time

Minimum fields:

- `schema_version`
- `edge_id`
- `from_ref`
- `to_ref`
- `relation`
- `created_at_utc`
- `source_event_ids`

Suggested relation values:

- `supports`
- `contradicts`
- `supersedes`
- `depends_on`
- `belongs_to_session`
- `exported_as`

## Operational pipeline

Memory-first MICA should run in this order:

1. Capture session metadata into `mica.sessions.jsonl`.
2. Append redacted but referentially stable evidence into `mica.observe.jsonl`.
3. Consolidate evidence into `mica.memories.jsonl`.
4. Project stable working state into `mica.slots.json`.
5. Project relations into `mica.graph.jsonl`.
6. Record recall events into `mica.recall.jsonl`.
7. Export governed truth into `mica_archive.json` and `mica_playbook.md`.

This keeps the memory substrate primary and the archive/playbook secondary.

Repository status:

- `tools/mica_memory.py` now provides the first minimal export utility for this step
- `tools/mica_memory.py synthesize-memories` now promotes raw observations into deterministic `candidate_memory` records
- `tools/mica_memory.py refresh-projections` now rebuilds `mica.slots.json` and `mica.graph.jsonl` from memory state
- `tools/mica_memory.py review-memory` now advances `candidate_memory` into `approved_lesson` or `bound_invariant_evidence` with explicit review metadata
- `tools/mica_memory.py materialize` now gives a consumer-facing rebuild entrypoint for `observations -> memories -> archive/playbook -> slots/graph`
- current export writes `memory_exports` into archive JSON, synthesizes `design_invariants` from `bound_invariant_evidence`, and regenerates playbook text from approved memories
- this is intentionally narrow: it preserves the export boundary without pretending that full retrieval or DI synthesis already exists

## Export rule

The export boundary is where MICA remains uniquely useful.

- not every memory becomes an archive fact
- not every recall-worthy item becomes a playbook lesson
- exported bindings still require provenance and review

This is how MICA avoids becoming a generic vector store with nice paperwork.

## Cross-repo loading rule

If another repository receives a memory-first MICA package, the consumer should:

1. load `mica.yaml`
2. always load `archive_export`, `playbook_export`, and `slots`
3. load `observations`, `memories`, `recall`, `graph`, and `sessions` only when the task
   or runtime mode needs them
4. refuse to infer missing paths from filenames
5. use `python tools/mica_memory.py <repo> materialize` when the package needs to rebuild its derived exports and projections locally

This preserves the portability rule already defined in the cross-repo adoption guide.

## Migration from current MICA packages

### Current shape

```text
repo/
  mica.yaml
  memory/
    mica_archive.json
    mica_playbook.md
```

### Memory-first target

```text
repo/
  mica.yaml
  memory/
    mica.sessions.jsonl
    mica.observe.jsonl
    mica.memories.jsonl
    mica.recall.jsonl
    mica.slots.json
    mica.graph.jsonl
    mica_archive.json
    mica_playbook.md
```

### Migration order

1. Add `mica.sessions.jsonl`.
2. Add append-only `mica.observe.jsonl`.
3. Add `mica.memories.jsonl` as the first durable synthesis layer.
4. Add `mica.slots.json` for stable current-state projection.
5. Add `mica.graph.jsonl` only after memory IDs are stable.
6. Keep `mica_archive.json` and `mica_playbook.md` as required exports during the whole migration.

## What should come from `agentmemory`

MICA should borrow structure, not identity.

The most relevant imports are:

- hook-driven observation capture
- provider and adapter boundaries
- memory object persistence
- slot projection
- graph retrieval surface
- recall telemetry
- evaluation harnesses after the substrate exists

## What should not be copied blindly

- product sprawl before the substrate contract stabilizes
- adapter breadth before trust tiers are enforced
- benchmark culture before export truth is stable
- UI or plugin surface before record shapes are frozen

## Recommended implementation order for a memory-first branch

### `P0-M`

- freeze `mode: memory_first`
- freeze layer kinds for `sessions`, `memories`, `slots`, and `graph`
- freeze export rule: archive/playbook remain mandatory derived layers

### `P1-M`

- add `mica.sessions.jsonl`
- add `mica.memories.jsonl`
- add `mica.slots.json`

### `P2-M`

- implement write/read paths for session and memory artifacts
- bind memories back to observation provenance

### `P3-M`

- implement export from memories to archive/playbook
- ensure exported facts cite source memory and source events

### `P4-M`

- add graph projection
- add retrieval and adapter maturity
- add evaluation and benchmark harnesses

## Short verdict

If MICA stays archive-first, it remains a strong governance package.
If MICA becomes memory-first with this structure, it can evolve toward a real operating
memory system without losing its portable contract and truth-discipline advantages.
