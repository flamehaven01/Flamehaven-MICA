# MICA v0.2.7 Changelog

## Release: Frame Stabilization Edition

v0.2.7 formalizes the MICA deployment model and DI namespace conventions that
emerged organically across four production deployments. No PCT behavior changes.
No format breaking changes.

---

## Changes

### docs/MICA_v0.2.7_RUNTIME_PROTOCOL.md (new)

| Item | Detail |
|---|---|
| Core boundary statement | Absorbed from abandoned CORE_BOUNDARY.md draft: "MICA is session-start memory contract, not repo governance" |
| Session entry states | FULL_MODE, COMPACT_MODE, LEGACY_MODE, INSERTION_MODE, INACTIVE — formally defined with condition and pct result |
| Detection order | Steps 1-3: locate markers, classify, behave |
| Invocation hierarchy | Natural / Guided / Forced tiers absorbed from abandoned INVOCATION_HIERARCHY.md draft |
| PCT applicability matrix | Which of PCT-001 to PCT-011 apply per deployment mode |
| DI namespace modes | `sequential`, `domain_namespaced`, `legacy_inv` — formal table with pattern and when-to-use |
| CLOSED CONTRACT definition | Hard rule on which HARD_FAIL checks must PASS; LEGACY is correct terminal for COMPACT |

### mica-v0.2.7-archive-di-binding.schema.json (new)

| Item | Detail |
|---|---|
| `id` pattern | Expanded from `^DI-\d+$` to `^(DI\|INV)(-[A-Z][A-Z0-9]*)?-\d+$` |
| Supported forms | `DI-001` (canonical), `DI-EQA-001` (domain-namespaced), `INV-009` (grandfathered) |
| Rejected forms | `DI-001-002` (digit-domain segment), `DI-eqa-001` (lowercase domain) |
| Supersedes | `mica-v0.2.4-archive-di-binding.schema.json` |

### mica.yaml.schema.json (edited)

| Change | Detail |
|---|---|
| `mica_spec` examples | Bumped to `["0.2.7", "0.2.6", "0.2.5"]` |
| `di_policy.namespace_mode` | New field: enum `sequential \| domain_namespaced \| legacy_inv`, default `sequential` |
| `di_policy` description | Updated to reference v0.2.7 DI binding schema |
| Top-level description | v0.2.7 mention added |

### tools/mica_core.py, mica_pct.py, mica_runtime.py

| Change | Detail |
|---|---|
| Docstrings | Version bumped to v0.2.7; COMPACT_MODE and namespace_mode notes added |
| No logic changes | All PCT verdicts, HARD_FAIL_CHECKS, and CLOSED CONTRACT behavior unchanged |

### fixtures/ (new)

| Fixture | Scenario | Expected result |
|---|---|---|
| `compact_mode/` | No mica.yaml, archive + playbook only | PCT-001 FAIL, PCT-009 FAIL, pct=LEGACY |
| `domain_namespaced_di/` | DI-EQA-xxx + DI-BIO-xxx, `critical_binding_required: true` | CLOSED CONTRACT, PCT-010 PASS |

### tests/test_pct_fixtures.py

| Change | Detail |
|---|---|
| `test_compact_mode_returns_pct001_fail_and_pct009` | New |
| `test_domain_namespaced_di_is_closed` | New |
| Total tests | 5 (v0.2.6) → 7 (v0.2.7) |

### docs/ (deletions)

| Deleted | Reason |
|---|---|
| `MICA_v0.2.7_CORE_REPO_TARGETS.md` | Repo governance drift — outside MICA core boundary |
| `MICA_v0.2.7_REPO_CONSISTENCY_RULEBOOK.md` | Repo governance drift |
| `MICA_v0.2.7_REPO_GOVERNANCE_POLICY.md` | Repo governance drift |
| `MICA_v0.2.7_REPO_PLAYBOOK.md` | Repo governance drift |
| `MICA_v0.2.8_CORE_BOUNDARY.md` | Content absorbed into RUNTIME_PROTOCOL.md |
| `MICA_v0.2.8_INVOCATION_HIERARCHY.md` | Content absorbed into RUNTIME_PROTOCOL.md |
| `MICA_v0.2.8_DEVTO_ARTICLE.md` | Marketing doc, not spec |
| `MICA_v0.2.8_GOVERNANCE_AUTOMATION_LOOP.md` | Repo governance drift |
| `MICA_v0.2.8_GOVERNANCE_HISTORY.md` | Repo governance drift |
| `MICA_v0.2.8_LINEAGE_AUDIT_*.md` | Analysis doc, not spec |
| `MICA_v0.2.8_REPORTING_PROTOCOL.md` | Repo governance drift |
| `MICA_v0.2.8_ROSETTASTONE_EXECUTION_MODEL.md` | Adjacent system, not MICA core |
| `MICA_v0.2.8_TRUSTED_GOVERNANCE_OVERRIDES.md` | Repo governance drift |
| `MICA_vNEXT_SESSION_REPORT_GATE_DESIGN.md` | Unvalidated design doc |
| `mica_evolution_and_tone_analysis.md` | Editorial, not spec |
| `mica_live_case_study_analysis.md` | Editorial, not spec |
| `mica_philosophical_and_reconstruction_analysis.md` | Editorial, not spec |
| `MICA_PRACTICAL_DEVTO_ARTICLE_NEW.md` | Marketing, not spec |
| Templates: `mica-v0.2.7-repo-governance-checklist.md` | Repo governance drift |
| Templates: `mica-v0.2.8-governance-cycle-*.md` (2 files) | Repo governance drift |

---

## What did NOT change

- `mica.yaml` format (additive: `di_policy.namespace_mode` is optional)
- Archive JSON format
- PCT-001 through PCT-011 behavior and verdict logic
- CLOSED CONTRACT definition
- HARD_FAIL_CHECKS set
- All profiles, templates, and carry-forward spec docs
