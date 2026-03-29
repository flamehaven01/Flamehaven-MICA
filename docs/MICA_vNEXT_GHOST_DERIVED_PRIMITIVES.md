# MICA vNext — Ghost-Derived Primitives

Status:
- forward-looking design note
- not a release spec
- intended to identify which Ghost-like operational primitives are worth importing into future MICA evolution

---

## 1. Why This Document Exists

`MICA v0.1.9` established a stable memory contract.

`v0.2.0` opened a candidate profile branch.

`v0.2.1` added triage and adoption discipline.

The next question is not simply:

`what more can be added?`

The better question is:

`which external operational ideas are strong enough to harden MICA without collapsing its boundary as a memory-layer protocol?`

Ghost is useful here because it frames agent memory not as a clever retrieval trick, but as part of a **workspace substrate**.

That does not mean MICA should become Ghost.
It means MICA can selectively absorb a few good primitives.

---

## 2. Boundary Rule

MICA must **not** absorb:

- database lifecycle management
- workspace provisioning
- search engine implementation
- sandbox execution orchestration
- “everything is postgres” as a requirement

Those are substrate concerns.

MICA may absorb only those ideas that strengthen:

- memory invocation
- temporal interpretation
- mutation discipline
- conflict awareness
- orientation quality

This is the core guardrail for `vNext`.

---

## 3. Primitive 1 — Temporal Memory Semantics

### What Ghost highlights

One of the strongest ideas in the Ghost/Memory Engine framing is:

`memory is not just a flat store; it is queryable across time`

The key value is not “vector DB versus SQL.”
The key value is that memory can answer:

- what was true then
- when it changed
- what superseded what

### What MICA should absorb

MICA should consider a thin temporal layer such as:

- `state_as_of`
- `valid_from`
- `valid_to`
- `superseded_by`

These do **not** require a database.
They can exist as semantics in archive, lineage, or result structures.

### Why this matters

This would let MICA answer not only:

- what the current project memory is

but also:

- when an old memory state stopped being authoritative

That is a real upgrade in governance clarity.

---

## 4. Primitive 2 — Fork-Before-Risk Memory Mutation

### What Ghost highlights

Ghost treats risky work as something that should happen on a forked database first.

The useful pattern is:

- branch
- test
- keep or discard

### What MICA should absorb

MICA should consider a thin mutation discipline such as:

- draft memory update
- validate
- promote or discard

This could remain file-based:

- `draft` lesson/result artifact
- validation outcome
- promotion into archive only after coherence checks

### Why this matters

This would make major MICA updates less brittle without turning MICA into a runtime orchestration engine.

---

## 5. Primitive 3 — Shared Memory Conflict Awareness

### What Ghost highlights

Ghost is strong wherever multiple agents or multiple sessions can interact with shared state.

That highlights a real problem:

- conflicting updates
- stale assumptions
- unsignaled invalidation of prior state

### What MICA should absorb

MICA should consider a lightweight conflict layer such as:

- `conflict_notice`
- `stale_assumption`
- `superseded_claim`
- `shared_memory_collision`

This does not require distributed locking.
It only requires that important conflicts can be named and remembered.

### Why this matters

Even file-based memory systems eventually face this problem once several sessions or actors interact with the same project memory.

---

## 6. Primitive 4 — Perception Snapshot Anchoring

### What Ghost and related discussion highlight

The comments around Ghost point to a real failure pattern:

- agents think and plan before they really perceive the workspace

This means memory quality is often limited by bad orientation, not just bad storage.

### What MICA should absorb

MICA should consider a thin pre-invocation orientation layer such as:

- `recent_changes_anchor`
- `workspace_snapshot_ref`
- `environment_state_hint`

These would not be a full environment crawler.
They would be just enough structure to say:

- what changed recently
- what surface is likely to matter first

### Why this matters

This would improve the quality of what MICA asks a session to load first, especially in projects where file/state drift is common.

---

## 7. Primitive 5 — Retrieval Primitive Separation

### What Ghost highlights

Ghost makes it clear that storage, search, and temporal recall can be very powerful substrate primitives.

### What MICA should preserve

MICA should **not** become the retrieval engine.

Instead, it should stay responsible for:

- final invocation policy
- selection discipline
- escalation / downgrade logic

The principle should be:

- substrate handles primitive retrieval
- MICA handles final memory relevance and packaging

### Why this matters

Without this boundary, MICA risks becoming a second substrate and losing portability.

---

## 8. Candidate vNext Directions

If MICA moves beyond `v0.2.1`, the strongest Ghost-derived directions appear to be:

1. `temporal semantics`
2. `fork-before-risk mutation discipline`
3. `shared memory conflict awareness`
4. `perception snapshot anchoring`

These are stronger candidates than importing:

- database lifecycle patterns
- platform-specific provisioning assumptions
- infrastructure-specific search internals

---

## 9. Recommended Order

Recommended order for future exploration:

1. `temporal semantics`
2. `fork-before-risk mutation discipline`
3. `perception snapshot anchoring`
4. `shared memory conflict awareness`

Rationale:

- temporal semantics strengthens current archive/lineage logic directly
- mutation discipline strengthens safe update behavior
- perception anchoring improves orientation quality
- shared conflict awareness is valuable, but usually appears after broader multi-actor adoption

---

## 10. What vNext Should Not Become

`vNext` should not be interpreted as:

- “make MICA more like a database”
- “make MICA substrate-aware in a hard-coded way”
- “replace Ghost”
- “replace files-first memory”

The better reading is:

`make MICA a stronger cross-substrate governance layer by importing a few good operational primitives`

That keeps the architecture clean:

- substrate remains replaceable
- governance remains portable

---

## 11. Final Judgment

Ghost is valuable to MICA not because it proves that Postgres is the answer, but because it exposes several strong operational primitives:

- time-aware memory
- fork-before-risk updates
- shared-state conflict awareness
- perception-linked workspace state

These are the parts worth carrying forward.

If `MICA vNext` absorbs them carefully, it can become more robust without ceasing to be what makes it useful:

`a portable, file-centered memory governance protocol rather than a workspace engine`
