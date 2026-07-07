# MICA v0.2.9 Execution Plan

## Status

Execution plan for the v0.2.9 blueprint.
This document translates the blueprint into phased implementation work.

Companion design document:

- `docs/MICA_v0.2.9_EVOLUTION_BLUEPRINT.md`

---

## Planning rule

v0.2.9 is not the release that makes MICA a general memory engine.
It is the release that makes MICA capable of governing an observation-to-promotion pipeline.

This execution plan therefore prioritizes:

- evidence capture
- provenance-preserving redaction
- candidate promotion control
- state honesty
- minimum enforceable PCTs

It deliberately postpones:

- large retrieval systems
- broad adapter ecosystems
- benchmark-driven auto-gating
- viewer polish

---

## Phase map

| Phase | Goal | Output class | Priority |
|---|---|---|---|
| `P0` | Freeze invariants and trust boundaries | Spec + schema decisions | Critical |
| `P1` | Ship observation and candidate artifacts | Data structures + parsers | High |
| `P2` | Ship promotion enforcement and first PCTs | Validation + runtime state | High |
| `P3` | Add recall trace and review/context separation | Operational auditability | Medium |
| `P4` | Expand adapters, metrics, and replay discipline | Optional flow maturity | Medium / deferred edge |

---

## P0 — Invariants And Trust Boundary Freeze

### Objective

Lock the rules that must not drift before implementation starts.

### Why P0 exists

Without P0, downstream implementation will make incompatible assumptions about:

- redaction behavior
- imported observation trust
- flow-state semantics
- retention safety
- what promotion is allowed to consume

### Deliverables

- final field contract for `mica.observe.jsonl`
- final field contract for `mica.candidates.json`
- normative meaning of `enabled` vs `required`
- trust-tier policy: `native`, `attested`, `opaque`
- attestation minimum for imported observations
- redaction identity rule: payload may change, IDs / timestamps / hashes may not
- GC pinning rule for promoted references
- static vs runtime PCT split
- `FLOW_DEGRADED` transition triggers

### Frozen decisions

- `opaque` observations may not become Stage 3 binding evidence
- `event_hash` is mandatory on every observation
- redaction may not break `source_event_ids` referential integrity
- `FLOW_DEGRADED` does not invalidate Core when `required=false`
- `mica.candidates.json` is versioned at the document root via mandatory `schema_version`

### Attested minimum

An imported observation may be labeled `attested` only if all of the following exist:

- `source_system`
- `source_event_ref`
- `imported_at_utc`
- `event_hash`
- integrity validation result recorded at import time

Additionally, at least one of the following must hold:

- signed import envelope verified by a trusted key
- append-only hash-chain continuity verified from the upstream segment
- explicit allowlisted adapter with a deterministic import contract and integrity check

If none of these conditions hold, the observation is `opaque`, not `attested`.

### Exit criteria

- all normative record shapes are frozen for v0.2.9
- promotion ladder rules are frozen
- runtime state transition rules are frozen
- no unresolved contradiction remains between redaction, provenance, retention, trust tier, and promotion

### Out of scope

- retrieval strategy
- recall ranking policy
- benchmark thresholds

---

## P1 — Observation And Candidate Foundation

### Objective

Create the first concrete flow artifacts and make them parseable, append-only, and promotion-safe.

### Deliverables

- `mica.observe.jsonl` schema and parser
- `mica.candidates.json` schema and parser
- append-only writer contract for observations
- candidate status model
- retention pin / tombstone model

### Required fields for observation MVP

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

### Required fields for candidates document MVP

Document root:

- `schema_version`
- `candidates`

Per candidate:

- `candidate_id`
- `stage`
- `source_event_ids`
- `claim`
- `target`
- `status`
- `risk`
- `trust_basis`
- `observed_at_utc`
- `project_scope`
- `operator_review`

### Required review metadata shape

`operator_review` must support at least:

- `state`
- `reviewed_by`
- `reviewed_at_utc`
- `decision_reason`

This is included in the MVP because Stage 2 and Stage 3 promotion already depend on review provenance.

### Implementation notes

- start with a narrow hook set
- prefer low-noise events over maximal event capture
- do not add retrieval output to candidate schema yet
- keep candidate generation provenance-first, not LLM-cleverness-first
- preserve future compatibility by versioning the candidates document from day one

### Exit criteria

- observation files can be written and re-read deterministically
- candidate registry can represent pending and reviewed states without schema migration
- redaction rules are enforced at write time
- GC pinning can be computed from candidate references

### Risks to avoid

- turning observation logs into unbounded noisy dumps
- storing secrets in summary fields
- inventing retrieval metadata too early

---

## P2 — Promotion Enforcement And First PCTs

### Objective

Enforce the governance boundary so that useful memory cannot silently become governed truth.

### Deliverables

- `promotion_policy` enforcement logic
- runtime status split: `Core` vs `Flow`
- first static/runtime PCT implementation set
- failure semantics for unapproved injection

### PCT set for v0.2.9 shipping core

- `PCT-013`: observation log present, parseable, and internally coherent when flow is enabled
- `PCT-015`: approved lessons / bound evidence cite valid source-event provenance
- `PCT-017`: no unapproved candidate enters `agent_context` when policy forbids it

### PCT-013 minimum validation scope

- every line parses
- every line has a supported `schema_version`
- `event_hash` recomputes successfully
- `prev_event_hash` links are coherent within a stream segment
- duplicate `event_id` values are rejected
- record ordering is deterministic within the validated segment

Timestamp monotonicity may be WARN-only if clock skew is tolerated, but ordering coherence must still hold.

### Enforcement rules

- no Stage 2 or Stage 3 object without source-event trace
- no Stage 3 object from `opaque` trust-tier evidence
- no unapproved candidate injection into `agent_context`
- `FLOW_DEGRADED` is non-fatal unless `required=true`

### Runtime report target

PASS example:

```text
Core: CLOSED
Flow: FLOW_ENABLED
Observation: PASS
Candidates: 3 pending, 1 approved
Promotion gate: PASS
```

FAIL example:

```text
Core: CLOSED
Flow: FLOW_DEGRADED
Observation: PASS
Candidates: 2 pending, 1 approved
Promotion gate: FAIL
Reason: candidate cand_00042 entered agent_context while operator_review.state=pending
```

### Exit criteria

- failing promotion provenance is machine-detectable
- flow degradation is visible without corrupting core truth
- agent-context injection policy is enforceable and auditable
- first v0.2.9 packages can be judged honestly under enabled/required combinations

### Risks to avoid

- implementing promotion as a best-effort lint instead of a hard boundary
- collapsing flow failures into core failures by default
- making `PCT-017` non-blocking

---

## P3 — Recall Trace And Surface Separation

### Objective

Add auditable recall traces without turning v0.2.9 into a retrieval-heavy release.

### Deliverables

- `mica.recall.jsonl` schema
- `target=operator_review|agent_context` separation
- trace records for injected or surfaced items
- `PCT-014` runtime check

### Required trace semantics

- every recall record has `schema_version`
- every recall record declares `target`
- operator review surfacing is allowed to include unapproved candidates
- agent-context injection is not allowed to include unapproved candidates under default policy

### Exit criteria

- operator review and agent-context events are distinguishable in telemetry
- `PCT-014` can detect missing trace coverage when recall is active
- trace records can point back to candidate IDs and source events

### Risks to avoid

- treating all recall as equivalent
- adding ranking logic before trace integrity exists
- requiring a viewer UI before trace format is stable

---

## P4 — Optional Flow Maturity

### Objective

Extend the flow plane once the promotion pipeline is already trustworthy.

### Candidate deliverables

- adapter declaration maturity (`PCT-016`)
- telemetry completeness checks (`PCT-018`)
- replay corpus format
- metrics reporting
- benchmark harness experiments
- stronger attestation modes for imported observations

### Metrics posture in P4

Metrics begin useful in v0.2.9, but deeper gating belongs here.

Priority metrics:

- `unapproved_injection_rate`
- `grounded_recall_rate`
- `false_recall_rate`
- `stale_recall_rate`
- `promotion_precision`
- `binding_trace_coverage`
- `closed_truth_preservation`

### Gate policy guidance

- keep `unapproved_injection_rate=0` as a hard rule
- treat broader quality metrics as report-first until labeling discipline exists
- do not auto-gate on weakly defined metrics before replay infrastructure is real

### Accepted risk carried from P1-P3

`PCT-016` is intentionally delayed. During P1-P3, packages may declare optional adapters that are not yet
subject to dedicated adapter-resolvability enforcement. This is acceptable only because:

- `required=false` optional adapters do not invalidate Core
- `opaque` trust-tier evidence is barred from Stage 3 promotion
- imported observations still need integrity metadata even before full adapter maturity

This is an explicit temporary risk, not an unnoticed omission.

### Exit criteria

- adapter trust is inspectable
- replay and evaluation artifacts are stable enough to compare runs
- metrics no longer act as decorative telemetry only

### Risks to avoid

- pulling P4 concerns into P1/P2 and delaying the first release
- conflating benchmark success with governance truth

---

## Accepted vs deferred audit guidance

### Accepted now

- redaction must preserve audit identity
- adapter trust boundary must be explicit
- static and runtime PCT tracks must be separated
- `enabled` and `required` must be distinct
- append-only streams need `schema_version`
- candidates document needs root-level versioning
- retention must not create dangling promotion references
- operator review and agent-context injection must be separated

### Deferred to later phases

- full hybrid retrieval policy
- benchmark thresholds as hard promotion gates
- large adapter marketplace
- replay leaderboard / polished viewer

The filter is relevance to the first governed shipping slice.

---

## Recommended immediate next actions

1. Write the `mica.observe.jsonl` schema draft.
2. Write the `mica.candidates.json` schema draft.
3. Draft the `PCT-013`, `PCT-015`, and `PCT-017` specification notes.
4. Add a minimal runtime status contract showing `Core` and `Flow` separately.

---

## Short verdict

> P0 through P4 are not equal slices of work. P0-P2 define whether v0.2.9 is a real
> governance release or just a memory-feature sketch. P3-P4 are important, but only after
> the observation-to-promotion boundary is already trustworthy.
