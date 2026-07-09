# MICA Changelog

All notable changes per version. Most recent first.
Full release notes and migration guides in `docs/`.

---

## v3.0.0-declaration - Invocation-first Floor (2026-07-09)

Milestone tag for freezing the repository at the invocation-first floor.
This is not a stable release; tool banners remain `v0.2.8` until a later versioned release.

Latest stable release tag remains `v0.2.8`.
The current working direction is a frozen invocation-first floor, with subsequent effort expected to move toward cross-repo consumption rather than deeper MICA-internal expansion.
- v3.0.0 direction declared: MICA is being reset around invocation-first context loading, truthful loaded-state declaration, and auditable invocation traces
- v3.0.0 declaration note added: `docs/MICA_v3.0.0_DECLARATION.md`
- README and About wording now place governance and memory-first machinery beneath the primary invocation contract
- obsolete `docs/CAS_AUDIT_PLAYBOOK.md` removed during doc sanity cleanup

- Tool version banner alignment: `mica_pct.py` and `mica_runtime.py` now report `v0.2.8` consistently
- Legacy archive selection is now deterministic: highest version first, then `operation_meta.last_updated`
- Regression tests expanded: 10 -> 13
- README doc sanity updated: PCT range now includes PCT-012; superseded v0.2.4 root schema link removed
- v0.2.9 design blueprint added: `docs/MICA_v0.2.9_EVOLUTION_BLUEPRINT.md`
- v0.2.9 phased execution plan added: `docs/MICA_v0.2.9_EXECUTION_PLAN.md`
- v0.2.9 schema drafts added: `mica.observe.schema.json`, `mica.candidates.schema.json`, `mica.recall.schema.json`, and flow fixtures
- v0.2.9 flow validator now enforces `PCT-013`, `PCT-015`, and `PCT-017` with runtime `Core` / `Flow` separation
- v0.2.9 PCT spec notes added: `docs/PCT-013_v0.2.9_SPEC.md`, `docs/PCT-014_v0.2.9_SPEC.md`, `docs/PCT-015_v0.2.9_SPEC.md`, `docs/PCT-017_v0.2.9_SPEC.md`, `docs/PCT-018_v0.2.9_SPEC.md`
- v0.2.9 runtime status contract added: `docs/MICA_v0.2.9_RUNTIME_STATUS_CONTRACT.md`
- cross-repo packaging guidance added: `docs/MICA_CROSS_REPO_ADOPTION_GUIDE.md`
- memory-first architecture draft and starter template added: `docs/MICA_v0.2.9_MEMORY_FIRST_ARCHITECTURE.md`, `templates/mica-v0.2.9-memory-first.yaml`
- `mica.yaml.schema.json`, `mica_core.py`, and `mica_runtime.py` now accept `mode: memory_first` plus kind-based export layers
- memory-first record schema drafts added: `mica.sessions.schema.json`, `mica.memories.schema.json`, `mica.slots.schema.json`, `mica.graph.schema.json`
- standalone invocation provenance schema added: `mica.invocation.schema.json` for independently validating `mica.invocation.jsonl` artifacts
- standalone invocation trace validator added: `tools/mica_invocation.py`
- `mica_invocation.py` now reports standalone schema presence and `mica_pct.py` prints `IVC-*` summary when an invocation trace artifact exists
- `tools/mica_memory.py` added: minimal writer/parser utility for memory-first sessions, memories, graph edges, and slots
- `tools/mica_memory.py synthesize-memories` added: deterministic observe -> candidate_memory promotion
- `tools/mica_memory.py refresh-projections` added: deterministic memories -> slots / graph projection rebuild
- `tools/mica_memory.py review-memory` added: deterministic candidate_memory -> approved_lesson / bound_invariant_evidence promotion
- `tools/mica_memory.py export` now materializes archive/playbook surfaces from approved/promoted memories and synthesizes design_invariants from bound evidence
- `tools/mica_memory.py materialize` added: single-command rebuild for observations -> memories -> archive/playbook -> slots/graph
- Repository metadata and docs now reflect the intended v3.0.0 invocation-first reset while `v0.2.9` remains draft groundwork

---

## v0.2.8 - Binding Depth Edition (2026-06-24)

**4 new PCT signals. No existing package breaks. All new signals are WARN or INFO.**

- **PCT-010 doctrinal WARN**: Detects `origin_episode` with no episode code (`EXP-xxx`), version ref, or date - signals ungrounded binding
- **PCT-010 coherence WARN**: `violation_count > 0` with empty `last_triggered` -> data defect
- **PCT-012 new (opt-in)**: `di_policy.max_archive_age_days` in mica.yaml -> WARN when archive is stale
- **PCT-006 version lag**: WARN when `mica_spec` is >= 2 versions behind canonical `0.2.8`
- `_EPISODE_PATTERNS`, `MICA_CANONICAL_VERSION`, `_parse_version()` added to mica_core.py
- `di_policy.max_archive_age_days` added to mica.yaml.schema.json
- 3 new fixtures: `doctrinal_binding`, `stale_archive`, `violation_count_incoherent`
- Tests: 7 -> 10 (all GREEN)

-> [MICA_v0.2.8_CHANGELOG.md](docs/MICA_v0.2.8_CHANGELOG.md) | [MICA_v0.2.8_APPROVAL_NOTE.md](docs/MICA_v0.2.8_APPROVAL_NOTE.md)

---

## v0.2.7 - Frame Stabilization Edition (2026-06-24)

**A small but important compatibility release that stabilizes hook output, LEGACY handling, and policy naming.**

- `COMPACT_MODE` formalized as a first-class deployment interpretation
- `di_policy.namespace_mode` added to `mica.yaml.schema.json`
- `mica_runtime.py` LEGACY and INACTIVE handling clarified; no behavior break
- Hook-output summary format preserved while adding policy forward-compatibility
- Legacy packages remain valid

---

## v0.2.6 - Critical Binding Escalation (2026-06-24)

**First opt-in hard fail for unbound critical invariants.**

- `di_policy.critical_binding_required: true` now escalates unbound critical DIs from WARN to FAIL
- `mica_core.run_pct_checks()` owns that escalation logic so validator and runtime agree
- New fixture: `binding_required_fail`
- Existing packages unchanged unless they opt in

---

## v0.2.5 - Runtime/PCT Unification (2026-06-24)

**Single source of truth for package judgment.**

- `mica_pct.py` and `mica_runtime.py` now both delegate PCT judgment to `mica_core.run_pct_checks()`
- `tools/mica_runtime.py` reports `CLOSED`, `INCOMPLETE`, `LEGACY`, or `INACTIVE` consistently
- Hook-specific coherence warning added when `loading_hint=hook` is used without `hook_trigger`
- Added fixture: `hook_output_violations_only`

---

## v0.2.4 - Archive Binding Contract (2026-06-24)

**Introduced DI binding truth checks without breaking older archives.**

- `PCT-010` added: critical DI binding presence / truth-depth checks
- `PCT-011` added: `binding.lesson_ref` dead-link detection
- Legacy archive structure remains valid when bindings are absent

---

## v0.2.3 - Hook Invocation Surface (2026-06-24)

- `invocation_protocol.hook_output` added
- Hook-trigger invocation pattern stabilized

---

## v0.2.2 - Invocation Protocol (2026-06-24)

- `invocation_protocol.primary_pattern` introduced
- Runtime summary now reports invocation pattern

---

## v0.2.1 - Portable Packaging Pass (2026-06-24)

- Added portable path layering rules in `mica.yaml`
- Strengthened package completeness checks

---

## v0.2.0 - Control Plane Baseline (2026-06-24)

- Initial `mica.yaml` packaging contract
- Archive / playbook dual-layer model
- First PCT family for package closure checks
