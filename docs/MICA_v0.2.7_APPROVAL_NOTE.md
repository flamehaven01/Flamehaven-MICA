# MICA v0.2.7 Approval Note

## Approval Status

Approved as the correct successor to v0.2.6.

Central judgment: v0.2.6 closed the PCT-010 enforcement gap. v0.2.7 closes the
frame gaps — the missing formal model for deployment modes and DI namespace conventions
that had emerged organically but were never articulated in the spec.

---

## Why v0.2.7 is the right design

### 1. COMPACT_MODE resolves a semantic ambiguity without adding complexity

Before v0.2.7, a Flamehaven-CAS-style deployment (no mica.yaml, archive only) was
classified as LEGACY_MODE. This was wrong: CAS is not a migration artifact. It is
a deliberate minimal deployment. Calling it LEGACY implied it should be upgraded — which
is not a correct recommendation.

COMPACT_MODE costs zero lines of code (the runtime behavior is identical to LEGACY_MODE).
The distinction is documentation-level: it tells consumers what kind of `pct=LEGACY`
they are reading.

This is consistent with MICA's philosophy: describe what is, not what should be.

### 2. DI domain namespacing closes a real schema gap

flamehaven-audit-reports had evolved `DI-EQA-001`, `DI-BIO-003` IDs. The v0.2.4 schema
pattern `^DI-\d+$` rejects these. The repo contained a live deployment that was technically
off-schema. v0.2.7 fixes this by broadening the pattern to `^(DI|INV)(-[A-Z][A-Z0-9]*)?-\d+$`.

The domain constraint (must start with uppercase letter, no all-digit domain) is intentional:
it prevents `DI-001-002` from passing as a domain-namespaced ID. The ambiguity between
"sequential ID with extra segment" and "domain-namespaced ID" is resolved structurally.

### 3. Drift removal is mandatory, not optional

The docs/ directory contained 19+ files that explicitly violate the core boundary defined
in CORE_BOUNDARY.md (now absorbed into RUNTIME_PROTOCOL.md). These files described repo
governance workflows, cross-repo compliance loops, and governance scorecards — none of
which are part of MICA core. Keeping them would perpetuate the confusion about what MICA is.

Deleting them is the correct act. No useful content was lost: the two docs worth keeping
(core boundary definition, invocation hierarchy) were absorbed into RUNTIME_PROTOCOL.md
before the deletes ran.

### 4. No PCT changes is the right call

v0.2.7 had an opportunity to escalate PCT-011 (lesson_ref existence) to FAIL. This was
explicitly rejected: the data problem (lesson files must exist before the check can pass)
has not been solved, and adding friction without a workflow to resolve it would make
COMPACT and LEGACY packages fail on something they cannot easily fix.

---

## Remaining Limits

### 1. Flamehaven-CAS ghost version

The CAS archive declares `mica_spec: 0.2.10`. No v0.2.10 spec exists. The archive should
be corrected in a CAS-side maintenance pass. MICA cannot own this — the archive belongs
to the CAS project.

### 2. Enforcement remains host-agent responsibility

CLOSED CONTRACT is a structural declaration, not a runtime guard. The host agent must
still choose to observe DI guards during session execution. This is unchanged from v0.2.5
and is by design — MICA is a session-start contract, not an execution-time enforcer.

### 3. PCT-011 escalation remains deferred

Lesson ref enforcement requires the file system to be in order before the check can pass.
Until a lesson file management workflow exists, WARN is the correct level.

---

## Short Verdict

> v0.2.7 is approved because it formalizes the deployment model and DI namespace
> conventions that four production deployments had already evolved toward, removes
> the governance drift that accumulated in docs/, and does so without changing any
> PCT verdicts or breaking any existing packages.
