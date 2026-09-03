# MICA v0.2.9 Release Notes

Stable release tag: `v0.2.9`
Supersedes `v0.2.8` as the canonical spec and tool banner version.

---

## What v0.2.9 is

Everything that had been carried as "v0.2.9 draft groundwork" since June, plus
the invocation work that landed under the `v3.0.0-*` milestone tags, promoted to
a stable release.

The `v3.0.0-declaration`, `v3.0.0-invocation-truth`, and `v3.0.0-origin` tags
remain what they were: non-release milestones marking direction and
implementation checkpoints. They are not superseded by this release; they are
the history of how it was built.

---

## The contract now reports three axes

Before v0.2.9 a single verdict decided everything. A package whose memory loaded
correctly could be reported `INCOMPLETE` because a DI binding was ungrounded or
a candidate's provenance was broken.

| Axis | Question | Checks |
|---|---|---|
| `Contract` | Did the declared memory resolve for this session, and did anything reach it that should not have? | PCT-001/002/003/004/007/008/017 |
| `Archive` | Is the memory content well formed? | PCT-005/006/010/011/012 |
| `Flow` | Is the memory-authoring pipeline coherent? | PCT-013/014/015/018 |

Only `Contract` decides `CLOSED CONTRACT`. Archive and flow failures report on
their own axis and no longer override it.

`mica_pct.py --strict` widens the exit code to every axis for consumers that
want a single gate.

**Consumers relying on exit 1 for archive or flow failures must add `--strict`.**

---

## Memory profiles: per-session surface selection

Surface selection used to be two hardcoded lists keyed on `mode`, so every
session received the same memory regardless of task.

```yaml
invocation_protocol:
  primary_pattern: readme_protocol
  profiles:
    default:
      surfaces: [archive, playbook]
    review:
      surfaces: [archive, playbook, lessons]
    incident:
      surfaces: [archive, playbook]
      sections:
        playbook: [Incident Runbook]
```

```bash
python tools/mica_runtime.py . --profile incident
python tools/mica_pct.py . --profile incident
```

Precedence: requested profile, then `loading_hint: session_start` on layers,
then the mode defaults. A package that declares no profiles resolves exactly as
it did in v0.2.8.

Requesting an undeclared profile, naming a surface that is not a declared layer,
declaring no usable surfaces, or repeating a surface all fail the contract. The
session asked for memory the package cannot supply.

**Profile selection is a caller input.** It is a CLI argument set by the
operator or by the hook that recognized the triggering event. Keeping that
authority away from the model is an integration constraint, not something the
schema guarantees on its own.

---

## The playbook is addressable

A profile may deliver named `##` sections of a markdown surface rather than the
whole file, so an incident session receives the runbook without the review
procedure.

The capsule digest covers the **delivered slice**, not the source file. Hashing
the whole file while delivering part of it would make the evidence describe
content the session never received. Drift is scoped the same way: editing a
section the profile did not deliver is not drift for that session.

The section parser tracks fenced code blocks, so a `##` heading inside a code
sample is content rather than a section boundary.

---

## Byte-bound invocation evidence

`mica.invocation.v2` records, for each delivered surface, a canonical
repository-relative path, the SHA-256 and byte count of exactly the bytes
selected, the audience, the delivery state, and any section slice. The record
carries a `capsule_hash` over the continuity-relevant fields, including the
profile that selected them.

Delivery states are deliberately weak:

| State | Meaning |
|---|---|
| `declared` | The surface appears in the composition contract |
| `resolved` | Its path exists, is allowed, and its bytes were hashed |
| `emitted` | An adapter reported those bytes were sent to its output channel |
| `acknowledged` | An external host confirmed receipt |

None of them means read, understood, or followed. `mica.invocation.v1` records
remain valid; nothing rewrites recorded history.

`IVC-005` re-hashes the newest capsule against the bytes on disk when given a
project root. Drift is a WARN, not a FAIL — a record was true when written, so a
later edit makes it stale rather than invalid.

---

## Flow plane

`PCT-013` through `PCT-018` cover the memory-authoring pipeline: observation
hash-chain coherence, recall trace coverage, promotion provenance, injection
safety, and telemetry completeness. `PCT-016` is reserved for adapter maturity
and is intentionally not implemented.

`PCT-017` sits on the contract axis rather than the flow axis. It asks what
entered `agent_context`, which is an invocation question.

---

## Measurement

`mica_measure.py` reports context budget in bytes, surface resolution, capsule
coverage, and verdict axes.

It is an instrument, not a result. It says nothing about whether any of this
improves task outcomes; that needs sessions with a control, which a static scan
cannot supply.

---

## Tooling

`tools/` is now layered and acyclic:

```
mica_primitives          no internal imports
    ^-- mica_evidence    capsule and trace validation
    ^-- mica_flow        memory-authoring pipeline checks
            ^-- mica_core  contract resolution, PCT-001..012, verdict axes
```

`mica_core` re-exports the primitive and evidence names it used to define, so
`from mica_core import load_yaml` keeps working for packages that vendored an
earlier `tools/` copy. `HARD_FAIL_CHECKS` is retained as a contract-only alias.

New tools: `mica_evidence.py`, `mica_flow.py`, `mica_primitives.py`,
`mica_measure.py`.

---

## Migration from v0.2.8

Replace `tools/` and re-run the validator. Nothing else is required.

New PCT signals surface automatically. `mica_spec: "0.2.8"` packages will see a
one-patch lag, which is below the warning threshold. Optional adoption:

- declare `invocation_protocol.profiles` to give different session types
  different memory
- bump `mica_spec` to `"0.2.9"`

See `MICA_v0.2.9_MIGRATION_GUIDE.md`.

---

## Known limits

| Item | State |
|---|---|
| Consumer pilot with a control | not run |
| Memory profile adoption across live consumers | 0 / 6 |
| Handoff surface (Context Continuity P2) | architecture proposal only |
| `mica_spec` alignment across the fleet (0.1.9 – 0.2.10) | unresolved |
| `PCT-016` adapter maturity | reserved, not implemented |

The selection machinery exists; nothing uses it yet. Building a capability is
not adoption, and adoption would not be proof it helps.

---

## Tests

204 tests across nine suites, passing on Python 3.9, 3.11, 3.12, and 3.13.

Behavior preservation during the tooling refactor was verified against a golden
baseline of `run_pct_checks` output — the 21 fixtures carrying a `mica.yaml`
across 5 profile selections, 105 combinations, 1,840 results — compared after
every step.
