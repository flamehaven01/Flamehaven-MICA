# MICA

Current stable tag: `v0.2.8` (`Binding Depth Edition`)
Current declaration tag: `v3.0.0-declaration` (invocation-first floor freeze; non-release milestone)
Current implementation milestone: `v3.0.0-invocation-truth` (resolved-versus-recorded runtime truth and consumer kit; non-release milestone)
Current floor: invocation-first runtime truth, with `v0.2.9` drafts retained as groundwork and cross-repository adoption continuing in consuming repositories

MICA (Memory Invocation & Context Archive) is a project memory package for AI maintenance work.

This repository tracks MICA from v0.2.6 onward. Legacy versions (v0.2.5 and earlier)
are in the `Legacy/` directory and are not tracked by git.

## Release Status

| Track | Status | Notes |
|---|---|---|
| Stable | `v0.2.8` | Latest release tag and current tool banner version |
| Declaration | `v3.0.0-declaration` | Invocation-first floor freeze; not a stable release |
| Implementation milestone | `v3.0.0-invocation-truth` | PCT/runtime truthfulness and consumer authoring kit; not a stable release |
| Draft groundwork | `v0.2.9` | Unreleased blueprint, PCT drafts, memory-first schemas, and helper tooling |
| Intended reset | `v3.0.0` | Invocation-first MICA: truthful context loading, session activation, and auditable invoked-state declaration |

From this point, the preferred next step is not more MICA-internal expansion.
The preferred next step is helping other repositories consume the invocation contract cleanly.

## What MICA is

MICA is primarily an invocation and context-loading contract.
Its primary job is to ensure that the right memory surfaces are loaded at session start,
that the session activates against the right invariants, and that runtime output states
truthfully what was actually invoked.

Archive, playbook, governance checks, and memory-first machinery exist to support that goal.
They are important, but they are not the center of the system.

Three assets form the minimal MICA package surface:

| Asset | Format | Role |
|---|---|---|
| `mica.yaml` | YAML | Composition contract — what files exist and how the package is invoked |
| `*.mica.*.json` | JSON | Archive — institutional memory, design invariants, provenance |
| `*-playbook.*.md` | Markdown | Playbook — human + AI operating guide |

Tools validate and summarize the package at session start. `mica_pct.py` now also prints an `IVC-*` appendix when an invocation trace artifact is present. MICA's job: locate the memory
package, load the declared context surfaces, activate against invariants, and declare loaded state truthfully.

For invocation-first packages, runtime and hook output must foreground resolved surfaces and `Context`
before governance/supporting details. `MICA CONTRACT RESOLVED` means the declared surface files were
found; `Trace: recorded` is separate timestamped invocation provenance. A package that declares
`agent_context_surfaces` should declare `primary_pattern` explicitly; an omitted pattern remains a
compatibility WARN and defaults to `readme_protocol`. `invocation_protocol.operator_only_surfaces`
separates human-review surfaces that must not overlap agent context. Agent-context surfaces must be
session-start loaded, or `PCT-007` fails the package contract. When `operator_review` recall is joined
with session invocation trace, that trace should expose `operator_only_surfaces` as provenance rather than
as memory content.

The current v0.2.9 draft adds governance and memory-first machinery beneath that surface.
Those additions remain subordinate to the invocation contract and should not replace it as MICA's core.
This repository is being held at that invocation-first floor rather than continuing to add deeper internal validator layers.

## What v0.2.8 adds over v0.2.7

| Change | Impact |
|---|---|
| PCT-010 doctrinal WARN | Detects `origin_episode` with no episode code, version ref, or date — signals ungrounded binding |
| PCT-010 coherence WARN | `violation_count > 0` with empty `last_triggered` → data defect signal |
| PCT-012 new (opt-in) | `di_policy.max_archive_age_days` → WARN when archive is stale |
| PCT-006 version lag | WARN when `mica_spec` is >= 2 versions behind canonical `0.2.8` |
| `di_policy.max_archive_age_days` field | New optional `mica.yaml` field activating PCT-012 |
| 3 new fixtures | `doctrinal_binding`, `stale_archive`, `violation_count_incoherent` |

No existing package breaks. All new signals are WARN or INFO. CLOSED CONTRACT definition unchanged.

## What v0.2.7 added over v0.2.6

| Change | Impact |
|---|---|
| `COMPACT_MODE` formally defined | No-mica.yaml intentional deployment distinguished from pre-migration `LEGACY_MODE` |
| `di_policy.namespace_mode` field | Declares DI ID convention: `sequential`, `domain_namespaced`, or `legacy_inv` |
| `mica-v0.2.7-archive-di-binding.schema.json` | Extended DI ID pattern: supports `DI-EQA-001`, `DI-BIO-003`, `INV-009` |
| `docs/MICA_v0.2.7_RUNTIME_PROTOCOL.md` | Full formal deployment model: modes, PCT matrix, invocation hierarchy, core boundary |

## Package Structure

| Component | Format | Role |
|---|---|---|
| `mica.yaml` | YAML | Composition contract |
| `*.mica.*.json` | JSON | Archive / institutional memory |
| `*-playbook.*.md` | Markdown | Human + AI operating guide |

Tools:

| File | Role |
|---|---|
| `tools/mica_core.py` | Shared PCT judgment and YAML loading |
| `tools/mica_pct.py` | Package contract validator (PCT-001 through PCT-012) |
| `tools/mica_runtime.py` | Portable runtime summary / hook emitter |
| `tools/mica_invocation.py` | Standalone validator for `mica.invocation.jsonl` provenance artifacts |
| `tools/mica_memory.py` | Memory-first read/write utility for sessions, memories, graph edges, and slot projections |

Fixtures:

| Directory | Purpose |
|---|---|
| `fixtures/valid_bound_di/` | PCT-010 PASS scenario |
| `fixtures/unbound_critical_di/` | PCT-010 WARN scenario (CLOSED preserved) |
| `fixtures/dead_lesson_ref/` | PCT-011 WARN scenario |
| `fixtures/hook_output_violations_only/` | Hook output filter demo |
| `fixtures/binding_required_fail/` | PCT-010 FAIL scenario (v0.2.6) |
| `fixtures/compact_mode/` | COMPACT_MODE: no mica.yaml, pct=LEGACY expected (v0.2.7) |
| `fixtures/domain_namespaced_di/` | DI-EQA-xxx / DI-BIO-xxx, CLOSED CONTRACT (v0.2.7) |

## Quick Start

```bash
# Validate a project
python tools/mica_pct.py [project_root]

# Runtime summary
python tools/mica_runtime.py [project_root] --format text
python tools/mica_runtime.py [project_root] --format hook

# Standalone invocation trace validator
python tools/mica_invocation.py [trace_file_or_project_root]
# reports the standalone invocation schema path and validates the trace artifact

# Memory-first utility
python tools/mica_memory.py [project_root] paths
python tools/mica_memory.py [project_root] dump slots
python tools/mica_memory.py [project_root] synthesize-memories
python tools/mica_memory.py [project_root] refresh-projections
python tools/mica_memory.py [project_root] review-memory --memory-id mem.obs.obs_2001 --record-file review.json
python tools/mica_memory.py [project_root] export
python tools/mica_memory.py [project_root] materialize

# Bound invariant evidence now contributes synthesized archive design_invariants during export
# materialize = synthesize candidate memories + export archive/playbook + rebuild slots/graph

# Run fixture tests
python -m pytest tests/ -v
```

## Development

```bash
pip install -r requirements-dev.txt
pytest -v
ruff check tools/ tests/
```

## DI Namespace Modes (v0.2.7)

Add to `mica.yaml` under `di_policy`:

```yaml
di_policy:
  namespace_mode: domain_namespaced   # or: sequential (default) | legacy_inv
  critical_binding_required: true     # optional: escalates PCT-010 to FAIL
```

Supported DI ID forms:

| Form | Example | Mode |
|---|---|---|
| `DI-NNN` | `DI-001` | `sequential` (default) |
| `DI-[DOMAIN]-NNN` | `DI-EQA-001`, `DI-BIO-003` | `domain_namespaced` |
| `INV-NNN` | `INV-009` | `legacy_inv` (grandfathered) |

## Deployment Modes

| Mode | Condition | pct= |
|---|---|---|
| `INVOCATION_MODE` | `mica.yaml` present | CLOSED or INCOMPLETE |
| `COMPACT_MODE` | No `mica.yaml`, intentional | LEGACY (correct, non-defective) |
| `LEGACY_MODE` | No `mica.yaml`, pre-migration | LEGACY (upgrade recommended) |
| `INACTIVE` | Nothing detected | INACTIVE |

## Document Map

| Document | Role |
|---|---|
| [README.md](README.md) | Entry document (this file) |
| [fixtures/README.md](fixtures/README.md) | Fixture map and expected outputs |

Schemas:

| Document | Role |
|---|---|
| [mica.yaml.schema.json](mica.yaml.schema.json) | mica.yaml schema |
| [mica-v0.2.7-archive-di-binding.schema.json](mica-v0.2.7-archive-di-binding.schema.json) | Archive DI binding schema (v0.2.7) |
| [mica.sessions.schema.json](mica.sessions.schema.json) | Session envelope schema draft for v0.2.9 memory-first packages |
| [mica.invocation.schema.json](mica.invocation.schema.json) | Invocation provenance schema draft for independently validating `mica.invocation.jsonl` artifacts |
| [mica.observe.schema.json](mica.observe.schema.json) | Observation record schema draft for v0.2.9 flow plane |
| [mica.memories.schema.json](mica.memories.schema.json) | Durable memory record schema draft for v0.2.9 memory-first packages |
| [mica.candidates.schema.json](mica.candidates.schema.json) | Candidate registry schema draft for v0.2.9 flow plane |
| [mica.recall.schema.json](mica.recall.schema.json) | Recall trace schema draft for v0.2.9 flow plane |
| [mica.slots.schema.json](mica.slots.schema.json) | Stable slot projection schema draft for v0.2.9 memory-first packages |
| [mica.graph.schema.json](mica.graph.schema.json) | Memory graph edge schema draft for v0.2.9 memory-first packages |

v0.2.9 draft docs:

| Document | Role |
|---|---|
| [docs/MICA_v0.2.9_EVOLUTION_BLUEPRINT.md](docs/MICA_v0.2.9_EVOLUTION_BLUEPRINT.md) | Blueprint for governed memory flow layer above external memory engines |
| [docs/MICA_v0.2.9_EXECUTION_PLAN.md](docs/MICA_v0.2.9_EXECUTION_PLAN.md) | P0-P4 phased execution plan for the v0.2.9 blueprint |
| [docs/PCT-013_v0.2.9_SPEC.md](docs/PCT-013_v0.2.9_SPEC.md) | Static flow check spec for observation coherence when flow is enabled |
| [docs/PCT-014_v0.2.9_SPEC.md](docs/PCT-014_v0.2.9_SPEC.md) | Recall trace coverage spec for active flow recall surfaces |
| [docs/PCT-015_v0.2.9_SPEC.md](docs/PCT-015_v0.2.9_SPEC.md) | Promotion provenance spec for approved lessons and bound evidence |
| [docs/PCT-017_v0.2.9_SPEC.md](docs/PCT-017_v0.2.9_SPEC.md) | Runtime injection safety spec for unapproved candidates |
| [docs/PCT-018_v0.2.9_SPEC.md](docs/PCT-018_v0.2.9_SPEC.md) | Runtime telemetry completeness spec for joinable flow traces |
| [docs/MICA_v0.2.9_RUNTIME_STATUS_CONTRACT.md](docs/MICA_v0.2.9_RUNTIME_STATUS_CONTRACT.md) | Core/Flow reporting contract for truthful runtime output |
| [docs/MICA_CROSS_REPO_ADOPTION_GUIDE.md](docs/MICA_CROSS_REPO_ADOPTION_GUIDE.md) | Packaging and handoff guide for making other repositories MICA-capable |
| [docs/MICA_v0.2.9_MEMORY_FIRST_ARCHITECTURE.md](docs/MICA_v0.2.9_MEMORY_FIRST_ARCHITECTURE.md) | Draft structure for evolving MICA from governed exports into a memory-first substrate |
| [docs/MICA_CONSUMER_AUTHORING_GUIDE.md](docs/MICA_CONSUMER_AUTHORING_GUIDE.md) | How maintainers and AI agents author and operate an invocation-first consumer package |
| [docs/MICA_INVOCATION_RECOVERY_PLAN.md](docs/MICA_INVOCATION_RECOVERY_PLAN.md) | Recovery plan for restoring invocation and context loading as the primary MICA objective |
| [docs/MICA_v3.0.0_DECLARATION.md](docs/MICA_v3.0.0_DECLARATION.md) | Declaration of the intended v3.0.0 invocation-first reset and release boundary |



v0.2.9 draft validator examples:

```text
python tools/mica_pct.py fixtures/flow_observation_valid
PCT-013 [PASS] memory\mica.observe.jsonl parseable and hash-chain coherent (2 records)
```

```text
python tools/mica_pct.py fixtures/flow_candidates_broken_provenance
PCT-015 [FAIL] cand_00044: unknown source_event_ids ['obs_missing_999']
Overall: INCOMPLETE
```

```text
python tools/mica_pct.py fixtures/flow_recall_enabled_missing_trace
PCT-014 [WARN] recall enabled but mica.recall.jsonl missing
PCT-009 [PASS] package complete. closed contract verified.
```

```text
python tools/mica_runtime.py fixtures/flow_recall_agent_context_violation --format text
Core      : INCOMPLETE
Flow      : FLOW_DEGRADED
Recall    : PASS
Telemetry : PASS
Promotion gate: FAIL
Reason    : candidate cand_00042 entered agent_context while operator_review.state=pending
```

```text
python tools/mica_pct.py fixtures/flow_recall_agent_context_violation
PCT-018 [PASS] memory\mica.recall.jsonl joins cleanly with candidates, observations, and invocation trace
```

Memory-first starter contract:

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

v0.2.8 docs:
| Document | Role |
|---|---|
| [docs/MICA_v0.2.8_CHANGELOG.md](docs/MICA_v0.2.8_CHANGELOG.md) | Release delta from v0.2.7 |
| [docs/MICA_v0.2.8_RELEASE_NOTES.md](docs/MICA_v0.2.8_RELEASE_NOTES.md) | Release rationale |
| [docs/MICA_v0.2.8_MIGRATION_GUIDE.md](docs/MICA_v0.2.8_MIGRATION_GUIDE.md) | v0.2.7 to v0.2.8 migration |
| [docs/MICA_v0.2.8_APPROVAL_NOTE.md](docs/MICA_v0.2.8_APPROVAL_NOTE.md) | v0.2.8 approval rationale |
| [CHANGELOG.md](CHANGELOG.md) | All-versions changelog summary |

Carried forward from v0.2.7:

| Document | Role |
|---|---|
| [docs/MICA_v0.2.7_RUNTIME_PROTOCOL.md](docs/MICA_v0.2.7_RUNTIME_PROTOCOL.md) | Full deployment model and PCT matrix |
| [docs/MICA_v0.2.7_CHANGELOG.md](docs/MICA_v0.2.7_CHANGELOG.md) | v0.2.7 release delta |
| [docs/MICA_v0.2.7_RELEASE_NOTES.md](docs/MICA_v0.2.7_RELEASE_NOTES.md) | v0.2.7 release rationale |
| [docs/MICA_v0.2.7_MIGRATION_GUIDE.md](docs/MICA_v0.2.7_MIGRATION_GUIDE.md) | v0.2.6 to v0.2.7 migration |
| [docs/MICA_v0.2.7_APPROVAL_NOTE.md](docs/MICA_v0.2.7_APPROVAL_NOTE.md) | v0.2.7 approval rationale |
| [templates/mica-v0.2.7-archive-bootstrap.json](templates/mica-v0.2.7-archive-bootstrap.json) | Bootstrap template (v0.2.7) |

Carried forward from v0.2.6:

| Document | Role |
|---|---|
| [docs/MICA_v0.2.6_CHANGELOG.md](docs/MICA_v0.2.6_CHANGELOG.md) | v0.2.6 release delta |
| [docs/MICA_v0.2.6_RELEASE_NOTES.md](docs/MICA_v0.2.6_RELEASE_NOTES.md) | v0.2.6 release rationale |
| [docs/MICA_v0.2.6_MIGRATION_GUIDE.md](docs/MICA_v0.2.6_MIGRATION_GUIDE.md) | v0.2.5 to v0.2.6 migration |
| [docs/MICA_v0.2.6_APPROVAL_NOTE.md](docs/MICA_v0.2.6_APPROVAL_NOTE.md) | v0.2.6 approval rationale |
| [docs/MICA_v0.2.5_TO_v0.2.6_COMPARISON.md](docs/MICA_v0.2.5_TO_v0.2.6_COMPARISON.md) | Structured comparison |
| [docs/MICA_v0.2.5_RUNTIME_PROTOCOL.md](docs/MICA_v0.2.5_RUNTIME_PROTOCOL.md) | Guard surface vs enforcement |
| [docs/MICA_v0.2.4_COMPOSITION_CONTRACT.md](docs/MICA_v0.2.4_COMPOSITION_CONTRACT.md) | mica.yaml field reference |
| [docs/MICA_v0.2.4_EXAMPLES.md](docs/MICA_v0.2.4_EXAMPLES.md) | Canonical mica.yaml examples |
| profiles/ | DI binding, hook output profiles |
