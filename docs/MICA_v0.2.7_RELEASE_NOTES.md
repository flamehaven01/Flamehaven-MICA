# MICA v0.2.7 Release Notes — Frame Stabilization Edition

## Summary

v0.2.7 cleans up the deployment model that has been accumulating organic variations
across four production MICA deployments. The spec frame is now explicit: deployment
modes, DI namespace conventions, PCT applicability per mode, and the core boundary
are all formally stated. No behavior changes to the tools.

---

## The Problem v0.2.7 Solves

### 1. No-mica.yaml deployments were ambiguous

Flamehaven-CAS and flamehaven-space both operate without a `mica.yaml`. Before v0.2.7,
the runtime classified both as `LEGACY_MODE` — implying they were pre-migration artifacts
waiting to be upgraded. But CAS is a deliberate minimal deployment: archive + playbook
is sufficient for its operational context.

**v0.2.7 fixes this**: `COMPACT_MODE` is formally defined as an intentional deployment
pattern. `LEGACY_MODE` is reserved for packages that genuinely pre-date the spec.
Both map to `pct=LEGACY` at runtime — the distinction is semantic and governance-facing,
not behavioral.

### 2. Domain-namespaced DI IDs had no canonical schema support

flamehaven-audit-reports organically evolved `DI-EQA-001`, `DI-BIO-003` IDs. The v0.2.4
DI binding schema only allowed `^DI-\d+$`, so technically the audit-reports archive was
off-schema. This was never caught because no automated validation ran against it.

**v0.2.7 fixes this**: `mica-v0.2.7-archive-di-binding.schema.json` accepts:
- `DI-001` (canonical sequential)
- `DI-EQA-001` (domain-namespaced, domain = uppercase alpha-start string)
- `INV-009` (grandfathered `INV-` prefix)

And rejects:
- `DI-001-002` (digit-domain segment — numeric-only domain not allowed)
- `DI-eqa-001` (lowercase domain)

### 3. Repo governance drift had colonized the docs/

An earlier design direction tried to expand MICA into a generic repo governance framework.
This produced 19+ docs and templates that violate MICA's own core boundary (memory
invocation, context archive, session activation). None of these were implemented in code.
All were deleted. The content worth keeping (core boundary definition, invocation hierarchy)
was absorbed into `MICA_v0.2.7_RUNTIME_PROTOCOL.md`.

---

## What Shipped

| Item | Type | Summary |
|---|---|---|
| `docs/MICA_v0.2.7_RUNTIME_PROTOCOL.md` | New doc | Full deployment model: modes, detection, PCT matrix, DI namespace, invocation hierarchy |
| `mica-v0.2.7-archive-di-binding.schema.json` | New schema | Extended DI ID pattern supporting domain-namespaced and legacy_inv forms |
| `mica.yaml.schema.json` (edited) | Schema update | `di_policy.namespace_mode` field added |
| `fixtures/compact_mode/` | New fixture | No-mica.yaml intentional deployment; PCT-001 FAIL expected |
| `fixtures/domain_namespaced_di/` | New fixture | DI-EQA-xxx + DI-BIO-xxx with `critical_binding_required: true` |
| `tests/test_pct_fixtures.py` (edited) | New tests | 2 new tests covering the above fixtures |
| 19+ drift docs deleted | Cleanup | Repo governance docs absorbed or removed |

---

## Upgrade Path

v0.2.7 is non-breaking. See `MICA_v0.2.7_MIGRATION_GUIDE.md`.

Existing packages that have `mica.yaml` and pass PCT: no action required.

COMPACT_MODE packages: no action required. `pct=LEGACY` remains the correct terminal state.

Packages using domain-namespaced DI IDs: validate against the new schema. All valid
`DI-[DOMAIN]-NNN` IDs will now PASS where previously they were technically off-schema.

---

## Remaining Limits

### 1. Ghost version in CAS archive

`flamehaven-cas/memory/mica_archive.json` declares `mica_spec: 0.2.10`. No canonical schema
for this version exists. The ghost version should be corrected to `0.2.7` in the next CAS
maintenance pass.

### 2. flamehaven-space pre-spec format

`flamehaven-space` has 24+ DIs without binding, no `mica_spec` field, and custom ID label
conventions (`invariant-NNN`). This archive pre-dates the formal spec. Migration is a
flamehaven-space project decision, not a MICA core concern.

### 3. STEM-BIO-AI at v0.2.4

The only four-deployment deployment with a `mica.yaml` still declares `mica_spec: 0.2.4`
and uses the grandfathered `INV-xxx` prefix. The `legacy_inv` namespace_mode now provides
a formal schema home for this pattern. Migration is optional.
