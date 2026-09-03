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

## Fixture Map

| Fixture | Version | PCT-010 | PCT-011 | PCT-012 | Contract | Notes |
|---|---|---|---|---|---|---|
| `valid_bound_di/` | v0.2.5 | PASS | INFO | INFO | CLOSED | All critical DIs have real binding |
| `unbound_critical_di/` | v0.2.5 | WARN | INFO | INFO | CLOSED | Critical DI lacks binding; no `critical_binding_required` |
| `dead_lesson_ref/` | v0.2.5 | PASS | WARN | INFO | CLOSED | `lesson_ref` declared but file missing |
| `hook_output_violations_only/` | v0.2.5 | WARN | INFO | INFO | CLOSED | Hook output filter demo |
| `binding_required_fail/` | v0.2.6 | FAIL | INFO | INFO | INCOMPLETE | `critical_binding_required=true` + unbound DI |
| `compact_mode/` | v0.2.7 | - | - | - | INCOMPLETE | No mica.yaml; PCT-001 FAIL. Runtime reports `LEGACY`; COMPACT is intent, not detection |
| `domain_namespaced_di/` | v0.2.7 | PASS | INFO | INFO | CLOSED | DI-EQA-xxx/DI-BIO-xxx + `critical_binding_required` |
| `doctrinal_binding/` | v0.2.8 | PASS+WARN | INFO | INFO | CLOSED | Bound but doctrinal `origin_episode` |
| `stale_archive/` | v0.2.8 | INFO | INFO | WARN | CLOSED | `max_archive_age_days=90`, last_updated=`2020-01-01` |
| `violation_count_incoherent/` | v0.2.8 | PASS+WARN | INFO | INFO | CLOSED | `violation_count=3` + empty `last_triggered` |
| `flow_observation_valid/` | v0.2.9 draft | - | - | - | N/A | Hash-chain observation seed for `mica.observe.jsonl` schema |
| `flow_candidates_pending/` | v0.2.9 draft | - | - | - | N/A | Pending candidate seed for `mica.candidates.json` schema |
| `flow_candidates_approved_lesson/` | v0.2.9 draft | - | - | - | N/A | Approved lesson seed with non-null review provenance |
| `flow_candidates_broken_provenance/` | v0.2.9 draft | - | - | - | INCOMPLETE | Approved lesson seed with missing source-event provenance |
| `flow_recall_operator_review_safe/` | v0.2.9 draft | - | - | - | CLOSED | Pending candidate surfaced only to `operator_review`; `PCT-017` PASS |
| `flow_recall_agent_context_violation/` | v0.2.9 draft | - | - | - | INCOMPLETE | Pending candidate injected into `agent_context`; `PCT-017` FAIL |
| `flow_recall_enabled_missing_trace/` | v0.2.9 draft | - | - | - | CLOSED | Recall enabled but trace missing; `PCT-014` WARN and `Flow=FLOW_DEGRADED` |
| `flow_recall_incomplete_telemetry/` | v0.2.9 draft | - | - | - | CLOSED | Recall trace exists but is not fully joinable; `PCT-018` WARN and `Flow=FLOW_DEGRADED` |
| `memory_first_minimal/` | v0.2.9 draft | - | - | - | CLOSED | Minimal memory-first portable package with sessions/observe/memories/slots/graph exports present and explicit `agent_context` surfaces |
| `implicit_primary_pattern/` | v0.2.8 | - | - | - | CLOSED | Declared context with implicit `readme_protocol`; PCT-007 WARN and trace absent |
| `invocation_capsule_v2/` | v3.0.0 P1 | PASS | INFO | INFO | CLOSED | Digest-bound `mica.invocation.v2` capsule; committed trace is byte-bound to its surfaces |


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
Overall: INCOMPLETE CONTRACT
```

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
provides no root to resolve relative paths against. Editing a surface without
regenerating the trace turns it into a WARN and the verdict becomes
`VALID INVOCATION TRACE (stale evidence)` -- stale, not invalid, because the
record was true when it was written.

Recorded evidence:

| role | path | audience | delivery_state |
|---|---|---|---|
| `archive` | `memory/mica_archive.json` | `agent_context` | `resolved` |
| `playbook` | `memory/mica_playbook.md` | `agent_context` | `resolved` |

`delivery_state` is `resolved` because the bytes were hashed, not delivered.
Only a MICA adapter that actually writes to an output channel may record
`emitted`, and no state in this vocabulary claims the model read or understood
the content.

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
PCT-009 [FAIL] package incomplete. failing checks: ['PCT-015']
Overall: INCOMPLETE
```

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
