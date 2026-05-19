# MICA v0.2.4 → v0.2.5 Comparison

## Summary

v0.2.4 and v0.2.5 share the same spec format. The difference is entirely in tooling.

- v0.2.4 closed the schema-PCT coordinate gap for DI binding
- v0.2.5 closes the runtime coherence gap between `mica_pct.py` and `mica_runtime.py`

No mica.yaml or archive format changes. The migration is tool-only.

---

## Comparison Table

| Area | v0.2.4 | v0.2.5 | Judgment |
|------|--------|--------|----------|
| pct= accuracy | Shallow: checked fields + path existence | Full PCT-001–011 via mica_core | v0.2.5 better |
| Tool agreement | pct_status() could diverge from mica_pct.py | Both call run_pct_checks() | v0.2.5 better |
| YAML fallback parser | Flat-line: lost nested structures | Indentation-aware recursive | v0.2.5 better |
| Shared runtime core | None — tools contained duplicate logic | mica_core.py | v0.2.5 better |
| Guard terminology | "install as active guard" | "surface as guard candidate" | v0.2.5 more accurate |
| Test fixtures | None | 4 fixture packages | v0.2.5 better |
| Spec format | Defined | Unchanged | Same |
| mica.yaml schema | Defined | Unchanged | Same |
| Archive DI binding schema | Defined | Unchanged | Same |
| CLOSED CONTRACT definition | PCT-001–009 (hard-fail set) | Same | Same |

---

## Detailed Delta

### 1. pct= Field Divergence

#### v0.2.4

`mica_runtime.py` contained a separate `pct_status()` function (20 lines) that
ran its own simplified checks:

```python
# v0.2.4 pct_status() — checked:
required = {"mica_spec", "mode", "layers"}
if not required <= set(yd.keys()):
    return "INCOMPLETE"
if archive_path is None or playbook_path is None:
    return "INCOMPLETE"
if not archive_path.exists() or not playbook_path.exists():
    return "INCOMPLETE"
return "CLOSED"
```

This could return `CLOSED` for a package that fails PCT-004 (missing lessons layer
for protocol_evolution) or PCT-008 (hook_script declared but missing).

`mica_pct.py` would correctly report INCOMPLETE for the same package.

#### v0.2.5

`pct_status()` is now 7 lines that delegate to the core:

```python
def pct_status(project_root: Path) -> str:
    mica_yaml = find_mica_yaml(project_root)
    if not mica_yaml:
        return "LEGACY" if find_legacy_archive(project_root) else "INACTIVE"
    results = run_pct_checks(project_root)
    return "CLOSED" if is_closed_contract(results) else "INCOMPLETE"
```

The two tools are guaranteed to agree because they use the same function.

---

### 2. YAML Fallback Parser

#### v0.2.4

The flat-line parser processed one line at a time without tracking indentation.
It handled top-level key-value and shallow lists, but could not:
- Build nested dicts (`invocation_protocol` → `hook_output` → `max_di_lines`)
- Capture more than one key per list item

Example: for a layer with `name`, `path`, `format`, and `loading_hint`, only
`name` was captured. `path` was silently dropped. PCT-003 would then pass
(it read the archive path as None), but load_json would fail to find the file.

#### v0.2.5

The `_parse_block` / `_parse_list` / `_coerce` functions track indentation and
build nested structures correctly. Type coercion converts "3" to integer 3,
"true" to True, "null" to None. The parser handles all structures MICA uses.

---

### 3. mica_core.py

#### v0.2.4

PCT logic was duplicated:
- `mica_pct.py`: full implementation in `run_pct()`
- `mica_runtime.py`: separate shallow implementation in `pct_status()`

Future PCT extensions (e.g., v0.2.6 `binding_required`) would require changes
in two places.

#### v0.2.5

Single implementation in `mica_core.run_pct_checks()`. Both tools import from it.
Future PCT changes happen in one place.

---

### 4. Guard Language

#### v0.2.4

```
For each critical invariant:
- install as an active guard for the current session
- if a proposed action would violate it, stop immediately
```

"Install" implies mica_runtime.py installs a guard. It does not.

#### v0.2.5

```
For each critical DI candidate surfaced by mica_runtime.py:
- treat it as an active guard for the session
...
mica_runtime.py is a summary emitter, not a command interceptor.
```

Accurate description of the actual architecture.

---

## What v0.2.4 got right that v0.2.5 preserves

- The complete spec (mica.yaml format, DI binding schema, PCT check definitions)
- hook_output policy and di_filter behavior
- PCT-010/011 as WARN-only maturity checks
- The CLOSED CONTRACT definition
- All spec documents, profiles, and templates

v0.2.5 does not replace any spec content. It replaces the tools that implement it.

---

## Final Comparison Judgment

v0.2.4 was the correct spec.

v0.2.5 is the correct implementation of that spec.

If the goal is a standard where the tools reliably reflect the spec's stated
package state, v0.2.5 is the required successor.
