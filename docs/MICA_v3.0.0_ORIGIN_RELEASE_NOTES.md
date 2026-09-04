# MICA v3.0.0 Origin — Release Notes

Milestone tag: `v3.0.0-origin`
This is a milestone, not a release. The work described here shipped in the
`v0.2.9` stable release; at the time of this milestone the stable tag was `v0.2.8`.

---

## Why this milestone exists

MICA is **Memory Invocation & Context Archive**. Over nine versions the centre of
gravity drifted toward governance: invariants, severity levels, gates, and by
v0.2.9 a full memory-authoring pipeline. `v3.0.0-declaration` said in prose that
governance was a supporting mechanism, not the centre.

The code did not follow. A structural audit found the split:

| Concern | Implementation |
|---|---|
| Proving the memory reached the session | ~580 lines |
| Governing the authoring pipeline | ~485 lines |
| **Deciding which memory a session receives** | **two hardcoded lists** |

```python
["archive", "playbook", "slots"] if mode == "memory_first" else ["archive", "playbook"]
```

Invocation has two halves — selection and verification. MICA had built
verification to an extreme and left selection as a constant. Origin closes that
gap and returns governance to a supporting role in code, not only in prose.

---

## What changed

### P0 — The invocation contract stops being decided by governance

`HARD_FAIL_CHECKS` contained PCT-010, PCT-013, and PCT-015. A package whose
memory loaded correctly could be reported `INCOMPLETE` because a DI binding was
ungrounded or a candidate's provenance was broken.

The verdict is now three axes:

| Axis | Question | Checks |
|---|---|---|
| `Contract` | Did the declared memory reach this session, and did anything reach it that should not have? | PCT-001/002/003/004/007/008/017 |
| `Archive` | Is the memory content well formed? | PCT-005/006/010/011/012 |
| `Flow` | Is the memory-authoring pipeline coherent? | PCT-013/014/015/018 |

Only `Contract` decides `CLOSED CONTRACT`.

PCT-017 stays on the contract axis. It asks what entered `agent_context`, which
is an invocation question. An earlier pass had grouped it with the flow checks;
that was a misclassification.

Opt-in strictness is preserved rather than dropped:
`di_policy.critical_binding_required` still escalates PCT-010 to FAIL, on the
archive axis. `mica_pct.py --strict` widens the exit code to every axis.

### P1 — Memory profiles: the selection half

```yaml
invocation_protocol:
  profiles:
    default:
      surfaces: [archive, playbook]
    review:
      surfaces: [archive, playbook, lessons]
```

```bash
python tools/mica_runtime.py . --profile review
```

Precedence: requested profile, then `loading_hint: session_start` on layers, then
the mode defaults. Requesting an undeclared profile, or one naming a surface that
is not a declared layer, fails the contract — the session asked for memory the
package cannot supply.

Capsule evidence and `agent_context` follow the profile, so the digests recorded
for a session cover exactly the surfaces that session selected.

### P2 — The playbook becomes addressable

MICA is a memory **and playbook** package, but the playbook was one opaque file
path while the archive had invariants, a schema, and binding provenance.

```yaml
    incident:
      surfaces: [archive, playbook]
      sections:
        playbook: [Incident Runbook]
```

The capsule digest covers the **delivered slice**, not the file it came from.
Hashing the whole file while delivering part of it would make the evidence
describe content the session never received. Drift is scoped the same way:
editing a section the profile did not deliver is not drift.

On the fixture playbook: `review` delivers 57% of the file, `incident` 47%.

### P3 — Layered modules and decomposed checks

AI-SLOP-DETECTOR v3.8.9 measured `mica_core.py` at 1,893 logic lines, deficit
68.2, status `inflated_signal`, 4 critical and 15 high findings. The worst single
item was `run_pct_checks`: 457 logic lines, cyclomatic complexity 88.

```
mica_primitives          no internal imports
    ^-- mica_evidence    capsule and trace validation
    ^-- mica_flow        memory-authoring pipeline checks
            ^-- mica_core  contract resolution, PCT-001..012, verdict axes
```

`run_pct_checks` decomposed into `_run_pct002`..`_run_pct012` around a
`_PackageContext`, following the shape the flow checks already used.

### P4 — Measurement, and what it found

`mica_measure.py` reports context budget in bytes, surface resolution, capsule
coverage, and verdict axes. MICA had no metrics before this.

Building it surfaced a defect in PCT-006. Versions were packed as
`major*10000 + minor*100 + patch` and the difference reported as
"N version(s) behind". Within one minor that is a true patch count; across a
minor boundary it counts nothing. A package declaring `0.1.9` was told it was
**99 version(s) behind** canonical `0.2.8`, and one live consumer package
declares `0.1.9`.

`mica_measure.py` now reads PCT-006's own message rather than recomputing the
comparison. The first draft recomputed it — two implementations of one
comparison is exactly the drift MICA exists to catch, and a test now asserts the
tool does not import `_parse_version`.

---

## Measured outcome

AI-SLOP-DETECTOR v3.8.9 on `tools/`. Line counts are logic lines, not `wc -l`.

| Measure | Before Origin | After Origin |
|---|---|---|
| cross-file risk | 0.13 | 0.00 |
| import cycles | 0 | 0 |
| duplicate functions | 1 | 0 |
| total critical | 5 | 3 |
| `mica_core.py` critical | 4 | 0 |
| `mica_core.py` high | 15 | 4 |
| `mica_core.py` deficit | 68.2 | 29.0 |
| `mica_core.py` status | `inflated_signal` | `clean` |
| tests | 143 | 184 |

Total high is unchanged at 23. Splitting a large function produces more
functions, several of which still exceed the 50-line threshold on their own. The
three remaining criticals — `_run_pct018`, `_check_capsule_schema`, and
`mica_memory.main` — are all outside core.

---

## Behavior verification

A golden baseline of `run_pct_checks` output was captured before the P3 refactor
across the 21 fixtures carrying a mica.yaml x 5 profile selections: 105 combinations, 1,840 results. It
was compared after every subsequent step.

- P3 refactor: identical at every checkpoint
- P4: PCT-006 is the only check whose output changed — 25 messages reworded,
  45 new warnings. Every other result byte-identical.

---

## Fleet baseline

Six live consumer packages, measured at this milestone:

| Package | `mica_spec` | Contract | Agent context bytes | Profiles |
|---|---|---|---|---|
| alecta-stock | 0.2.6 | CLOSED | 15,893 | — |
| flamehaven-verification | 0.2.8 | CLOSED | 28,199 | — |
| flamehaven-cas | 0.2.10 | CLOSED | 3,998 | — |
| stem-ai-bio | 0.2.4 | CLOSED | 51,056 | — |
| cocomini-ultimatepos | 0.2.8 | CLOSED | 16,406 | — |
| (internal package, not public) | 0.1.9 | CLOSED | 97,560 | — |

All six close the contract. All six carry a digest for every invoked surface,
so the exact bytes are identifiable.

**None declares a memory profile.** Per package the baseline ranges from 3,998
to 97,560 bytes, summing to 213,112 across the fleet. The problem is not that a
session receives 213 KB -- it is that *within* each consumer, review, routine
maintenance, and incident work all receive the same declared context set
regardless of task. The selection half now exists; nothing uses it yet.

---

## Compatibility

Backward compatible throughout.

- A package that declares no profiles resolves exactly as before;
  `active_profile` is null
- `mica_core` re-exports the primitive and evidence names it used to define, so
  `from mica_core import load_yaml` keeps working for vendored `tools/` copies
- `HARD_FAIL_CHECKS` is retained as a contract-only alias
- `mica.invocation.v1` records remain valid; v2 adds `trigger`,
  `surface_evidence`, `capsule_hash`, and `profile`

**One behavioral change consumers must know about:** `mica_pct.py` now exits 1
on a contract failure only. A consumer CI relying on exit 1 for archive or flow
failures must add `--strict`.

---

## What this milestone does not establish

`mica_measure.py` is an instrument, not a result. It reports what is
structurally observable and says nothing about whether MICA improves task
outcomes — that needs sessions with a control, which a static scan cannot
supply.

The original P4 intent was a consumer pilot. What exists is the instrument that
would make one possible, and the baseline it produced.

---

## Remaining

| Item | Status |
|---|---|
| Consumer pilot with a control | run once, on `flamehaven-audit-reports` |
| Profile adoption in any consumer package | 1 / 6 |
| `_run_pct018`, `_check_capsule_schema`, `mica_memory.main` | still critical |
| `mica_spec` fleet alignment (0.1.9 … 0.2.10) | not sought; divergence respected |
| Handoff surface (Context Continuity P2) | implemented; no consumer declares one |
