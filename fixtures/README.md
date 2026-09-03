# MICA Fixtures

Minimal test packages for validating PCT behavior, runtime output, and v0.2.9 flow-schema drafts.
Each fixture is a self-contained project root. Run tools against them directly.

## Usage

```bash
python tools/mica_pct.py fixtures/valid_bound_di
python tools/mica_pct.py fixtures/unbound_critical_di
python tools/mica_pct.py fixtures/dead_lesson_ref
python tools/mica_pct.py fixtures/binding_required_fail
python tools/mica_pct.py fixtures/compact_mode
python tools/mica_pct.py fixtures/domain_namespaced_di
python tools/mica_pct.py fixtures/doctrinal_binding
python tools/mica_pct.py fixtures/stale_archive
python tools/mica_pct.py fixtures/violation_count_incoherent
python tools/mica_pct.py fixtures/implicit_primary_pattern
python tools/mica_runtime.py fixtures/implicit_primary_pattern --format text
python tools/mica_runtime.py fixtures/hook_output_violations_only --format hook
python tools/mica_pct.py fixtures/invocation_capsule_v2
python tools/mica_invocation.py fixtures/invocation_capsule_v2/memory/mica.invocation.jsonl

# v0.2.9 flow fixtures
cat fixtures/flow_observation_valid/memory/mica.observe.jsonl
cat fixtures/flow_candidates_pending/memory/mica.candidates.json
cat fixtures/flow_candidates_approved_lesson/memory/mica.candidates.json
cat fixtures/flow_recall_operator_review_safe/memory/mica.recall.jsonl
cat fixtures/flow_recall_agent_context_violation/memory/mica.recall.jsonl
python tools/mica_pct.py fixtures/memory_first_minimal
python tools/mica_memory.py fixtures/memory_first_minimal materialize
# missing-trace fixture intentionally has no mica.recall.jsonl
```

## Verdict axes

Results report on three axes. Only `Contract` decides `CLOSED CONTRACT`.

| Axis | Question | Checks |
|---|---|---|
| `Contract` | Did the declared memory reach this session, and did anything reach it that should not have? | PCT-001/002/003/004/007/008/017 |
| `Archive` | Is the memory content well formed? | PCT-005/006/010/011/012 |
| `Flow` | Is the memory-authoring pipeline coherent? | PCT-013/014/015/018 |

`mica_pct.py` exits 1 on a contract failure only. `--strict` widens it to every axis.

| Fixture | Contract | Archive | Flow | exit |
|---|---|---|---|---|
| `binding_required_fail` | CLOSED | **FAILED** | N/A | 0 (1 with `--strict`) |
| `flow_candidates_broken_provenance` | CLOSED | OK | **FAILED** | 0 (1 with `--strict`) |
| `flow_recall_agent_context_violation` | **INCOMPLETE** | OK | OK | 1 |
| `compact_mode` | **INCOMPLETE** | N/A | N/A | 1 |
| `invocation_capsule_v2` | CLOSED | OK | N/A | 0 |
| `memory_first_minimal` | CLOSED | OK | N/A | 0 |

The first two used to report `INCOMPLETE`. Ungrounded DI bindings and broken
promotion provenance are real problems, but they do not mean the session failed
to receive its memory, so they no longer break the contract.

## Fixture Map

| Fixture | Version | PCT-010 | PCT-011 | PCT-012 | Contract | Notes |
|---|---|---|---|---|---|---|
| `valid_bound_di/` | v0.2.5 | PASS | INFO | INFO | CLOSED | All critical DIs have real binding |
| `unbound_critical_di/` | v0.2.5 | WARN | INFO | INFO | CLOSED | Critical DI lacks binding; no `critical_binding_required` |
| `dead_lesson_ref/` | v0.2.5 | PASS | WARN | INFO | CLOSED | `lesson_ref` declared but file missing |
| `hook_output_violations_only/` | v0.2.5 | WARN | INFO | INFO | CLOSED | Hook output filter demo |
| `binding_required_fail/` | v0.2.6 | FAIL | INFO | INFO | CLOSED | `critical_binding_required=true` + unbound DI; fails the **Archive** axis |
| `compact_mode/` | v0.2.7 | - | - | - | INCOMPLETE | No mica.yaml; PCT-001 FAIL. Runtime reports `LEGACY`; COMPACT is intent, not detection |
| `domain_namespaced_di/` | v0.2.7 | PASS | INFO | INFO | CLOSED | DI-EQA-xxx/DI-BIO-xxx + `critical_binding_required` |
| `doctrinal_binding/` | v0.2.8 | PASS+WARN | INFO | INFO | CLOSED | Bound but doctrinal `origin_episode` |
| `stale_archive/` | v0.2.8 | INFO | INFO | WARN | CLOSED | `max_archive_age_days=90`, last_updated=`2020-01-01` |
| `violation_count_incoherent/` | v0.2.8 | PASS+WARN | INFO | INFO | CLOSED | `violation_count=3` + empty `last_triggered` |
| `flow_observation_valid/` | v0.2.9 draft | - | - | - | N/A | Hash-chain observation seed for `mica.observe.jsonl` schema |
| `flow_candidates_pending/` | v0.2.9 draft | - | - | - | N/A | Pending candidate seed for `mica.candidates.json` schema |
| `flow_candidates_approved_lesson/` | v0.2.9 draft | - | - | - | N/A | Approved lesson seed with non-null review provenance |
| `flow_candidates_broken_provenance/` | v0.2.9 draft | - | - | - | CLOSED | Missing source-event provenance; fails the **Flow** axis |
| `flow_recall_operator_review_safe/` | v0.2.9 draft | - | - | - | CLOSED | Pending candidate surfaced only to `operator_review`; `PCT-017` PASS |
| `flow_recall_agent_context_violation/` | v0.2.9 draft | - | - | - | INCOMPLETE | Pending candidate injected into `agent_context`; `PCT-017` FAIL (contract axis) |
| `flow_recall_enabled_missing_trace/` | v0.2.9 draft | - | - | - | CLOSED | Recall enabled but trace missing; `PCT-014` WARN and `Flow=FLOW_DEGRADED` |
| `flow_recall_incomplete_telemetry/` | v0.2.9 draft | - | - | - | CLOSED | Recall trace exists but is not fully joinable; `PCT-018` WARN and `Flow=FLOW_DEGRADED` |
| `memory_first_minimal/` | v0.2.9 draft | - | - | - | CLOSED | Minimal memory-first portable package with sessions/observe/memories/slots/graph exports present and explicit `agent_context` surfaces |
| `implicit_primary_pattern/` | v0.2.8 | - | - | - | CLOSED | Declared context with implicit `readme_protocol`; PCT-007 WARN and trace absent |
| `invocation_capsule_v2/` | v3.0.0 P1 | PASS | INFO | INFO | CLOSED | Digest-bound `mica.invocation.v2` capsule; committed trace is byte-bound to its surfaces |
| `handoff_surface/` | v0.2.9 | PASS | INFO | INFO | CLOSED | Handoff surface with `default`/`resume` profiles; `resume` delivers it, `default` does not |
| `memory_profiles/` | v3.0.0 Origin P1/P2 | PASS | INFO | INFO | CLOSED | `default`/`review`/`incident` profiles select different surfaces, and slice the playbook |


## Expected Outputs

### implicit_primary_pattern

```text
PCT-007 [WARN] primary_pattern omitted; runtime default readme_protocol applies
[MICA CONTRACT RESOLVED] implicit-primary-pattern v0.2.8
Pattern   : readme_protocol (defaulted)
Trace     : absent
```
### valid_bound_di

```text
PCT-010 [PASS] all 2 critical DIs have binding
PCT-011 [INFO] no lesson_ref fields declared; nothing to validate
Overall: CLOSED CONTRACT
```

### unbound_critical_di

```text
PCT-010 [WARN] critical DIs missing binding.origin_episode: ['DI-001']
              -- set di_policy.critical_binding_required: true to escalate to FAIL
PCT-011 [INFO] no lesson_ref fields declared; nothing to validate
Overall: CLOSED CONTRACT
```

### dead_lesson_ref

```text
PCT-010 [PASS] all 1 critical DIs have binding
PCT-011 [WARN] binding.lesson_ref dead links: [('DI-001', 'memory/lessons/missing.md')]
Overall: CLOSED CONTRACT
```

### binding_required_fail

```text
PCT-010 [FAIL] critical DIs missing binding.origin_episode: ['DI-001']
              -- di_policy.critical_binding_required is true

Contract : CLOSED
Archive  : FAILED
Flow     : N/A

Overall: CLOSED CONTRACT
```

The opt-in escalation still produces a FAIL. Since Origin P0 it fails the
archive axis rather than the contract: an ungrounded binding is a memory-quality
problem, not evidence that the session failed to receive its memory. `--strict`
exits 1 on it.

### compact_mode

This fixture sits on three distinct axes. Keep them separate when reading its output.

| Axis | Value | Determined by |
|---|---|---|
| PCT result | `INCOMPLETE` | `mica_pct.py` -- `mica.yaml` absent, so PCT-001/009 FAIL |
| Runtime detection | `LEGACY_MODE` | `mica_runtime.py` -- no composition contract to resolve |
| Deployment intent | `COMPACT_MODE` | Operator declaration only; **not machine-detectable** |

```text
PCT-001 [FAIL] mica.yaml missing (checked root + memory/)
PCT-009 [FAIL] package incomplete. failing checks: ['PCT-001']
Overall: INCOMPLETE
```

```bash
python tools/mica_runtime.py fixtures/compact_mode --format text
```

```text
Mode      : legacy
Pattern   : legacy (legacy)
PCT       : LEGACY
```

Both tool outputs are correct. The third axis is the one to be careful about:
an absent `mica.yaml` cannot distinguish an intentional archive/playbook-only
deployment (COMPACT_MODE) from an unmigrated package (LEGACY_MODE). The runtime
therefore reports `LEGACY`, and does not claim `COMPACT`. Treating absence as
evidence of intent would misclassify every unmigrated package as deliberate.

### invocation_capsule_v2 (v3.0.0 P1)

Digest-bound invocation evidence. The committed trace records the exact bytes of
each loaded surface, so editing a surface without regenerating the trace is
detected rather than silently accepted.

```bash
python tools/mica_invocation.py fixtures/invocation_capsule_v2/memory/mica.invocation.jsonl
```

```text
IVC-000 [PASS] invocation schema present
IVC-001 [PASS] invocation trace present
IVC-002 [PASS] parseable invocation trace (1 records)
IVC-003 [PASS] invocation trace shape matches supported schema expectations
IVC-004 [PASS] invocation surfaces are internally coherent
IVC-005 [PASS] capsule inv_... digests match the current surface bytes
```

`IVC-005` re-hashes the surfaces on disk and compares them to the newest
capsule. It runs only when a project root is given, since a bare trace file
provides no root to resolve relative paths against, and it is skipped entirely
when `IVC-003` or `IVC-004` failed -- an unsound record must not be able to
direct the validator at a file. Recorded paths are re-resolved against the root
before being opened, so a `../` path or a symlink leaving the package is refused
rather than read.

Three states are reported separately and must not be collapsed:

| Axis | Meaning | Where |
|---|---|---|
| Artifact validity | Is the record itself well-formed and coherent? | `IVC-003` / `IVC-004` |
| Continuity freshness | Do the recorded digests still match disk? | `IVC-005` |
| Runtime trace state | What should a session be told? | `mica_runtime.py` `Trace:` |

Editing a surface without regenerating the trace makes `IVC-005` WARN, the
validator verdict `VALID INVOCATION TRACE (stale evidence)` with exit 0, and
the runtime `Trace: stale`. The artifact stays valid because the record was
true when written; only its continuity with the current surfaces is broken.
The runtime resolves the trace against the project root precisely so it cannot
report `recorded` while the validator reports drift.

Recorded evidence:

| role | path | audience | delivery_state |
|---|---|---|---|
| `archive` | `memory/mica_archive.json` | `agent_context` | `resolved` |
| `playbook` | `memory/mica_playbook.md` | `agent_context` | `resolved` |

`delivery_state` is `resolved` because the bytes were hashed, not delivered.
Only a MICA adapter that actually writes to an output channel may record
`emitted`, and no state in this vocabulary claims the model read or understood
the content.

### memory_profiles (v3.0.0 Origin P1)

Selection, not just verification. The same package gives a session different
memory depending on the profile it requests.

```bash
python tools/mica_runtime.py fixtures/memory_profiles --format text
python tools/mica_runtime.py fixtures/memory_profiles --profile review --format text
```

```text
Profile   : default
Resolved  : archive, playbook

Profile   : review
Resolved  : archive, playbook, lessons
```

The `incident` profile slices the playbook to a single section:

```bash
python tools/mica_runtime.py fixtures/memory_profiles --profile incident --format text
```

| Profile | playbook delivered | of file |
|---|---|---|
| `default` | whole file | 100% |
| `review` | `Review`, `Invariants` | 57% |
| `incident` | `Incident Runbook` | 47% |

The capsule digest covers the slice, so drift is scoped to what the session
actually received: editing the `Onboarding` section does not affect a `review`
capsule, while editing `Review` does.

Requesting a profile that is not declared, a profile naming a surface that is
not a declared layer, or a section that does not exist, fails `PCT-007` on the
contract axis. The session asked for memory the package cannot supply, which is
an invocation fault.

### domain_namespaced_di

```text
PCT-010 [PASS] all 3 critical DIs have binding
Overall: CLOSED CONTRACT
```

### doctrinal_binding (v0.2.8)

```text
PCT-010 [PASS] all 2 critical DIs have binding
PCT-010 [WARN] doctrinal binding (no episode code, version ref, or date): ['DI-001', 'DI-002']
              -- ground origin_episode in a real incident
Overall: CLOSED CONTRACT
```

### stale_archive (v0.2.8)

```text
PCT-012 [WARN] archive last_updated 2020-01-01 is NNNN days old (max_archive_age_days=90)
Overall: CLOSED CONTRACT
```

### violation_count_incoherent (v0.2.8)

```text
PCT-010 [PASS] all 1 critical DIs have binding
PCT-010 [WARN] violation_count > 0 but last_triggered empty: ['DI-001']
Overall: CLOSED CONTRACT
```

### hook_output_violations_only

```bash
python tools/mica_runtime.py fixtures/hook_output_violations_only --format hook
```

Expected output (3 critical DIs, only 2 have violation_count > 0, `max_di_lines: 2`):

```text
[MICA] hook-output-test v1.0.0 | mode=memory_injection | pattern=readme_protocol | DI=3crit/0high | pct=CLOSED | last=2026-05-19
[MICA:DI] DI-001(critical): first-violated-di [3x]
[MICA:DI] DI-002(critical): second-violated-di [1x]
```

DI-003 is suppressed because `di_filter=violations_only`, and the cap of 2 is reached after DI-002.


### flow_observation_valid (PCT-013)

```text
PCT-013 [PASS] memory\mica.observe.jsonl parseable and hash-chain coherent (2 records)
PCT-015 [INFO] memory\mica.candidates.json contains no approved or promoted artifacts requiring provenance validation
Overall: CLOSED CONTRACT
```

### flow_candidates_approved_lesson (PCT-015 PASS)

```text
PCT-013 [PASS] memory\mica.observe.jsonl parseable and hash-chain coherent (2 records)
PCT-015 [PASS] validated promotion provenance for 1 governed candidate(s)
Overall: CLOSED CONTRACT
```

### flow_candidates_broken_provenance (PCT-015 FAIL)

```text
PCT-013 [PASS] memory\mica.observe.jsonl parseable and hash-chain coherent (2 records)
PCT-015 [FAIL] cand_00044: unknown source_event_ids ['obs_missing_999']
PCT-009 [PASS] declared memory surfaces reached the session; contract closed

Contract : CLOSED
Archive  : OK
Flow     : FAILED

Overall: CLOSED CONTRACT
```

Broken promotion provenance is an authoring-pipeline fault. Since Origin P0 it
fails the flow axis and leaves the invocation contract closed; the memory this
session needed still reached it. `--strict` exits 1 on the flow failure.

### flow_recall_operator_review_safe (PCT-017 PASS)

```text
PCT-014 [PASS] memory\mica.recall.jsonl provides recall trace coverage (1 records)
PCT-017 [PASS] memory\mica.recall.jsonl enforces approved-only agent_context injection
Overall: CLOSED CONTRACT
```

### flow_recall_agent_context_violation (PCT-017 FAIL)

```text
Core      : INCOMPLETE
Flow      : FLOW_DEGRADED
Recall    : PASS
Telemetry : PASS
Promotion gate: FAIL
Reason    : candidate cand_00042 entered agent_context while operator_review.state=pending
```

### flow_recall_enabled_missing_trace (PCT-014 WARN)

```text
PCT-014 [WARN] recall enabled but mica.recall.jsonl missing
PCT-017 [INFO] recall enabled but trace file absent; PCT-017 deferred until runtime trace exists
Overall: CLOSED CONTRACT
```

### flow_recall_incomplete_telemetry (PCT-018 WARN)

```text
PCT-014 [PASS] memory\mica.recall.jsonl provides recall trace coverage (1 records)
PCT-018 [WARN] record 1: session_id 'sess_unlinked_999' not linked to observation stream; record 1: missing source_event_ids for candidate cand_00042

Runtime summary should surface this as `Telemetry : WARN` while leaving `Core` unchanged.
Overall: CLOSED CONTRACT
```

### memory_first_minimal

```text
PCT-004 [PASS] memory_first coherence ok
PCT-013 [INFO] flow disabled; observation coherence not required
PCT-015 [INFO] flow disabled; promotion provenance not required
Overall: CLOSED CONTRACT
```
