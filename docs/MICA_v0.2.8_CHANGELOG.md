# MICA v0.2.8 Changelog

## Release: Binding Depth Edition

v0.2.8 adds binding quality signals — distinguishing real incident-grounded bindings
from doctrinal prose, checking violation_count coherence, and detecting stale archives.
No PCT verdicts break existing packages; all new signals are WARN or INFO.

---

## Changes

### tools/mica_core.py

| Change | Detail |
|---|---|
| `MICA_CANONICAL_VERSION` | New constant `"0.2.8"` used by PCT-006 lag check |
| `_EPISODE_PATTERNS` | New module-level compiled patterns for doctrinal detection |
| `_parse_version()` | New helper: parses `"0.2.8"` → `(0, 2, 8)` |
| PCT-006 lag check | WARN when declared mica_spec is >= 2 versions behind `MICA_CANONICAL_VERSION` |
| PCT-010 doctrinal WARN | After PASS/WARN/FAIL: additional WARN if bound origin_episode has no episode code, version ref, or date pattern |
| PCT-010 coherence WARN | After PASS: WARN if `violation_count > 0` but `last_triggered` is empty |
| PCT-012 new | Archive freshness check: WARN when `operation_meta.last_updated` exceeds `di_policy.max_archive_age_days`. INFO when not configured. |
| `import re`, `from datetime import date` | Added at module level |
| Docstring | v0.2.8 notes added |

### mica.yaml.schema.json

| Change | Detail |
|---|---|
| `di_policy.max_archive_age_days` | New optional integer field (opt-in PCT-012) |
| `diPolicy.description` | v0.2.8 mention added |
| Top-level description | v0.2.8 mention added |
| `mica_spec` examples | Bumped to `["0.2.8", "0.2.7", "0.2.6"]` |

### fixtures/ (new)

| Fixture | Scenario | Expected result |
|---|---|---|
| `doctrinal_binding/` | Critical DIs with generic prose binding (no EXP-/version/date) | PCT-010 PASS + PCT-010 WARN (doctrinal). CLOSED. |
| `stale_archive/` | `max_archive_age_days=90`, `last_updated=2020-01-01` | PCT-012 WARN. CLOSED. |
| `violation_count_incoherent/` | `violation_count=3` + `last_triggered=""` | PCT-010 WARN (coherence). CLOSED. |

### tests/test_pct_fixtures.py

| Change | Detail |
|---|---|
| `_any_warn()` helper | New: returns True if any result for a check_id has WARN status |
| `test_doctrinal_binding_warns_but_closed` | New |
| `test_stale_archive_pct012_warns_but_closed` | New |
| `test_violation_count_incoherent_warns_but_closed` | New |
| Total tests | 7 (v0.2.7) → 10 (v0.2.8) |

---

## What did NOT change

- HARD_FAIL_CHECKS (PCT-012 is WARN only; not added to the set)
- CLOSED CONTRACT definition
- PCT-001 through PCT-009 behavior (existing verdicts unchanged)
- PCT-010 existing PASS/WARN/FAIL logic for unbound DIs
- PCT-011 behavior
- `mica.yaml` format (additive: `di_policy.max_archive_age_days` is optional)
- Archive JSON format
