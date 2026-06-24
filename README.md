# MICA v0.2.8 — Binding Depth Edition

MICA (Memory Invocation & Context Archive) is a project memory package for AI maintenance work.

This repository tracks MICA from v0.2.6 onward. Legacy versions (v0.2.5 and earlier)
are in the `Legacy/` directory and are not tracked by git.

## What MICA is

Three assets form a MICA package:

| Asset | Format | Role |
|---|---|---|
| `mica.yaml` | YAML | Composition contract — what files exist and how the package is invoked |
| `*.mica.*.json` | JSON | Archive — institutional memory, design invariants, provenance |
| `*-playbook.*.md` | Markdown | Playbook — human + AI operating guide |

Tools validate and summarize the package at session start. MICA's job: locate the memory
package, load archive and playbook, activate against invariants, declare loaded state truthfully.

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
| `tools/mica_pct.py` | Package contract validator (PCT-001 through PCT-011) |
| `tools/mica_runtime.py` | Portable runtime summary / hook emitter |

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
| [mica-v0.2.4-archive-di-binding.schema.json](mica-v0.2.4-archive-di-binding.schema.json) | Archive DI binding schema (v0.2.4, superseded) |

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
