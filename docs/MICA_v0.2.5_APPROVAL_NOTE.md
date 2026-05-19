# MICA v0.2.5 Approval Note

## Approval Status

Approved as the correct successor to v0.2.4.

This approval is based on one central judgment:

- v0.2.4 closed the schema-PCT coordinate gap but left a runtime coherence gap
- v0.2.5 closes that runtime gap without touching the spec format
- All changes are corrections, not additions

---

## Why v0.2.5 is better

### 1. pct= field is now reliable

The most important fix in v0.2.5 is in `mica_runtime.py`'s `pct_status()`.

In v0.2.4, `pct=CLOSED` in hook output meant: "mica.yaml has the required fields
and archive/playbook paths exist." In v0.2.5, it means the same thing as
`CLOSED CONTRACT` from `mica_pct.py` — full PCT-001 through PCT-011.

A standard where two tools disagree on a key status field is not a reliable standard.
v0.2.5 eliminates that disagreement by construction: both tools call `run_pct_checks()`
from `mica_core.py`.

### 2. YAML fallback now handles MICA's actual structures

The v0.2.4 flat-line parser could not parse:
- `invocation_protocol.hook_output` — meaning `max_di_lines` and `di_filter`
  were silently ignored in environments without PyYAML
- Full `layers[]` items — only the first key per item was captured

v0.2.5 replaces the flat-line parser with an indentation-aware recursive parser.
For MICA's mica.yaml structures, the fallback now produces identical output to PyYAML.

### 3. Terminology is accurate

The v0.2.4 Runtime Protocol described critical DIs as being "installed as active guards"
in the session. This language implied mica_runtime.py could enforce behavior. It cannot.

v0.2.5 replaces "install" with "surface as guard candidates" and explicitly notes:
"mica_runtime.py is a summary emitter, not a command interceptor."
Enforcement is the host agent's responsibility.

This is not a behavioral change. It is a correct description of what exists.

### 4. Shared core enables future alignment

`mica_core.py` is not just a refactor. It is the foundation for future PCT extensions.
When PCT-010 escalates to FAIL in v0.2.6 (when `binding_required: true` is set),
that change happens in one place and affects both tools automatically.

### 5. Fixtures close the test gap

v0.2.5 ships four test fixtures with documented expected output. These serve as
regression tests for the YAML parser and PCT behavior. They can be run in CI.

---

## Remaining Limits

### 1. PCT-010 escalation is still deferred

`binding_required: true` is planned for v0.2.6. Until then, unbound critical DIs
produce WARN — CLOSED CONTRACT is preserved. This is intentional: forcing binding
on all existing archives would break backward compatibility.

### 2. mica_core.py adds a dependency between tools

`mica_pct.py` and `mica_runtime.py` now require `mica_core.py` to be in the same
directory. Operators who deploy tools individually must ensure all three files
are co-located. Both tools handle the missing import gracefully with a clear error.

### 3. Enforcement is still the host agent's job

mica_runtime.py surfaces guard candidates. The host AI agent is responsible for
stopping, citing evidence, and requesting acknowledgment when a guard fires.
This is the correct architecture, but it means the effectiveness of the guard
system depends on how the host agent behaves.

---

## Final Judgment

MICA v0.2.5 should be treated as:

- the version that makes pct= trustworthy in both hook output and text summary
- the version that makes the YAML fallback parser production-usable
- the first version with a shared runtime core that both validation and summary tools use
- the version where the fixture set begins

## Short Verdict

> v0.2.5 is approved because it closes the runtime coherence gap that v0.2.4 left:
> both tools now agree on package state, the YAML parser handles all MICA structures,
> and the guard terminology accurately describes what the tools do vs. what the host
> agent must do.
