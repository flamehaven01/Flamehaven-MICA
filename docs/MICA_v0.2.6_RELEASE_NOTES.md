# MICA v0.2.6 Release Notes — Binding Enforcement Edition

## Summary

v0.2.6 closes the PCT-010 enforcement gap that v0.2.5 deferred.

v0.2.5 noted in its approval: "PCT-010 escalation is still deferred. Forcing binding on all
existing archives would break backward compatibility." v0.2.6 resolves this with an opt-in
flag (`di_policy.critical_binding_required: true`) rather than a global behavior change.

Packages that do not set the flag behave identically to v0.2.5.
Packages that opt in get a hard gate: unbound critical DIs break CLOSED CONTRACT.

---

## The Gap v0.2.6 Closes

### PCT-010: WARN is not enforcement

In v0.2.4 and v0.2.5, PCT-010 warns when critical DIs lack `binding.origin_episode`.
A WARN does not break CLOSED CONTRACT. A maintainer can run `mica_pct.py`, see the WARN,
and choose not to act. The invariant remains unbound.

For mature packages where binding is mandatory policy, WARN is not sufficient.
The critical DI system's value depends on every critical invariant being grounded
in a real incident. An ungrounded DI is a label, not a guard.

### The opt-in design

`di_policy.critical_binding_required: true` in mica.yaml signals that this package
treats binding as mandatory. When set:

- PCT-010 emits FAIL (not WARN) for any unbound critical DI
- PCT-009 reports INCOMPLETE
- `pct_status()` returns INCOMPLETE
- The package does not achieve CLOSED CONTRACT until all critical DIs have `origin_episode`

When absent or false: PCT-010 behavior is identical to v0.2.5. No packages break.

---

## CI Foundation

v0.2.6 adds the tooling layer that v0.2.5 described but did not ship:

- `tests/test_pct_fixtures.py`: 5 pytest tests, one per fixture
- `.github/workflows/ci.yml`: matrix over Python 3.9, 3.11, 3.12
- `pyproject.toml`: ruff + pytest config
- `requirements-dev.txt`: pinned versions

The fixtures introduced in v0.2.5 now have automated coverage. PCT behavior
changes in future versions will be caught immediately by CI.

---

## Upgrade Path

v0.2.6 is non-breaking. See `MICA_v0.2.6_MIGRATION_GUIDE.md`.

For packages that want enforcement:
1. Add `di_policy.critical_binding_required: true` to mica.yaml
2. Run `python tools/mica_pct.py .`
3. Add `binding.origin_episode` to any unbound critical DIs until CLOSED CONTRACT

For packages that do not set the flag: no action required.

---

## Remaining Limits

### 1. PCT-011 is still WARN-only

`lesson_ref` existence checks remain advisory. A dead lesson_ref is worse than
no lesson_ref, but fixing it requires the lesson file to exist on disk. This is
a data problem, not a schema problem, and escalating to FAIL adds friction that
is hard to justify before the file system is in order.

### 2. di_policy is package-scoped, not global

There is no workspace-level policy that forces `critical_binding_required` across
all packages in a monorepo. Each mica.yaml opts in independently. This is by design:
coarse enforcement would block packages that are early in their lifecycle.

### 3. Enforcement is still the host agent's job

mica_runtime.py surfaces guard candidates. CLOSED CONTRACT means the package is
structurally complete. Neither tool stops a host agent from ignoring a guard.
