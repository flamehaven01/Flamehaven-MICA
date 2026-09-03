# MICA v3.0.0 Context Continuity Upgrade Plan

Status: architecture proposal
Target: post-v0.2.9 groundwork, pre-v3.0.0 release decision
Primary identity: Memory Invocation & Context Archive

## 1. Decision

MICA remains an invocation and context-loading contract.

This plan does not turn MICA into an SDLC engine, an MCP gateway, a pull-request
reviewer, a deployment controller, or a monitoring platform. It adds a narrow
continuity layer that answers two related questions:

1. Which exact context bytes were selected and delivered for this invocation?
2. What bounded state should the next invocation receive from this one?

The proposed architecture has two parts:

- an **Invocation Capsule**, represented as a digest-bound projection of the
  existing invocation trace;
- an optional **Handoff Surface**, containing short-lived state and references
  required by the next invocation.

Governance, promotion, receipts, and lifecycle integrations remain supporting
mechanisms. They do not replace invocation as the top-level contract.

## 2. Why This Is Needed

The current invocation trace records surface roles such as `archive`,
`playbook`, and `slots`. That establishes which declared roles were resolved,
but not which exact bytes were selected. A surface may change while retaining
the same path and role.

The current agent guide also requires a session-end report, but that report has
no portable, bounded artifact that the next session can resolve through
`mica.yaml`. Consumer repositories have started solving this locally with
handoff documents, which demonstrates the need but leaves the contract
inconsistent between consumers.

The missing continuity is therefore:

```text
declared surfaces
  -> resolved surface bytes
  -> bounded invocation payload
  -> invocation evidence
  -> bounded session handoff
  -> next invocation
```

MICA should close this loop without owning the work performed between the two
invocations.

## 3. Reference Inputs and Authority Boundary

This plan is informed by two adjacent systems:

- Anthropic's AI-Native SDLC Playbook uses versioned artifacts as handoffs
  between intent, design, build, review, deployment, and maintenance.
- Flamehaven-MCP binds selected context, prepared changes, actions, and
  verification to hashes and runtime-originated receipts.

These are references, not authorities over MICA.

MICA may adopt digest binding, explicit handoff, and truthful state separation.
It must not import:

- a vendor-specific Claude lifecycle;
- MCP transport or gateway dependencies;
- repository mutation authority;
- PR merge or deployment authority;
- monitoring or incident-response execution;
- claims that an external receipt is trusted merely because it is referenced.

## 4. Goals

### G1. Bind invocation to exact surface versions

Record a canonical path, content digest, byte count, audience, and delivery
state for each selected surface.

### G2. Keep delivery claims truthful

Separate declaration, resolution, emission, and external acknowledgment. Never
claim that a model understood or obeyed content because bytes were emitted.

### G3. Preserve bounded continuity between sessions

Allow the next session to load a compact handoff containing references,
unresolved items, verification references, and required next surfaces.

### G4. Support lifecycle events without owning an SDLC

Permit intent, review, release, and incident artifacts to trigger MICA
invocation profiles while keeping their execution in consumer-owned systems.

### G5. Preserve existing consumers

Archive-first and current memory-first packages remain valid without a handoff
surface. Existing invocation records retain their original schema semantics.

## 5. Non-Goals

- Generating or approving `intent.md`, `spec.md`, or `plan.md`.
- Reviewing, approving, merging, or modifying pull requests.
- Deploying, rolling back, or managing production credentials.
- Polling metrics or operating a monitoring service.
- Replacing Git, issue trackers, CI, deployment systems, or MCP gateways.
- Persisting full conversations or tool transcripts.
- Turning referenced action receipts into MICA-issued attestations.
- Adding a general workflow DSL.
- Adding a new PCT before a consumer pilot demonstrates a recurring failure.

## 6. Core Architecture

### 6.1 Invocation Capsule

The Invocation Capsule is a logical projection of one invocation trace record.
It is not a second mandatory log in the initial implementation.

Conceptual shape:

```json
{
  "schema_version": "mica.invocation.v2",
  "invocation_id": "inv_20260903_0001",
  "session_id": "sess_20260903_0001",
  "timestamp_utc": "2026-09-03T03:00:00Z",
  "trigger": {
    "kind": "review",
    "ref": "git:commit-or-pr-reference"
  },
  "surface_evidence": [
    {
      "role": "archive",
      "path": "memory/mica_archive.json",
      "sha256": "sha256:...",
      "bytes": 4096,
      "audience": "agent_context",
      "delivery_state": "emitted"
    }
  ],
  "previous_handoff_ref": "memory/mica_handoff.json",
  "capsule_hash": "sha256:..."
}
```

The complete v2 record continues to carry the existing package, core, flow,
mode, pattern, surface-role, invariant, and freshness fields. The example shows
only the new continuity fields.

#### Capsule invariants

- `surface_evidence.path` is repository-relative and normalized with `/`.
- The digest is computed from the bytes selected for delivery, before delivery.
- Required surfaces are rechecked before emission to prevent resolve-to-emit
  drift.
- `operator_only` evidence cannot be labeled `agent_context`.
- `capsule_hash` covers trigger, surface evidence, session binding, and the
  relevant existing invocation fields.
- A null `session_id` remains valid for operator-side resolution but cannot be
  presented as evidence for an individually identified AI session.
- A capsule proves selected and recorded bytes, not semantic comprehension.

### 6.2 Delivery states

The following states are distinct and monotonic within one invocation:

| State | Meaning |
|---|---|
| `declared` | The surface appears in the composition contract. |
| `resolved` | Its path exists, is allowed, and its bytes were hashed. |
| `emitted` | A MICA adapter or hook reports that those bytes were sent to its output channel. |
| `acknowledged` | An external host confirms receipt using an independently supplied reference. |

`acknowledged` does not mean read, understood, followed, or verified. MICA
should not expose those stronger states without a future host-specific evidence
contract.

The existing `recorded` term continues to describe the existence of a valid
trace artifact, not a delivery state.

### 6.3 Handoff Surface

The Handoff Surface is optional, short-lived, and intentionally separate from
the durable archive.

Proposed default path:

```text
memory/mica_handoff.json
```

Conceptual shape:

```json
{
  "schema_version": "mica.handoff.v1",
  "handoff_id": "handoff_20260903_0001",
  "created_at_utc": "2026-09-03T04:00:00Z",
  "project_scope": "example-project",
  "source_invocation_id": "inv_20260903_0001",
  "state": "active",
  "artifact_refs": [
    {
      "kind": "review",
      "ref": "git:commit-or-pr-reference",
      "trust": "referenced"
    }
  ],
  "verification_refs": [],
  "candidate_memory_refs": [],
  "unresolved": ["release authorization remains pending"],
  "next_invocation": {
    "trigger_kind": "release",
    "required_surfaces": ["archive", "playbook", "handoff"]
  },
  "expires_at_utc": "2026-09-10T04:00:00Z",
  "prev_handoff_hash": "sha256:...",
  "handoff_hash": "sha256:..."
}
```

#### Handoff invariants

- The handoff contains references and bounded state, not a full transcript.
- Durable invariants and approved lessons remain in the archive or playbook.
- Unreviewed discoveries remain candidate references and cannot be promoted by
  the handoff writer.
- External receipts retain an explicit trust state such as `referenced`,
  `attested`, or `unverified`.
- A stale or superseded handoff is visible and cannot silently become current
  project truth.
- The handoff may be updated only through a consumer-declared update trigger
  and authority.

### 6.4 Composition role

The proposed optional layer is:

```yaml
layers:
  - id: handoff
    kind: handoff
    path: memory/mica_handoff.json
    loading_hint: session_start_only

invocation_protocol:
  agent_context_surfaces:
    - archive
    - playbook
    - handoff
```

Packages without active cross-session work should omit this layer. The handoff
must not become a mandatory empty file.

## 7. Lifecycle Touchpoint Profiles

Touchpoints are playbook profiles, not workflow-engine states.

| Profile | Consumer-owned trigger | MICA input | Handoff purpose |
|---|---|---|---|
| `INTENT_ACTIVATION` | intent created or accepted | intent reference, archive, playbook | Preserve active intent and unresolved questions. |
| `REVIEW_ACTIVATION` | review requested | plan/diff reference, invariants, approved lessons | Preserve findings and verification references. |
| `RELEASE_ACTIVATION` | release candidate created | release reference, runbook, operator-only evidence | Preserve authorization state, receipts, and residual risk. |
| `INCIDENT_REACTIVATION` | alert or incident accepted | incident reference, operational playbook | Preserve diagnosis references and candidate memory. |

Each consumer playbook profile must state:

- trigger and source-of-truth reference;
- required and optional surfaces;
- audience separation;
- expected external artifact;
- handoff update rule;
- failure behavior;
- authority that may close the touchpoint.

MICA validates invocation truth around a touchpoint. It does not validate that
the external lifecycle action itself was correct unless an explicit external
verification reference is supplied, and even then it reports the reference's
trust basis rather than manufacturing authority.

## 8. Runtime Behavior

### Session start

1. Resolve `mica.yaml`.
2. Select required surfaces for the invocation pattern and active touchpoint.
3. Resolve canonical paths and reject escapes or ambiguity.
4. Read and hash the exact selected bytes.
5. Recheck required inputs before emission.
6. Emit the bounded context through the selected adapter or hook.
7. Record the invocation trace and capsule hash.
8. Report declared, resolved, emitted, acknowledged, and recorded states
   separately.

### Session end

1. Reference the source invocation ID.
2. Record external artifacts and verification references without copying their
   full payloads.
3. Record unresolved items and the next required invocation surfaces.
4. Write candidate memory references without promotion.
5. Apply freshness and hash continuity.
6. Update the handoff only through declared consumer authority.

## 9. Failure Semantics

| Condition | Required behavior |
|---|---|
| Required surface missing before hashing | Invocation remains incomplete; do not emit a success capsule. |
| Surface changes between resolution and emission | Re-resolve or fail; do not reuse the earlier digest. |
| Operator-only surface enters agent context | Fail the invocation contract. |
| Manual command records only resolution | Do not label delivery `emitted`. |
| Handoff expired | Warn and exclude it unless the operator explicitly reactivates it. |
| Handoff references missing external evidence | Preserve the reference as `unverified`; do not invent a receipt. |
| Candidate memory is listed in handoff | Keep it candidate-only until the existing promotion path approves it. |
| Optional handoff is absent | Core invocation remains valid. |
| Required handoff is absent for a declared profile | Mark the touchpoint invocation incomplete without invalidating unrelated package modes. |

## 10. Implementation Plan

### P0 - Contract freeze

Deliverables:

- approve or reject the names `Invocation Capsule` and `Handoff Surface`;
- freeze delivery-state semantics;
- freeze the boundary between reference storage and external authority;
- define compatibility behavior for invocation v1 records;
- select one consumer pilot and one negative-control consumer.

Exit criteria:

- no statement implies model comprehension from delivery;
- no lifecycle action is owned by MICA;
- archive, playbook, handoff, candidate memory, and external receipts have
  non-overlapping responsibilities.

### P1 - Digest-bound invocation evidence

Candidate files:

- `mica.invocation.schema.json`;
- `tools/mica_runtime.py`;
- focused invocation fixtures and tests;
- invocation documentation.

Deliverables:

- introduce invocation schema v2 without rewriting v1 history;
- add trigger, surface evidence, and capsule hash;
- canonicalize cross-platform paths;
- record byte counts and audience;
- preserve truthful declared/resolved/recorded output.

Required negative tests:

- surface mutation between resolution and emission;
- operator-only audience overlap;
- invalid or duplicate surface paths;
- null-session overclaim;
- capsule hash mismatch;
- Windows/Linux path normalization.

### P2 - Optional handoff surface

Candidate files:

- `mica.handoff.schema.json`;
- `mica.yaml.schema.json` for optional `kind: handoff`;
- one minimal handoff template;
- focused fixtures and tests;
- consumer authoring guidance.

Deliverables:

- add the optional handoff layer role;
- validate bounded artifact and verification references;
- add freshness and hash continuity;
- keep handoff absence non-failing unless a consumer profile requires it;
- prohibit direct memory promotion through handoff data.

### P3 - Playbook touchpoints

Deliverables:

- add the four lifecycle touchpoint templates to the consumer guide;
- document source-of-truth and working-copy distinctions;
- document update authority and failure behavior;
- demonstrate one intent/review path and one incident/re-entry path;
- keep vendor-specific hook, CI, PR, and deployment examples outside core
  semantics.

### P4 - Consumer experiment and promotion decision

Run a bounded pilot before adding a new PCT.

Compare the existing invocation contract with the context-continuity profile
using equivalent tasks. Measure:

- wrong or stale surface loading;
- ability to identify the exact invoked bytes;
- next-session recovery of active intent and unresolved state;
- context bytes and token overhead;
- false claims that context was loaded or verified;
- operator effort to maintain handoff state;
- duplicate or conflicting archive updates;
- cross-platform reproducibility.

Promotion criteria:

- the capsule detects at least one drift class not detectable by v1 traces;
- the handoff improves next-session recovery without becoming a second archive;
- default consumers incur no mandatory artifact or runtime cost;
- no new PCT is added unless the pilot reveals a stable, machine-detectable
  contract failure.

If these criteria are not met, retain the touchpoint material as consumer
guidance and do not promote the schema or runtime changes.

## 11. Compatibility and Migration

- `mica.invocation.v1` records remain valid historical artifacts.
- v2 writers do not rewrite existing JSONL records.
- archive-first packages may use capsule evidence without adopting memory-first
  storage.
- memory-first packages may reuse session IDs and candidate references but do
  not receive stronger authority from doing so.
- the handoff layer is opt-in.
- `mica_spec: 0.2.8` consumers remain valid under their existing contract.
- the final v3.0.0 release decision must define whether capsule evidence is
  required for all invocation-first packages or remains a capability profile.

## 12. Risks and Falsifiers

### R1. Artifact proliferation

Falsifier: consumers create handoffs that duplicate archive, playbook, issue
tracker, and full session logs.

Mitigation: keep capsule data inside invocation trace and make the handoff a
short reference surface with explicit size and freshness guidance.

### R2. False delivery assurance

Falsifier: users interpret `emitted` or `acknowledged` as proof that the model
read or obeyed the content.

Mitigation: prohibit `read`, `understood`, and `complied` as core delivery
states and keep recorded trace status separate.

### R3. Governance drift

Falsifier: MICA begins authorizing changes, validating PR quality, controlling
deployment, or monitoring production.

Mitigation: store external references and trust basis only; execution and
authorization remain consumer-owned.

### R4. Context overhead exceeds benefit

Falsifier: capsule and handoff bytes cost more than the stale-context failures
they prevent.

Mitigation: make handoff optional, cap it, and compare against a negative
control before promotion.

### R5. Receipt laundering

Falsifier: an arbitrary model-authored receipt reference is presented as
runtime attestation.

Mitigation: distinguish `referenced`, `attested`, and `unverified`; MICA never
upgrades trust without a declared adapter trust basis.

## 13. Release Boundary

This plan does not make v3.0.0 complete.

The context-continuity work may enter v3.0.0 only if it strengthens the existing
release declaration:

> truthful invocation of the right memory context at the session boundary

The release remains held if exact surface bytes cannot be identified, delivery
states are overstated, audience separation can be bypassed, or handoff data can
silently become archive truth.

## 14. Architecture Verdict

The preferred direction is a **Context Continuity Contract**, not an SDLC
module.

The Invocation Capsule makes session-start evidence byte-specific. The Handoff
Surface makes session-end state portable without becoming a second archive.
Intent, review, release, and incident events become optional invocation
touchpoints around that pair.

This is the smallest architecture that incorporates the useful lessons from
AI-native SDLC and governed MCP execution while keeping MICA faithful to its
name and original purpose.
