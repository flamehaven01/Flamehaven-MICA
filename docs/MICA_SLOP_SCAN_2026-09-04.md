# MICA Static Analysis Snapshot -- 2026-09-04

A one-time measurement of `tools/` with an external slop detector, recorded so
the numbers do not have to be re-derived from memory. **This is a record, not a
gate.** Nothing in CI enforces it, no threshold is ratcheted against it, and the
result did not produce a patch.

| | |
|---|---|
| Revision measured | `a7ac0b3` (working tree clean under `tools/`) |
| Scope | `tools/*.py` -- 9 files, 4,628 source lines, 122 functions |
| Tool | AI-SLOP-DETECTOR 3.8.9 |
| Outcome | **No action.** Structural hotspots identified and deferred. |

## Reproduction

```text
python -m slop_detector.cli <MICA_ROOT>/tools --project --cross-file --json -o slop.json
python -m slop_detector.cli sweep dead-code          <MICA_ROOT> --json
python -m slop_detector.cli sweep dupes              <MICA_ROOT> --json
python -m slop_detector.cli sweep unused-deps        <MICA_ROOT> --json
python -m slop_detector.cli sweep boundary-violations <MICA_ROOT> --json
python -m slop_detector.cli sweep stale-suppressions <MICA_ROOT> --json
```

Function spans, cyclomatic counts, and the dead-function cross-check below were
recomputed independently with `ast` rather than taken from the detector, because
the detector reports its own line accounting (non-blank, non-comment) and not
source lines.

## Result

| Metric | Value | Meaning |
|---|---|---|
| Weighted deficit | **35.59** | `suspicious` band (30-50) |
| Unweighted mean deficit | 21.23 | 4 files above threshold, 5 clean |
| Structural coherence | 0.8381 | `vr_structural` |
| Mean LDR | 0.9928 | see below |
| Mean inflation / jargon | 0.0 / 0 | no buzzword or complexity inflation |
| Mean DDC / unused imports | 1.00 / **0** | every import is used |
| Findings | 45 (3 critical, 24 high, 8 medium, 10 low) | |

The score is single-axis. For the worst file the breakdown is:

```text
mica_core.py  ldr_penalty -0.0  inflation_penalty -0.0  ddc_penalty -0.0
              purity 4.88       pattern_hits 49.0       total 53.88
```

Every point comes from `pattern_hits`. The text-level slop axes contribute
nothing.

**What LDR 1.00 actually asserts.** The detector's LDR divides logic lines by
non-blank non-comment lines, subtracting lines that match placeholder patterns
(`pass`, `...`, bare `return None`) and lines inside functions whose body is only
such statements. A score of 1.00 therefore means *no stub or placeholder
function bodies*, not "no filler of any kind". The metric is live rather than
degenerate here: `mica_primitives.py` scores 0.9888 because three real `pass`
lines exist (an optional-dependency guard and two scalar-coercion fallbacks), and
that count matches the three `empty_except` findings exactly.

## Per file

| File | Deficit | Source lines | Logic lines | Churn (180d) | Patterns | Status |
|---|---|---|---|---|---|---|
| `mica_core.py` | **53.9** | 1,477 | 1,242 | **35** | 14 | inflated_signal |
| `mica_flow.py` | 44.9 | 549 | 492 | 2 | 7 | suspicious |
| `mica_evidence.py` | 39.9 | 599 | 506 | 4 | 6 | suspicious |
| `mica_runtime.py` | 30.0 | 908 | 796 | 22 | 8 | suspicious |
| `mica_handoff.py` | 8.0 | 325 | 260 | 4 | 3 | clean |
| `mica_primitives.py` | 7.4 | 364 | 266 | 12 | 4 | clean |
| `mica_measure.py` | 7.0 | 219 | 175 | 5 | 3 | clean |
| `mica_pct.py` | 0.0 | 122 | 99 | 8 | 0 | clean |
| `mica_invocation.py` | 0.0 | 65 | 49 | 5 | 0 | clean |

Priority hotspots (deficit combined with churn): `mica_core.py` **71.2**
(imported by 4 modules), `mica_runtime.py` 42.3, `mica_flow.py` 30.2,
`mica_evidence.py` 29.2.

## Critical findings (3)

All three are the same composite: deep nesting together with high branch count.

```text
mica_flow.py:285      _run_pct018             depth=5  cc=37  170 lines
mica_evidence.py:135  _check_capsule_schema   depth=6  cc=31   86 lines
mica_core.py:724      _run_pct003             depth=6  cc=22   59 lines
```

## Concentration

```text
189 lines  cc=40  mica_core.py:928      _run_pct007
181 lines  cc=49  mica_core.py:418      resolve_invocation_contract
170 lines  cc=45  mica_flow.py:285      _run_pct018
160 lines  cc=41  mica_evidence.py:340  run_invocation_trace_checks
```

Those four hold 700 of 4,628 lines (15.1%). Functions of 50 source lines or more
number 26 of 122 and hold 2,203 lines (47.6%).

The cause is structural rather than incidental: the 30 emitted checks (PCT 17,
HND 6, IVC 7) are implemented as one monolithic function per check, with parsing,
branching, and message assembly inline. Complexity therefore accumulates roughly
linearly with the number of checks. The single exception is
`resolve_invocation_contract`, which is not a check but the contract resolution
path itself, and it carries the highest branch count in the tree (cc=49).

## Dead functions

One genuine orphan:

```text
tools/mica_runtime.py:223  _default_loaded_surfaces()   5 lines, 0 references repo-wide
```

Commit `a3e0723` ("Enforce invocation contract from loading hints") moved this
computation into `resolve_invocation_contract` (`mica_core.py:583`,
`invoked_surfaces`); the old helper was left behind. Verified equivalent:
`fixtures/memory_first_minimal` emits `archive, playbook, slots`, matching the
orphan's hardcoded list, except the live path derives the roles from the manifest
instead of hardcoding them. Removing it changes no emitted byte.

Two functions are reachable only from tests and are not documented as public API:

```text
tools/mica_handoff.py:108  build_handoff    2 test modules
tools/mica_runtime.py:810  emit_context     2 test modules; a 2-line .decode()
                                            wrapper over emit_context_bytes
```

## Duplicate functions

50 near-identical pairs were reported. None is between two live files:

| Pair kind | Count |
|---|---|
| `Legacy/` to `Legacy/` | 41 |
| `Legacy/` to live `tools/` | 9 |
| live to live | **0** |

The nine cross-pairs are `find_mica_yaml` (x4), `detect_state` (x4), and
`load_json` (x1), all at similarity 1.00 against archived version snapshots.
These are intentional frozen copies, so there is no duplication debt -- but they
do dominate the sweep, and any future run should exclude `Legacy/` at the
detector invocation rather than by adding configuration to this repository.

## Clean sweeps

`unused-deps` 0 &middot; `boundary-violations` 0 &middot; `stale-suppressions` 0
&middot; suppressed issues 0.

## False positives (14)

Recorded so a later run does not re-litigate them.

**`empty_except` x3 -- all deliberate.** `mica_primitives.py:93` is the optional
dependency guard that falls through to `_minimal_yaml_parse` when `yaml` is
absent. `:186` and `:190` are the int-then-float-then-string scalar coercion
cascade.

**`lint_escape` x10 -- structural.** Ten `# noqa: E402` markers sit on the
re-export facade. `tools/` is a flat directory bootstrapped onto `sys.path`
rather than an installed package, so imports must follow the path insertion, and
the facade exists to keep `from mica_core import ...` working for consumers that
vendored an earlier copy.

**dead-code sweep flags `mica_primitives.py` as a "placeholder-only file".** The
detector's `_has_placeholder_only_body()` walks the whole AST and returns true
when any node has a body consisting solely of `pass`. The `except ImportError:
pass` guard above triggers it. The file has 266 logic lines.

## Decision

No patch. `a7ac0b3` stands as the floor.

- Text-level slop is absent and measured so: LDR 0.9928, inflation 0, DDC 1.00,
  zero unused imports, zero hallucinated dependencies, zero dead files, zero
  live-to-live duplicate functions.
- Complexity numbers are a maintenance risk signal, not evidence of a product
  defect. None of the 45 findings changes an emitted byte or blocks a path by
  which the emitted context comes out wrong.
- Decomposing the 26 long functions is explicitly out of scope. Extracting
  helpers to lower a complexity score adds code in response to a measurement,
  which is the failure mode this repository already paid for once.
- `resolve_invocation_contract` is retained as an observation target only.
- Deleting `_default_loaded_surfaces` is ordinary cleanup, not grounds for its
  own change. It should ride along with the next real edit to `mica_runtime.py`.

Work resumes on this only when a real consumer adoption reproduces a resolution
error or a change bottleneck, and then only on the path that actually failed.
