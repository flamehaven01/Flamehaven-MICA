# MICA Changelog

All notable changes per version. Most recent first.
Full release notes and migration guides in `docs/`.

---

## v0.2.8 — Binding Depth Edition (2026-06-24)

**4 new PCT signals. No existing package breaks. All new signals are WARN or INFO.**

- **PCT-010 doctrinal WARN**: Detects `origin_episode` with no episode code (`EXP-xxx`), version ref, or date — signals ungrounded binding
- **PCT-010 coherence WARN**: `violation_count > 0` with empty `last_triggered` → data defect
- **PCT-012 new (opt-in)**: `di_policy.max_archive_age_days` in mica.yaml → WARN when archive is stale
- **PCT-006 version lag**: WARN when `mica_spec` is >= 2 versions behind canonical `0.2.8`
- `_EPISODE_PATTERNS`, `MICA_CANONICAL_VERSION`, `_parse_version()` added to mica_core.py
- `di_policy.max_archive_age_days` added to mica.yaml.schema.json
- 3 new fixtures: `doctrinal_binding`, `stale_archive`, `violation_count_incoherent`
- Tests: 7 → 10 (all GREEN)

→ [MICA_v0.2.8_CHANGELOG.md](docs/MICA_v0.2.8_CHANGELOG.md) | [MICA_v0.2.8_APPROVAL_NOTE.md](docs/MICA_v0.2.8_APPROVAL_NOTE.md)

---

## v0.2.7 — Frame Stabilization Edition (2026-06-24)

**Deployment model + DI namespace formalized. 19 drift docs removed.**

- **COMPACT_MODE** formally defined: intentional no-mica.yaml deployment vs pre-migration LEGACY_MODE
- **`di_policy.namespace_mode`**: `sequential` / `domain_namespaced` / `legacy_inv`
- **`mica-v0.2.7-archive-di-binding.schema.json`**: Extended DI ID pattern `^(DI|INV)(-[A-Z][A-Z0-9]*)?-\d+$`
- **`docs/MICA_v0.2.7_RUNTIME_PROTOCOL.md`**: Full deployment model, PCT matrix, invocation hierarchy
- 2 new fixtures: `compact_mode`, `domain_namespaced_di`
- Tests: 5 → 7 (all GREEN)
- 19 repo-governance drift docs deleted

→ [MICA_v0.2.7_CHANGELOG.md](docs/MICA_v0.2.7_CHANGELOG.md) | [MICA_v0.2.7_APPROVAL_NOTE.md](docs/MICA_v0.2.7_APPROVAL_NOTE.md)

---

## v0.2.6 — Binding Enforcement Edition (2026-05-xx)

**PCT-010 can now escalate from WARN to FAIL (opt-in).**

- `di_policy.critical_binding_required: true` in mica.yaml → PCT-010 FAIL for unbound critical DIs
- PCT-010 added to `HARD_FAIL_CHECKS`
- `tests/test_pct_fixtures.py`: 5 pytest tests covering all fixtures
- `.github/workflows/ci.yml`: pytest + ruff matrix (Python 3.9, 3.11, 3.12)
- `pyproject.toml` + `requirements-dev.txt` added
- New fixture: `binding_required_fail`

→ [MICA_v0.2.6_CHANGELOG.md](docs/MICA_v0.2.6_CHANGELOG.md) | [MICA_v0.2.6_APPROVAL_NOTE.md](docs/MICA_v0.2.6_APPROVAL_NOTE.md)

---

## v0.2.5

PCT-010/011 checks added. Fixtures introduced. DI binding schema (v0.2.4) extended to support `lesson_ref`.

→ [MICA_v0.2.5_CHANGELOG.md](docs/MICA_v0.2.5_CHANGELOG.md)

---

## v0.2.4

DI binding schema introduced. `binding.origin_episode` formalized. Hook output policy added.

→ [MICA_v0.2.4_APPROVAL_NOTE.md](docs/MICA_v0.2.4_APPROVAL_NOTE.md)
