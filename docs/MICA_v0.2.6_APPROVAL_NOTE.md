# MICA v0.2.6 Approval Note

## Approval Status

Approved as the correct successor to v0.2.5.

Central judgment: v0.2.5 left one explicit gap — PCT-010 escalation was deferred
because a global behavior change would break backward compatibility. v0.2.6 closes
that gap with an opt-in flag. No packages break. Packages that want enforcement get it.

---

## Why v0.2.6 is the right design

### 1. Opt-in is the correct enforcement model

A global flag that forces binding on all packages would invalidate packages that are
early in their lifecycle and have not yet observed real violations. That is the wrong
tradeoff. The opt-in model (`di_policy.critical_binding_required: true`) lets package
authors declare maturity when their invariants are grounded in real incidents.

This is consistent with MICA's broader philosophy: the spec records what happened, not
what should hypothetically happen. Binding enforcement makes that requirement structural.

### 2. PCT-010 in HARD_FAIL_CHECKS is correct

PCT-010 now appears in `HARD_FAIL_CHECKS`. This may look surprising given that PCT-010
was WARN-only in v0.2.4 and v0.2.5. The key is that PCT-010 only emits FAIL when
`critical_binding_required=True`. When absent or false, PCT-010 emits WARN or PASS —
and WARNs in HARD_FAIL_CHECKS have no effect on `is_closed_contract()`.

The alternative (adding PCT-010 to HARD_FAIL_CHECKS only when the flag is set) would
require `is_closed_contract()` to know about the flag. The current design is simpler:
the flag controls the emitted status, not the check set.

### 3. CI foundation completes the package

v0.2.5 shipped fixtures but no automated runner. v0.2.6 closes that gap with:
- `tests/test_pct_fixtures.py`: 5 pytest tests covering all fixture scenarios
- `.github/workflows/ci.yml`: matrix over Python 3.9, 3.11, 3.12

Future PCT changes (e.g., PCT-011 escalation in v0.2.7) will have regression coverage
from the first commit.

### 4. No spec format changes

mica.yaml, archive JSON, DI binding schema, and all profiles are unchanged.
The `di_policy` block is additive — absent means `critical_binding_required: false`.

---

## Remaining Limits

### 1. PCT-011 escalation is deferred

Lesson ref enforcement is a data problem (the file must exist before the check runs).
There is no clear opt-in analog for PCT-011 without creating a lesson file management
workflow that is out of scope for this version.

### 2. No workspace-level policy

Each mica.yaml opts in independently. There is no mechanism to require enforcement
across all packages in a workspace. This is a future concern — v0.2.x scope is the
single-package contract.

### 3. Enforcement remains the host agent's responsibility

CLOSED CONTRACT means the package is structurally complete and binding is documented.
It does not guarantee that the host agent will observe guards at runtime. That
architecture remains unchanged from v0.2.5.

---

## Short Verdict

> v0.2.6 is approved because it closes the PCT-010 enforcement gap that v0.2.5
> explicitly deferred: packages that opt in get a hard gate on critical DI binding,
> packages that do not are unaffected, and CI now verifies all fixture scenarios
> automatically.
