# MICA v0.2.5 Changelog

## Release: v0.2.5 — Runtime Alignment Edition

**Type:** Non-breaking patch over v0.2.4.
**Spec documents:** Unchanged. Tools and fixtures updated.

---

## Changes

### tools/mica_core.py (new)

Extracted shared PCT judgment and YAML loading into a standalone module.

**Before (v0.2.4):**
- `mica_pct.py` contained full PCT logic in `run_pct()`
- `mica_runtime.py` contained a separate `pct_status()` that ran its own shallow check
- The two tools could disagree: `pct=CLOSED` in hook output did not mean the same
  thing as `CLOSED CONTRACT` from `mica_pct.py`

**After (v0.2.5):**
- Both tools import `run_pct_checks()` and `is_closed_contract()` from `mica_core.py`
- `pct_status()` in `mica_runtime.py` calls `run_pct_checks()` directly
- Identical input produces identical verdict from both tools

---

### tools/mica_pct.py (simplified)

No logic change. Now imports from `mica_core` instead of containing PCT logic inline.
Output format is identical to v0.2.4.

---

### tools/mica_runtime.py (pct_status fixed)

`pct_status()` rewritten to delegate to `run_pct_checks()`.

**v0.2.4 pct_status() checked:**
- mica.yaml fields present
- archive and playbook paths exist

**v0.2.5 pct_status() checks:**
- PCT-001 through PCT-011 (same as mica_pct.py)

**Impact:** Packages that previously received `pct=CLOSED` in hook output but
`INCOMPLETE` from mica_pct.py now report `pct=INCOMPLETE` consistently.
This is a bug fix. The hook output `pct=` field is now reliable.

Affected cases (where divergence was possible):
- `mode: protocol_evolution` without lessons layer (PCT-004 FAIL)
- `primary_pattern: hook_trigger` without hook_script (PCT-008 FAIL)
- `hook_script` declared but file missing on disk (PCT-008 FAIL)

---

### YAML fallback parser (mica_core.py)

Replaced flat-line parser with indentation-aware recursive parser.

**v0.2.4 parser limitations:**
- Could not parse nested dicts (e.g., `invocation_protocol.hook_output`)
- Lost additional keys in list items beyond the first key
- `max_di_lines` returned as string "3" instead of integer 3

**v0.2.5 parser handles:**
- Nested dicts at arbitrary depth
- Lists of dicts with multiple properties
- Type coercion: integers, booleans, None

No behavior change when PyYAML is installed.

---

### fixtures/ (new)

Four minimal test packages with documented expected PCT output.

| Fixture | Tests |
|---------|-------|
| `valid_bound_di/` | PCT-010 PASS path |
| `unbound_critical_di/` | PCT-010 WARN path; CLOSED CONTRACT preserved |
| `dead_lesson_ref/` | PCT-011 WARN path; CLOSED CONTRACT preserved |
| `hook_output_violations_only/` | hook_output di_filter + max_di_lines |

---

### MICA_v0.2.5_RUNTIME_PROTOCOL.md (terminology)

Session Guard Rule section updated to distinguish:
- "surface guard candidates" — what mica_runtime.py does
- "enforce guards" — what the host AI agent does

**Old language (v0.2.4):**
> install as an active guard for the current session

**New language (v0.2.5):**
> treat as an active guard candidate surfaced by mica_runtime.py
> The host agent is responsible for enforcement.

---

## What did NOT change

- `mica.yaml` format
- Archive `design_invariants` format and binding structure
- PCT check IDs, severities, and CLOSED CONTRACT definition
- `mica_pct.py` output format
- `mica_runtime.py` summary format (text, hook, json)
- All spec documents (COMPOSITION_CONTRACT, EXAMPLES, SELF_TEST_EXAMPLES, etc.)
- Profiles, templates, schema files
