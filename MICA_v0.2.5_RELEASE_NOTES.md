# MICA v0.2.5 Release Notes — Runtime Alignment Edition

## The gap this closes

v0.2.4 closed the schema-PCT coordinate gap: DI binding in the archive now has
formal schema governance. But it left a runtime gap that was less visible.

`mica_runtime.py`'s `pct_status()` function ran a different check than `mica_pct.py`.
The runtime checked: does mica.yaml have the required fields, and do archive and
playbook paths exist? The validator checked: PCT-001 through PCT-011.

These are not the same checks. A package with `mode: protocol_evolution` but no
lessons layer would produce:

```
mica_pct.py  → PCT-004 FAIL → INCOMPLETE
mica_runtime.py summary → pct=CLOSED
```

The hook output said CLOSED. The validator said INCOMPLETE. The runtime was wrong.

This is the kind of gap that erodes trust in a standard. If `pct=CLOSED` in hook
context doesn't mean the same thing as `CLOSED CONTRACT` from the validator, then
operators cannot rely on the hook output to signal package health.

## How v0.2.5 fixes it

`mica_core.py` extracts `run_pct_checks()` — the single authoritative PCT judgment
function. Both `mica_pct.py` and `mica_runtime.py` import from it.

`pct_status()` in `mica_runtime.py` now calls `run_pct_checks()`:

```python
def pct_status(project_root: Path) -> str:
    mica_yaml = find_mica_yaml(project_root)
    if not mica_yaml:
        return "LEGACY" if find_legacy_archive(project_root) else "INACTIVE"
    results = run_pct_checks(project_root)
    return "CLOSED" if is_closed_contract(results) else "INCOMPLETE"
```

7 lines instead of 20, and they agree with the validator by construction.

## YAML parser correction

The v0.2.4 flat-line fallback parser missed nested structures. The two most
important structures it could not parse:

1. `invocation_protocol.hook_output` — meaning `max_di_lines` and `di_filter`
   were silently ignored when PyYAML was not installed
2. `layers[]` items — only the first key (e.g., `name`) was captured;
   `path`, `format`, and `loading_hint` were lost

The v0.2.5 parser tracks indentation and builds nested structures correctly.
For MICA's mica.yaml, the fallback now produces the same result as PyYAML.

## Terminology alignment

The v0.2.4 Runtime Protocol used "install as an active guard" language. This
implied that mica_runtime.py could intercept actions. It cannot.

mica_runtime.py is a summary emitter. It surfaces which invariants a host agent
should enforce. The enforcement decision belongs to the agent.

The corrected framing:

```text
mica_runtime.py surfaces guard candidates.
The host agent is responsible for enforcement.
```

This is not a behavioral change. It is a correct description of what the tools do.

## Fixture coverage

v0.2.5 ships four test fixtures that can be used to verify tool behavior in CI
or during SDK development. Each fixture documents its expected PCT output.

The fixtures also serve as regression tests for the YAML parser — they include
all nested structures MICA uses (`layers[]`, `hook_output`).

## Design position

v0.2.5 does not add new spec features. It aligns the runtime behavior with the
spec that was already declared. Every change is a correction, not an addition.

The roadmap from the review stands:
- v0.2.6: `binding_required: true` opt-in — PCT-010 escalation to FAIL
- v0.3.0: global PCT-010 FAIL reviewed
