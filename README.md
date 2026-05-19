# MICA v0.2.6 — Binding Enforcement Edition

MICA (Memory Invocation & Context Archive) is a project memory package for AI maintenance work.

This repository tracks MICA from v0.2.6 onward. Legacy versions (v0.2.5 and earlier)
are in the `Legacy/` directory and are not tracked by git.

## What MICA is

Three assets form a MICA package:

| Asset | Format | Role |
|-------|--------|------|
| `mica.yaml` | YAML | Composition contract — what files exist and how the package is invoked |
| `*.mica.*.json` | JSON | Archive — institutional memory, design invariants, provenance |
| `*-playbook.*.md` | Markdown | Playbook — human + AI operating guide |

Tools validate and summarize the package at session start.

## What v0.2.6 adds over v0.2.5

| Change | Impact |
|--------|--------|
| `di_policy.critical_binding_required: true` | PCT-010 escalates from WARN to FAIL (opt-in) |
| PCT-010 added to `HARD_FAIL_CHECKS` | Contract breaks when flag is set and DIs are unbound |
| `fixtures/binding_required_fail/` | New fixture demonstrating PCT-010 FAIL |
| `tests/test_pct_fixtures.py` | 5 pytest tests covering all fixtures |
| `.github/workflows/ci.yml` | CI: pytest + ruff on Python 3.9, 3.11, 3.12 |
| `pyproject.toml` + `requirements-dev.txt` | Tooling config |
| `mica.yaml.schema.json` | `di_policy` block added |

Packages that do not set `critical_binding_required` behave identically to v0.2.5.

## Package Structure

| Component | Format | Role |
|-----------|--------|------|
| `mica.yaml` | YAML | Composition contract |
| `*.mica.*.json` | JSON | Archive / institutional memory |
| `*-playbook.*.md` | Markdown | Human + AI operating guide |

Tools:

| File | Role |
|------|------|
| `tools/mica_core.py` | Shared PCT judgment and YAML loading |
| `tools/mica_pct.py` | Package contract validator (PCT-001 through PCT-011) |
| `tools/mica_runtime.py` | Portable runtime summary / hook emitter |

Fixtures:

| Directory | Purpose |
|-----------|---------|
| `fixtures/valid_bound_di/` | PCT-010 PASS scenario |
| `fixtures/unbound_critical_di/` | PCT-010 WARN scenario (CLOSED preserved) |
| `fixtures/dead_lesson_ref/` | PCT-011 WARN scenario |
| `fixtures/hook_output_violations_only/` | Hook output filter demo |
| `fixtures/binding_required_fail/` | PCT-010 FAIL scenario (v0.2.6 new) |

## Quick Start

```bash
# Validate a project
python tools/mica_pct.py [project_root]

# Runtime summary
python tools/mica_runtime.py [project_root] --format text
python tools/mica_runtime.py [project_root] --format hook

# Run PCT fixture tests
python tools/mica_pct.py fixtures/valid_bound_di
python tools/mica_pct.py fixtures/unbound_critical_di
python tools/mica_pct.py fixtures/dead_lesson_ref
python tools/mica_pct.py fixtures/binding_required_fail
python tools/mica_runtime.py fixtures/hook_output_violations_only --format hook
```

## Development

```bash
pip install -r requirements-dev.txt
pytest -v
ruff check tools/ tests/
```

## Enabling Binding Enforcement

Add to `mica.yaml`:

```yaml
di_policy:
  critical_binding_required: true
```

Then run `python tools/mica_pct.py .` — PCT-010 will FAIL for any critical DI
without `binding.origin_episode`. Add binding blocks until CLOSED CONTRACT.

## Compatibility

- v0.2.6 is non-breaking over v0.2.5
- `mica.yaml` and archive format unchanged
- Packages without `di_policy` behave identically to v0.2.5
- `pct=` field in hook output may change from CLOSED to INCOMPLETE for packages
  that set `critical_binding_required: true` with unbound DIs — this is the intended behavior

## Document Map

| Document | Role |
|----------|------|
| [README.md](README.md) | Entry document (this file) |
| [MICA_v0.2.6_CHANGELOG.md](MICA_v0.2.6_CHANGELOG.md) | Release delta from v0.2.5 |
| [MICA_v0.2.6_RELEASE_NOTES.md](MICA_v0.2.6_RELEASE_NOTES.md) | Release rationale |
| [MICA_v0.2.6_MIGRATION_GUIDE.md](MICA_v0.2.6_MIGRATION_GUIDE.md) | v0.2.5 to v0.2.6 migration |
| [fixtures/README.md](fixtures/README.md) | Fixture map and expected outputs |

v0.2.6 docs:

| Document | Role |
|----------|------|
| [docs/MICA_v0.2.6_APPROVAL_NOTE.md](docs/MICA_v0.2.6_APPROVAL_NOTE.md) | v0.2.6 approval rationale |
| [docs/MICA_v0.2.5_TO_v0.2.6_COMPARISON.md](docs/MICA_v0.2.5_TO_v0.2.6_COMPARISON.md) | Structured comparison with v0.2.5 |
| [templates/mica-v0.2.6-archive-bootstrap.json](templates/mica-v0.2.6-archive-bootstrap.json) | Bootstrap template (v0.2.6) |

Carried forward from v0.2.5:

| Document | Role |
|----------|------|
| [MICA_v0.2.5_CHANGELOG.md](MICA_v0.2.5_CHANGELOG.md) | v0.2.5 release delta |
| [MICA_v0.2.5_RELEASE_NOTES.md](MICA_v0.2.5_RELEASE_NOTES.md) | v0.2.5 release rationale |
| [MICA_v0.2.5_RUNTIME_PROTOCOL.md](MICA_v0.2.5_RUNTIME_PROTOCOL.md) | Guard surface vs enforcement |
| [MICA_v0.2.5_MIGRATION_GUIDE.md](MICA_v0.2.5_MIGRATION_GUIDE.md) | v0.2.4 to v0.2.5 migration |
| [MICA_v0.2.4_COMPOSITION_CONTRACT.md](MICA_v0.2.4_COMPOSITION_CONTRACT.md) | mica.yaml field reference |
| [MICA_v0.2.4_EXAMPLES.md](MICA_v0.2.4_EXAMPLES.md) | Canonical mica.yaml examples |
| [MICA_v0.2.4_SELF_TEST_EXAMPLES.md](MICA_v0.2.4_SELF_TEST_EXAMPLES.md) | PCT-010/011 self-test examples |
| [mica.yaml.schema.json](mica.yaml.schema.json) | mica.yaml schema (v0.2.6: di_policy added) |
| [mica-v0.2.4-archive-di-binding.schema.json](mica-v0.2.4-archive-di-binding.schema.json) | Archive DI binding schema |
| [docs/MICA_v0.2.5_APPROVAL_NOTE.md](docs/MICA_v0.2.5_APPROVAL_NOTE.md) | v0.2.5 approval rationale |
| [docs/MICA_v0.2.4_TO_v0.2.5_COMPARISON.md](docs/MICA_v0.2.4_TO_v0.2.5_COMPARISON.md) | v0.2.4 to v0.2.5 comparison |
| [templates/mica-v0.2.5-archive-bootstrap.json](templates/mica-v0.2.5-archive-bootstrap.json) | Bootstrap template (v0.2.5) |
| profiles/ | DI binding, hook output, hook trigger, runtime portability profiles |
